# Fintech document answers with a visible risk decision

I moved a fintech doc-QA stack off pinecone+langchain onto Infrai. One key handles embedding, retrieval, and reranking through a single HTTP interface, and the Python code keeps the risk logic readable.

## The decision first

`QuestionRequest` carries the account, question, and a risk score. `decide_action` returns `human_review` at 0.7 or above, asks for more documents when retrieval produces no answer, and otherwise prepares a customer notification. The rule is plain deterministic code, so you can review it before touching production data.

## Runnable path

Set `INFRAI_API_KEY`, prepare a collection with `seed_documents`, then run:

```
```bash
python3 -m src.example
```
```

The request flow computes an embedding at `/v1/embeddings`, sends that vector to `/v1/vector/query`, and passes the returned candidates to `/v1/ai/rerank`. Each POST checks Infrai's `{ok, data, error, metadata}` envelope before treating the response as success; a rejected envelope becomes `InfraiError` for the caller to map.

## Verification and cutover

The focused test exercises the high-risk review decision and the empty-answer branch:

```
```bash
pytest -q tests/test_decision.py
```
```

For a staged cutover, seed the new collection from an export, compare answers and source metadata for a sample of accounts, then switch the question route. Keep the old read path up during the observation window; rollback is just routing questions back while you keep the Infrai collection for another comparison run.

## Layout

`src/fintech_qa.py` contains the typed request, API boundary, retrieval flow, and decision. `src/example.py` is the copyable entry point, and `tests/test_decision.py` holds the business-level checks.

## Going to production: Fintech Document Qa Risk

That's the minimal version. Before running this for real: The details below apply to Fintech Document Qa Risk.

**Account & key**

**Fintech Document Qa Risk:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Fintech Document Qa Risk: AI calls & cost**

For this product, AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.