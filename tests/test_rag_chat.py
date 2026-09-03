from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage

from app.services.rag_chat import NO_ANSWER, RAGChatService


def faq_document(faq_id: str, question: str, answer: str) -> Document:
    return Document(
        page_content=f"Question: {question}\nAnswer: {answer}",
        metadata={
            "faq_id": faq_id,
            "category": "Cards",
            "question": question,
        },
    )


def test_ask_uses_relevant_context_and_returns_sources() -> None:
    relevant = faq_document("faq-1", "How do I reset my PIN?", "Use the mobile app.")
    irrelevant = faq_document("faq-2", "How do I close my account?", "Contact support.")
    received_messages: list[BaseMessage] = []

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        assert query == "I forgot my PIN"
        assert top_k == 5
        return [(relevant, 0.91), (irrelevant, 0.20)]

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        received_messages.extend(messages)
        return AIMessage(content="You can reset it in the mobile app.")

    service = RAGChatService(search, generate, min_score=0.35)
    result = service.ask("  I forgot my PIN  ")

    assert result.answer == "You can reset it in the mobile app."
    assert len(result.sources) == 1
    assert result.sources[0].faq_id == "faq-1"
    assert "Use the mobile app." in str(received_messages[-1].content)
    assert "Contact support." not in str(received_messages[-1].content)


def test_ask_refuses_without_relevant_context() -> None:
    model_was_called = False

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return [(faq_document("faq-1", "Card question", "Card answer"), 0.10)]

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        nonlocal model_was_called
        model_was_called = True
        return AIMessage(content="Invented answer")

    result = RAGChatService(search, generate, min_score=0.35).ask("Mortgage rates?")

    assert result.answer == NO_ANSWER
    assert result.sources == []
    assert model_was_called is False


def test_ask_rejects_empty_question() -> None:
    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return []

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        return AIMessage(content="Unused")

    service = RAGChatService(search, generate)

    try:
        service.ask("   ")
    except ValueError as error:
        assert str(error) == "Question cannot be empty."
    else:
        raise AssertionError("Expected an empty question to be rejected.")
