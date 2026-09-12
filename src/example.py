from .fintech_qa import QuestionRequest, answer_question


if __name__ == "__main__":
    result = answer_question(QuestionRequest("Why was this payment held?", "acct-42", 0.82), [])
    print(result)
