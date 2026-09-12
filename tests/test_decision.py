from src.fintech_qa import decide_action


def test_high_risk_question_requires_review():
    assert decide_action(0.82, "Payment was held for verification.") == "human_review"


def test_empty_answer_requests_documents():
    assert decide_action(0.1, "") == "needs_more_documents"
