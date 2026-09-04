import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "8")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v2/")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "30")

    configured = Settings(_env_file=None)  # type: ignore[call-arg]

    assert configured.app_env == "production"
    assert configured.app_debug is False
    assert configured.retrieval_top_k == 8
    assert configured.api_v1_prefix == "/api/v2"
    assert configured.rate_limit_requests == 30


@pytest.mark.parametrize("top_k", ["0", "21"])
def test_settings_reject_invalid_retrieval_top_k(
    monkeypatch: pytest.MonkeyPatch,
    top_k: str,
) -> None:
    monkeypatch.setenv("RETRIEVAL_TOP_K", top_k)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_reject_invalid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_reject_invalid_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "0")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_secret_is_masked_in_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    groq_api_key = "test-groq-secret"
    app_api_key = "test-app-secret"
    monkeypatch.setenv("GROQ_API_KEY", groq_api_key)
    monkeypatch.setenv("APP_API_KEY", app_api_key)

    configured = Settings(_env_file=None)  # type: ignore[call-arg]

    assert configured.groq_api_key.get_secret_value() == groq_api_key
    assert configured.app_api_key.get_secret_value() == app_api_key
    for secret in (groq_api_key, app_api_key):
        assert secret not in repr(configured)
        assert secret not in configured.model_dump_json()
