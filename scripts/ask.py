from __future__ import annotations

import argparse

from app.services.conversation import create_conversation_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask the conversational RAG assistant.")
    parser.add_argument("question", help="Question to answer from the knowledge base.")
    parser.add_argument(
        "--conversation-id",
        default="terminal",
        help="Identifier used to continue a conversation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    answer = create_conversation_service().ask(args.question, args.conversation_id)

    print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
    main()
