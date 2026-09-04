from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Conversational RAG Platform"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"

    app_api_key: SecretStr = SecretStr("")
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "qwen/qwen3.6-27b"

    assistant_name: str = "Knowledge Assistant"
    assistant_role: str = "a helpful knowledge-base assistant"
    assistant_domain: str = "the configured knowledge base"
    assistant_tone: str = "clear, concise, and professional"
    assistant_language: str = "the same language as the user"
    assistant_instructions: str = (
        "Prefer direct answers and practical steps when the context provides them."
    )
    assistant_fallback_message: str = (
        "I do not have enough information in the knowledge base to answer that."
    )
    assistant_profile_path: str = "./data/assistant_profile.json"
    assistant_profile_editing_enabled: bool = False

    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "knowledge_base"
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_device: str = "cpu"
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_min_score: float = Field(default=0.35, ge=0.0, le=1.0)

    conversation_db_url: str = "sqlite:///./data/conversations.db"
    conversation_history_limit: int = Field(default=10, ge=1, le=100)

    rate_limit_requests: int = Field(default=20, ge=1, le=1000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        prefix = value.strip().rstrip("/")
        if not prefix.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        return prefix


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
