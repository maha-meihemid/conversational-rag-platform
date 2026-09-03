from __future__ import annotations

import argparse

from app.services.rag_chat import create_rag_chat_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask the banking RAG assistant a question.")
    parser.add_argument("question", help="Banking question to answer.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = create_rag_chat_service().ask(args.question)

    print(f"\nAnswer:\n{result.answer}")


if __name__ == "__main__":
    main()
