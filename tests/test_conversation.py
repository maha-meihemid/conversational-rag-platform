from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage

from app.services.conversation import ConversationService
from app.services.rag_chat import RAGChatService


def test_follow_up_question_uses_and_updates_history() -> None:
    histories: dict[str, InMemoryChatMessageHistory] = {}
    search_queries: list[str] = []
    model_responses = iter(
        [
            "You can request a replacement in the mobile app.",
            "How long does a replacement card take to arrive?",
            "A replacement card usually arrives within five business days.",
        ]
    )

    def get_history(conversation_id: str) -> BaseChatMessageHistory:
        return histories.setdefault(conversation_id, InMemoryChatMessageHistory())

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        search_queries.append(query)
        return [
            (
                Document(
                    page_content="Question: Card replacement\nAnswer: Within five business days.",
                    metadata={
                        "faq_id": "faq-1",
                        "category": "Cards",
                        "question": "How long does card replacement take?",
                    },
                ),
                0.90,
            )
        ]

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        return AIMessage(content=next(model_responses))

    rag_service = RAGChatService(search, generate)
    conversation = ConversationService(rag_service, get_history)

    first_answer = conversation.ask("How do I replace my card?", "customer-1")
    second_answer = conversation.ask("How long does it take?", "customer-1")

    assert first_answer == "You can request a replacement in the mobile app."
    assert second_answer == "A replacement card usually arrives within five business days."
    assert search_queries == [
        "How do I replace my card?",
        "How long does a replacement card take to arrive?",
    ]
    assert len(histories["customer-1"].messages) == 4


def test_conversations_are_isolated() -> None:
    histories: dict[str, InMemoryChatMessageHistory] = {}

    def get_history(conversation_id: str) -> BaseChatMessageHistory:
        return histories.setdefault(conversation_id, InMemoryChatMessageHistory())

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return []

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        return AIMessage(content="Unused")

    conversation = ConversationService(RAGChatService(search, generate), get_history)
    conversation.ask("First question", "conversation-a")
    conversation.ask("Second question", "conversation-b")

    assert len(histories["conversation-a"].messages) == 2
    assert len(histories["conversation-b"].messages) == 2


def test_clear_removes_conversation_history() -> None:
    history = InMemoryChatMessageHistory()

    def get_history(conversation_id: str) -> BaseChatMessageHistory:
        return history

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return []

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        return AIMessage(content="Unused")

    conversation = ConversationService(RAGChatService(search, generate), get_history)
    conversation.ask("A question", "conversation-a")
    conversation.clear("conversation-a")

    assert history.messages == []
