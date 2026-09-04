from __future__ import annotations

import argparse
from pathlib import Path

from app.rag.vector_store import (
    DEFAULT_KNOWLEDGE_BASE,
    create_embeddings,
    create_vector_store,
    index_documents,
    load_knowledge_documents,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index the knowledge base in ChromaDB.")
    parser.add_argument("--input", type=Path, default=DEFAULT_KNOWLEDGE_BASE)
    parser.add_argument("--batch-size", type=int, default=64)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    documents, ids = load_knowledge_documents(args.input)
    vector_store = create_vector_store(create_embeddings())
    indexed_count = index_documents(
        vector_store,
        documents,
        ids,
        batch_size=args.batch_size,
    )
    print(f"Indexed {indexed_count} knowledge records in ChromaDB.")


if __name__ == "__main__":
    main()
