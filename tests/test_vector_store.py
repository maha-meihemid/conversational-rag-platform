import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

from app.rag.vector_store import load_faq_documents, search_documents


class FakeVectorStore:
    def similarity_search_with_relevance_scores(
        self,
        query: str,
        *,
        k: int,
    ) -> list[tuple[Document, float]]:
        document = Document(page_content=query, metadata={"category": "Cards"})
        return [(document, 0.9)][:k]


def test_load_faq_documents(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "faq.jsonl"
    record = {
        "id": "faq_123",
        "category": "Cards",
        "question": "How do I reset my PIN?",
        "answer": "Use the mobile app.",
        "source": "test",
        "content": "Question: How do I reset my PIN?\nAnswer: Use the mobile app.",
    }
    knowledge_base.write_text(json.dumps(record) + "\n", encoding="utf-8")

    documents, ids = load_faq_documents(knowledge_base)

    assert ids == ["faq_123"]
    assert documents[0].metadata["category"] == "Cards"
    assert documents[0].page_content == record["content"]


def test_load_faq_documents_rejects_invalid_records(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "invalid.jsonl"
    knowledge_base.write_text('{"id": "missing-fields"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_faq_documents(knowledge_base)


def test_search_documents_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        search_documents(FakeVectorStore(), "   ")  # type: ignore[arg-type]


def test_search_documents_returns_ranked_results() -> None:
    results = search_documents(FakeVectorStore(), "reset my card", top_k=1)  # type: ignore[arg-type]

    assert len(results) == 1
    assert results[0][1] == 0.9
