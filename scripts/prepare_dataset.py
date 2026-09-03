from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_INPUT = Path(
    "data/raw/banking-faq-dataset/banking_knowledge_base_1000.csv"
)
DEFAULT_OUTPUT = Path("data/processed/banking_faq.jsonl")
DEFAULT_REPORT = Path("data/processed/quality_report.json")
REQUIRED_COLUMNS = {"Section", "Question", "Answer"}
SOURCE_NAME = "kaggle-banking-faq-v4"


@dataclass(frozen=True)
class FAQRecord:
    id: str
    category: str
    question: str
    answer: str
    source: str
    content: str


@dataclass(frozen=True)
class PreparationResult:
    records: list[FAQRecord]
    rows_read: int
    blank_rows_removed: int
    duplicate_questions_removed: int
    categories: dict[str, int]


def normalize_text(value: str) -> str:
    """Normalize Unicode and collapse repeated whitespace deterministically."""
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", normalized).strip()


def stable_faq_id(question: str) -> str:
    normalized_question = normalize_text(question).casefold().encode("utf-8")
    digest = hashlib.sha256(normalized_question).hexdigest()[:16]
    return f"faq_{digest}"


def prepare_rows(rows: Iterable[dict[str, str]]) -> PreparationResult:
    records: list[FAQRecord] = []
    seen_questions: set[str] = set()
    categories: Counter[str] = Counter()
    rows_read = 0
    blank_rows_removed = 0
    duplicate_questions_removed = 0

    for row in rows:
        rows_read += 1
        category = normalize_text(row.get("Section", ""))
        question = normalize_text(row.get("Question", ""))
        answer = normalize_text(row.get("Answer", ""))

        if not category or not question or not answer:
            blank_rows_removed += 1
            continue

        question_key = question.casefold()
        if question_key in seen_questions:
            duplicate_questions_removed += 1
            continue

        seen_questions.add(question_key)
        categories[category] += 1
        records.append(
            FAQRecord(
                id=stable_faq_id(question),
                category=category,
                question=question,
                answer=answer,
                source=SOURCE_NAME,
                content=f"Question: {question}\nAnswer: {answer}",
            )
        )

    return PreparationResult(
        records=records,
        rows_read=rows_read,
        blank_rows_removed=blank_rows_removed,
        duplicate_questions_removed=duplicate_questions_removed,
        categories=dict(sorted(categories.items())),
    )


def read_csv(input_path: Path) -> PreparationResult:
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {input_path}. See README.md for download instructions."
        )

    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Dataset is missing required columns: {missing}")
        return prepare_rows(reader)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_jsonl(records: Iterable[FAQRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
    temporary_path.replace(output_path)


def write_report(
    result: PreparationResult,
    input_path: Path,
    output_path: Path,
    report_path: Path,
) -> None:
    report = {
        "source": SOURCE_NAME,
        "input_file": input_path.as_posix(),
        "input_sha256": sha256_file(input_path),
        "output_file": output_path.as_posix(),
        "output_sha256": sha256_file(output_path),
        "rows_read": result.rows_read,
        "records_written": len(result.records),
        "blank_rows_removed": result.blank_rows_removed,
        "duplicate_questions_removed": result.duplicate_questions_removed,
        "category_count": len(result.categories),
        "categories": result.categories,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and normalize the Kaggle banking FAQ dataset."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = read_csv(args.input)
    write_jsonl(result.records, args.output)
    write_report(result, args.input, args.output, args.report)
    print(
        f"Prepared {len(result.records)} FAQ records from {result.rows_read} rows "
        f"({result.duplicate_questions_removed} duplicates removed)."
    )


if __name__ == "__main__":
    main()
