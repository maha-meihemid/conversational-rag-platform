from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

DEFAULT_INPUT = Path("data/raw/knowledge_base.json")
DEFAULT_OUTPUT = Path("data/processed/knowledge_base.jsonl")
DEFAULT_REPORT = Path("data/processed/quality_report.json")
SUPPORTED_FORMATS = {".json", ".jsonl"}


@dataclass(frozen=True)
class KnowledgeRecord:
    id: str
    category: str
    question: str
    answer: str
    source: str
    content: str


@dataclass(frozen=True)
class PreparationResult:
    records: list[KnowledgeRecord]
    rows_read: int
    blank_rows_removed: int
    duplicate_questions_removed: int
    categories: dict[str, int]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", normalized).strip()


def stable_record_id(question: str) -> str:
    normalized_question = normalize_text(question).casefold().encode("utf-8")
    digest = hashlib.sha256(normalized_question).hexdigest()[:16]
    return f"record_{digest}"


def optional_text(value: Any, default: str = "") -> str:
    if not isinstance(value, str):
        return default
    return normalize_text(value) or default


def prepare_records(
    rows: Iterable[dict[str, Any]],
    *,
    default_source: str,
) -> PreparationResult:
    records: list[KnowledgeRecord] = []
    seen_questions: set[str] = set()
    categories: Counter[str] = Counter()
    rows_read = 0
    blank_rows_removed = 0
    duplicate_questions_removed = 0

    for row in rows:
        rows_read += 1
        question = optional_text(row.get("question"))
        answer = optional_text(row.get("answer"))

        if not question or not answer:
            blank_rows_removed += 1
            continue

        question_key = question.casefold()
        if question_key in seen_questions:
            duplicate_questions_removed += 1
            continue

        category = optional_text(row.get("category"), "General")
        source = optional_text(row.get("source"), default_source)
        seen_questions.add(question_key)
        categories[category] += 1
        records.append(
            KnowledgeRecord(
                id=stable_record_id(question),
                category=category,
                question=question,
                answer=answer,
                source=source,
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


def read_input(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.is_file():
        raise FileNotFoundError(f"Knowledge-base file not found at {input_path}.")
    if input_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError("Knowledge-base input must be a .json or .jsonl file.")

    if input_path.suffix.lower() == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("JSON input must contain an array of objects.")
        return cast(list[dict[str, Any]], data)

    rows: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"JSONL record on line {line_number} must be an object.")
            rows.append(item)
    return rows


def prepare_file(input_path: Path) -> PreparationResult:
    return prepare_records(read_input(input_path), default_source=input_path.stem)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_jsonl(records: Iterable[KnowledgeRecord], output_path: Path) -> None:
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
        description="Validate and normalize a JSON or JSONL Q&A knowledge base."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = prepare_file(args.input)
    write_jsonl(result.records, args.output)
    write_report(result, args.input, args.output, args.report)
    print(
        f"Prepared {len(result.records)} knowledge records from {result.rows_read} rows "
        f"({result.duplicate_questions_removed} duplicates removed)."
    )


if __name__ == "__main__":
    main()
