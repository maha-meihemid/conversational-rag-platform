from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_conversation_service
from app.main import app

client = TestClient(app)


class FakeConversationService:
    def __init__(self) -> None:
        self.ask_calls: list[tuple[str, str]] = []
        self.cleared_conversations: list[str] = []
        self.error: RuntimeError | None = None

    def ask(self, question: str, conversation_id: str) -> str:
        if self.error:
            raise self.error
        self.ask_calls.append((question, conversation_id))
        return "You can change your PIN at an ATM."

    def clear(self, conversation_id: str) -> None:
        if self.error:
            raise self.error
        self.cleared_conversations.append(conversation_id)


@pytest.fixture
def conversation_service() -> Iterator[FakeConversationService]:
    service = FakeConversationService()
    app.dependency_overrides[get_conversation_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


def test_chat_creates_conversation_id(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post("/api/v1/chat", json={"message": "How can I change my PIN?"})

    assert response.status_code == 200
    body = response.json()
    conversation_id = UUID(body["conversation_id"])
    assert body["answer"] == "You can change your PIN at an ATM."
    assert conversation_service.ask_calls == [
        ("How can I change my PIN?", str(conversation_id))
    ]


def test_chat_continues_existing_conversation(
    conversation_service: FakeConversationService,
) -> None:
    conversation_id = uuid4()
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "How long does it take?",
            "conversation_id": str(conversation_id),
        },
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == str(conversation_id)
    assert conversation_service.ask_calls == [
        ("How long does it take?", str(conversation_id))
    ]


def test_chat_rejects_blank_message(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post("/api/v1/chat", json={"message": "   "})

    assert response.status_code == 422
    assert conversation_service.ask_calls == []


def test_clear_conversation(conversation_service: FakeConversationService) -> None:
    conversation_id = uuid4()
    response = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert conversation_service.cleared_conversations == [str(conversation_id)]


def test_chat_hides_internal_service_error(
    conversation_service: FakeConversationService,
) -> None:
    conversation_service.error = RuntimeError("Private provider error")

    response = client.post("/api/v1/chat", json={"message": "A valid question"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The chat service is temporarily unavailable."
    }
