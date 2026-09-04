from collections.abc import Callable

import chromadb
from sqlalchemy import create_engine, text

from app.core.config import settings

ReadinessCheck = Callable[[], None]


def check_configuration() -> None:
    if not settings.app_api_key.get_secret_value():
        raise RuntimeError("Application API key is missing")
    if not settings.groq_api_key.get_secret_value():
        raise RuntimeError("Groq API key is missing")


def check_vector_store() -> None:
    client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    client.get_collection(settings.chroma_collection_name)


def check_conversation_store() -> None:
    engine = create_engine(settings.conversation_db_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def run_readiness_checks(
    checks: dict[str, ReadinessCheck] | None = None,
) -> dict[str, str]:
    configured_checks = checks or {
        "configuration": check_configuration,
        "vector_store": check_vector_store,
        "conversation_store": check_conversation_store,
    }
    results: dict[str, str] = {}

    for name, check in configured_checks.items():
        try:
            check()
        except Exception:
            results[name] = "unavailable"
        else:
            results[name] = "ok"

    return results
