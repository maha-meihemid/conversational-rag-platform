from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.dependencies import get_chat_rate_limiter, get_conversation_service
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


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


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_api_key", SecretStr(AUTH_HEADERS["X-API-Key"]))


def test_chat_creates_conversation_id(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "How can I change my PIN?"},
        headers=AUTH_HEADERS,
    )

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
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == str(conversation_id)
    assert conversation_service.ask_calls == [
        ("How long does it take?", str(conversation_id))
    ]


def test_chat_rejects_blank_message(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "   "},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422
    assert conversation_service.ask_calls == []


def test_clear_conversation(conversation_service: FakeConversationService) -> None:
    conversation_id = uuid4()
    response = client.delete(
        f"/api/v1/conversations/{conversation_id}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204
    assert response.content == b""
    assert conversation_service.cleared_conversations == [str(conversation_id)]


def test_chat_hides_internal_service_error(
    conversation_service: FakeConversationService,
) -> None:
    conversation_service.error = RuntimeError("Private provider error")

    response = client.post(
        "/api/v1/chat",
        json={"message": "A valid question"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The chat service is temporarily unavailable."
    }


def test_chat_rejects_missing_api_key(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post("/api/v1/chat", json={"message": "A valid question"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}
    assert conversation_service.ask_calls == []


def test_chat_rejects_invalid_api_key(
    conversation_service: FakeConversationService,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "A valid question"},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert conversation_service.ask_calls == []


def test_chat_fails_closed_without_configured_api_key(
    conversation_service: FakeConversationService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "app_api_key", SecretStr(""))

    response = client.post(
        "/api/v1/chat",
        json={"message": "A valid question"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "API authentication is not configured."}
    assert conversation_service.ask_calls == []


def test_chat_returns_429_when_rate_limit_is_reached(
    conversation_service: FakeConversationService,
) -> None:
    limiter = RateLimiter(requests=1, window_seconds=60, clock=lambda: 100.0)
    app.dependency_overrides[get_chat_rate_limiter] = lambda: limiter

    first_response = client.post(
        "/api/v1/chat",
        json={"message": "First question"},
        headers=AUTH_HEADERS,
    )
    limited_response = client.post(
        "/api/v1/chat",
        json={"message": "Second question"},
        headers=AUTH_HEADERS,
    )

    assert first_response.status_code == 200
    assert limited_response.status_code == 429
    assert limited_response.headers["Retry-After"] == "60"
    assert limited_response.json() == {
        "detail": "Too many chat requests. Please try again later."
    }
    assert len(conversation_service.ask_calls) == 1
