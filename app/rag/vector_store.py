from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

DEFAULT_KNOWLEDGE_BASE = Path("data/processed/knowledge_base.jsonl")


def create_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )


def create_vector_store(
    embeddings: Embeddings,
    *,
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> Chroma:
    return Chroma(
        collection_name=collection_name or settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory or settings.chroma_persist_directory,
        collection_metadata={"hnsw:space": "cosine"},
    )


def load_knowledge_documents(
    path: Path = DEFAULT_KNOWLEDGE_BASE,
) -> tuple[list[Document], list[str]]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Knowledge base not found at {path}. Run scripts/prepare_dataset.py first."
        )

    documents: list[Document] = []
    ids: list[str] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
                record_id = str(record["id"])
                content = str(record["content"])
                metadata = {
                    "record_id": record_id,
                    "category": str(record["category"]),
                    "question": str(record["question"]),
                    "answer": str(record["answer"]),
                    "source": str(record["source"]),
                }
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(f"Invalid knowledge-base record on line {line_number}.") from error

            ids.append(record_id)
            documents.append(Document(page_content=content, metadata=metadata))

    if not documents:
        raise ValueError(f"Knowledge base is empty: {path}")

    return documents, ids


def batched(
    items: list[Document],
    ids: list[str],
    size: int,
) -> Iterable[tuple[list[Document], list[str]]]:
    for start in range(0, len(items), size):
        end = start + size
        yield items[start:end], ids[start:end]


def index_documents(
    vector_store: Chroma,
    documents: list[Document],
    ids: list[str],
    *,
    batch_size: int = 64,
) -> int:
    if len(documents) != len(ids):
        raise ValueError("Each document must have exactly one identifier.")
    if batch_size < 1:
        raise ValueError("Batch size must be greater than zero.")

    for document_batch, id_batch in batched(documents, ids, batch_size):
        vector_store.add_documents(documents=document_batch, ids=id_batch)

    return len(documents)


def search_documents(
    vector_store: Chroma,
    query: str,
    *,
    top_k: int | None = None,
) -> list[tuple[Document, float]]:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Search query cannot be empty.")

    return vector_store.similarity_search_with_relevance_scores(
        clean_query,
        k=top_k or settings.retrieval_top_k,
    )
