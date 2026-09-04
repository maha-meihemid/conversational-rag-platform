import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "8")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v2/")

    configured = Settings(_env_file=None)  # type: ignore[call-arg]

    assert configured.app_env == "production"
    assert configured.app_debug is False
    assert configured.retrieval_top_k == 8
    assert configured.api_v1_prefix == "/api/v2"


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


def test_secret_is_masked_in_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    api_key = "test-secret-key"
    monkeypatch.setenv("GROQ_API_KEY", api_key)

    configured = Settings(_env_file=None)  # type: ignore[call-arg]

    assert configured.groq_api_key.get_secret_value() == api_key
    assert api_key not in repr(configured)
    assert api_key not in configured.model_dump_json()
