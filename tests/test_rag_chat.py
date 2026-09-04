from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage

from app.models.assistant import AssistantProfile
from app.services.rag_chat import RAGChatService


def knowledge_document(record_id: str, question: str, answer: str) -> Document:
    return Document(
        page_content=f"Question: {question}\nAnswer: {answer}",
        metadata={
            "record_id": record_id,
            "category": "Account",
            "question": question,
        },
    )


def test_ask_uses_relevant_context_and_returns_sources() -> None:
    relevant = knowledge_document(
        "record-1",
        "How do I reset my password?",
        "Use the account settings.",
    )
    irrelevant = knowledge_document(
        "record-2",
        "How do I close my account?",
        "Contact support.",
    )
    received_messages: list[BaseMessage] = []

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        assert query == "I forgot my password"
        assert top_k == 5
        return [(relevant, 0.91), (irrelevant, 0.20)]

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        received_messages.extend(messages)
        return AIMessage(content="You can reset it in the account settings.")

    service = RAGChatService(search, generate, min_score=0.35)
    result = service.ask("  I forgot my password  ")

    assert result.answer == "You can reset it in the account settings."
    assert len(result.sources) == 1
    assert result.sources[0].record_id == "record-1"
    assert "Use the account settings." in str(received_messages[-1].content)
    assert "Contact support." not in str(received_messages[-1].content)


def test_ask_refuses_without_relevant_context() -> None:
    model_was_called = False
    profile = AssistantProfile(fallback_message="No grounded answer is available.")

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return [(knowledge_document("record-1", "Product question", "Product answer"), 0.10)]

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        nonlocal model_was_called
        model_was_called = True
        return AIMessage(content="Invented answer")

    result = RAGChatService(
        search,
        generate,
        min_score=0.35,
        profile_provider=lambda: profile,
    ).ask("Unrelated question?")

    assert result.answer == "No grounded answer is available."
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
