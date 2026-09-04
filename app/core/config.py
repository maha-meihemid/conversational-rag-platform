from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Conversational RAG Platform"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"

    groq_api_key: str = ""
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
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.35

    conversation_db_url: str = "sqlite:///./data/conversations.db"
    conversation_history_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
