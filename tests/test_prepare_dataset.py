import json
from pathlib import Path

import pytest

from scripts.prepare_dataset import prepare_file, stable_record_id


def test_prepare_json_normalizes_optional_fields_and_deduplicates(tmp_path: Path) -> None:
    input_path = tmp_path / "products.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "question": "How do I reset   my password?",
                    "answer": "Use the account settings.",
                    "category": " Account ",
                    "source": " Product docs ",
                },
                {
                    "question": "how do i reset my password?",
                    "answer": "Duplicate answer.",
                },
                {"question": "", "answer": "Missing question."},
            ]
        ),
        encoding="utf-8",
    )

    result = prepare_file(input_path)

    assert result.rows_read == 3
    assert result.blank_rows_removed == 1
    assert result.duplicate_questions_removed == 1
    assert len(result.records) == 1
    assert result.records[0].category == "Account"
    assert result.records[0].source == "Product docs"
    assert result.records[0].question == "How do I reset my password?"


def test_prepare_jsonl_uses_defaults_for_optional_fields(tmp_path: Path) -> None:
    input_path = tmp_path / "support.jsonl"
    input_path.write_text(
        json.dumps({"question": "Where is my order?", "answer": "Open Orders."}) + "\n",
        encoding="utf-8",
    )

    result = prepare_file(input_path)

    assert result.records[0].category == "General"
    assert result.records[0].source == "support"


def test_stable_record_id_ignores_case_and_repeated_whitespace() -> None:
    assert stable_record_id("How do I reset my password?") == stable_record_id(
        "  HOW do I   reset my password?  "
    )


def test_prepare_rejects_invalid_json_shape(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid.json"
    input_path.write_text(json.dumps({"question": "Q", "answer": "A"}), encoding="utf-8")

    with pytest.raises(ValueError, match="array of objects"):
        prepare_file(input_path)
