from __future__ import annotations

import argparse
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
DEFAULT_DESTINATION = Path("data/raw/banking-faq-dataset")


def download_dataset(destination: Path, *, force: bool = False) -> Path:
    output_path = destination / EXPECTED_CSV_NAME
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Dataset already exists at {output_path}. Use --force to replace it."
        )

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="banking-faq-") as temporary_directory:
        archive_path = Path(temporary_directory) / "dataset.zip"
        request = urllib.request.Request(
            DATASET_URL,
            headers={"User-Agent": "banking-rag-assistant/0.1"},
        )
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            archive_path.open("wb") as archive_file,
        ):
            shutil.copyfileobj(response, archive_file)

        with zipfile.ZipFile(archive_path) as archive:
            matching_files = [
                member
                for member in archive.infolist()
                if Path(member.filename).name == EXPECTED_CSV_NAME and not member.is_dir()
            ]
            if len(matching_files) != 1:
                raise ValueError(
                    f"Expected exactly one {EXPECTED_CSV_NAME} file in the archive, "
                    f"found {len(matching_files)}."
                )

            temporary_output = output_path.with_suffix(".csv.tmp")
            with (
                archive.open(matching_files[0]) as source,
                temporary_output.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
            temporary_output.replace(output_path)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the public Kaggle banking FAQ dataset."
    )
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing dataset file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = download_dataset(args.destination, force=args.force)
    print(f"Dataset downloaded to {output_path}")


if __name__ == "__main__":
    main()
