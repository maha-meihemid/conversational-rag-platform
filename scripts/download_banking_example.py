from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DATASET_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "rudrakumargupta/banking-faq-dataset-for-chatbot-training"
)
EXPECTED_CSV_NAME = "banking_knowledge_base_1000.csv"
DEFAULT_OUTPUT = Path("data/raw/knowledge_base.json")


def download_banking_example(output_path: Path, *, force: bool = False) -> Path:
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Knowledge base already exists at {output_path}. Use --force to replace it."
        )

    with tempfile.TemporaryDirectory(prefix="rag-example-") as temporary_directory:
        archive_path = Path(temporary_directory) / "dataset.zip"
        request = urllib.request.Request(
            DATASET_URL,
            headers={"User-Agent": "conversational-rag-platform/0.1"},
        )
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            archive_path.open("wb") as archive_file,
        ):
            shutil.copyfileobj(response, archive_file)

        with zipfile.ZipFile(archive_path) as archive:
            matches = [
                member
                for member in archive.infolist()
                if Path(member.filename).name == EXPECTED_CSV_NAME and not member.is_dir()
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one {EXPECTED_CSV_NAME} file, found {len(matches)}."
                )

            with (
                archive.open(matches[0]) as source,
                io.TextIOWrapper(source, encoding="utf-8-sig", newline="") as text_source,
            ):
                rows = list(csv.DictReader(text_source))

    records = [
        {
            "question": row.get("Question", ""),
            "answer": row.get("Answer", ""),
            "category": row.get("Section", "General"),
            "source": "Kaggle Banking FAQ Dataset",
        }
        for row in rows
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_output.replace(output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the banking demo and convert it to the generic JSON schema."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = download_banking_example(args.output, force=args.force)
    print(f"Example knowledge base written to {output_path}")


if __name__ == "__main__":
    main()
