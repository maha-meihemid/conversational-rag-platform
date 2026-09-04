from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import settings
from app.main import app
from app.models.assistant import AssistantProfile
from app.services.assistant_profile import AssistantProfileStore, get_assistant_profile_store

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


@pytest.fixture
def profile_store(tmp_path: Path) -> Iterator[AssistantProfileStore]:
    store = AssistantProfileStore(
        tmp_path / "assistant_profile.json",
        AssistantProfile(),
    )
    app.dependency_overrides[get_assistant_profile_store] = lambda: store
    yield store
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_api_key", SecretStr(AUTH_HEADERS["X-API-Key"]))


def test_profile_store_persists_configuration(tmp_path: Path) -> None:
    path = tmp_path / "assistant_profile.json"
    store = AssistantProfileStore(path, AssistantProfile())
    profile = AssistantProfile(
        name="Product Guide",
        domain="product documentation",
        tone="friendly and concise",
    )

    store.save(profile)

    assert AssistantProfileStore(path, AssistantProfile()).get() == profile


def test_read_assistant_profile(profile_store: AssistantProfileStore) -> None:
    response = client.get("/api/v1/assistant-profile")

    assert response.status_code == 200
    assert response.json()["name"] == "Knowledge Assistant"


def test_update_assistant_profile_when_enabled(
    profile_store: AssistantProfileStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "assistant_profile_editing_enabled", True)

    response = client.put(
        "/api/v1/assistant-profile",
        json={
            "name": "Support Copilot",
            "role": "a customer support assistant",
            "domain": "product support",
            "tone": "warm and concise",
            "language": "the same language as the user",
            "instructions": "Provide numbered steps when useful.",
            "fallback_message": "I cannot answer that from the support knowledge base.",
        },
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert profile_store.get().name == "Support Copilot"


def test_update_assistant_profile_is_disabled_by_default(
    profile_store: AssistantProfileStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "assistant_profile_editing_enabled", False)

    response = client.put(
        "/api/v1/assistant-profile",
        json=AssistantProfile().model_dump(),
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 403
