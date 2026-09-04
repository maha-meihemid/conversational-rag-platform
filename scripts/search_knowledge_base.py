from __future__ import annotations

import argparse

from app.rag.vector_store import create_embeddings, create_vector_store, search_documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search the configured knowledge base.")
    parser.add_argument("query", help="Question to search for.")
    parser.add_argument("--top-k", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vector_store = create_vector_store(create_embeddings())
    results = search_documents(vector_store, args.query, top_k=args.top_k)

    for position, (document, score) in enumerate(results, start=1):
        print(f"\nResult {position} | score={score:.3f}")
        print(f"Category: {document.metadata['category']}")
        print(document.page_content)


if __name__ == "__main__":
    main()
