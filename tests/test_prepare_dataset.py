import csv
from pathlib import Path

import pytest

from scripts.prepare_dataset import read_csv, stable_faq_id


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_read_csv_normalizes_and_deduplicates_questions(tmp_path: Path) -> None:
    input_path = tmp_path / "banking.csv"
    write_csv(
        input_path,
        ["Section", "Question", "Answer"],
        [
            {
                "Section": " Cards ",
                "Question": "How do I reset   my PIN?",
                "Answer": "Use the mobile app.",
            },
            {
                "Section": "Cards",
                "Question": "how do i reset my pin?",
                "Answer": "This duplicate should be removed.",
            },
            {"Section": "Cards", "Question": "", "Answer": "Missing question."},
        ],
    )

    result = read_csv(input_path)

    assert result.rows_read == 3
    assert result.blank_rows_removed == 1
    assert result.duplicate_questions_removed == 1
    assert len(result.records) == 1
    assert result.records[0].category == "Cards"
    assert result.records[0].question == "How do I reset my PIN?"
    assert result.records[0].content == (
        "Question: How do I reset my PIN?\nAnswer: Use the mobile app."
    )


def test_stable_faq_id_ignores_case_and_repeated_whitespace() -> None:
    assert stable_faq_id("How do I reset my PIN?") == stable_faq_id(
        "  HOW do I   reset my pin?  "
    )


def test_read_csv_rejects_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid.csv"
    write_csv(input_path, ["Question", "Answer"], [{"Question": "Q", "Answer": "A"}])

    with pytest.raises(ValueError, match="Section"):
        read_csv(input_path)
