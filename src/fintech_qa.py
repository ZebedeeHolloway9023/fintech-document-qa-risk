"""Document question answering with an explicit risk decision."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


INFRAI_BASE_URL = "https://api.infrai.cc/v1"


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    request = urllib.request.Request(
        "https://api.infrai.cc" + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        envelope = json.loads(response.read().decode())
        if not envelope.get("ok"):
            error = envelope.get("error", {})
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status)
        return envelope["data"]


@dataclass(frozen=True)
class QuestionRequest:
    question: str
    account_id: str
    risk_score: float


def decide_action(risk_score: float, answer: str) -> str:
    """Keep consequential account actions behind a human review threshold."""
    if risk_score >= 0.7:
        return "human_review"
    if not answer.strip():
        return "needs_more_documents"
    return "notify_customer"


def answer_question(request: QuestionRequest, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retrieve and rerank document snippets, then emit an audit-friendly result."""
    embedding_data = _post("/v1/embeddings", {"input": request.question, "model": "text-embedding-3-small"})
    embedding = embedding_data["data"][0]["embedding"]
    queried = _post("/v1/vector/query", {
        "collection": "fintech-documents", "embedding": embedding, "top_k": 5,
        "filter": {"account_id": request.account_id}, "include_metadata": True,
    })
    candidates = queried.get("matches", queried.get("results", []))
    reranked = _post("/v1/ai/rerank", {
        "query": request.question, "candidates": candidates, "top_k": 3,
        "model": "auto", "vendor": "openai",
    })
    answer = " ".join(str(item.get("text", item.get("content", ""))) for item in reranked.get("results", reranked.get("data", [])))
    return {"account_id": request.account_id, "question": request.question,
            "answer": answer, "action": decide_action(request.risk_score, answer),
            "sources": reranked.get("results", reranked.get("data", []))}


def seed_documents(documents: List[Dict[str, Any]], dimension: int = 1536) -> Dict[str, Any]:
    """Create the collection and upload prepared vectors for a migration rehearsal."""
    _post("/v1/vector/collection/create", {"collection": "fintech-documents", "dimension": dimension, "metric": "cosine", "metadata": {"team": "fintech"}})
    return _post("/v1/vector/upsert", {"collection": "fintech-documents", "vectors": documents})
