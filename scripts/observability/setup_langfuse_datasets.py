"""Upload ACM-AI ground truth benchmarks to Langfuse for evaluation.

Creates two datasets:
- broadmeadows-31
- alexander-43

Each dataset gets a single item where:
- input: source PDF path and benchmark metadata
- expected_output: full list of ground-truth ACM records
"""

import argparse
import csv
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from langfuse import Langfuse
from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[2]

DATASET_DEFINITIONS = [
    {
        "name": "broadmeadows-31",
        "description": "Broadmeadows benchmark ground truth (31 records)",
        "csv_path": REPO_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.csv",
        "source_pdf_path": REPO_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf",
    },
    {
        "name": "alexander-43",
        "description": "Alexander benchmark ground truth (43 records)",
        "csv_path": REPO_ROOT / "docs" / "samplePDF" / "Alexander_GroundTruth.csv",
        "source_pdf_path": REPO_ROOT
        / "docs"
        / "samplePDF"
        / "Clucth_Alexander_District_Hospital.pdf",
    },
]


def _iter_non_comment_lines(lines: Iterable[str]) -> Iterable[str]:
    """Yield CSV lines excluding comments and blank rows."""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        yield line


def _load_csv_records(csv_path: Path) -> List[Dict[str, str]]:
    """Load records from a benchmark CSV file."""

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(_iter_non_comment_lines(handle))
        rows: List[Dict[str, str]] = []
        for row in reader:
            normalized: Dict[str, str] = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized[key.strip()] = (value or "").strip()
            if normalized:
                rows.append(normalized)
    return rows


def _create_langfuse_client() -> Langfuse:
    """Create an authenticated Langfuse client from environment settings."""

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        raise ValueError(
            "Missing LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY in environment"
        )

    client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    if not client.auth_check():
        raise RuntimeError("Langfuse auth_check failed. Verify keys and host.")

    return client


def _ensure_dataset(client: Langfuse, name: str, description: str) -> Any:
    """Get existing dataset or create it when missing."""

    try:
        return client.get_dataset(name=name, fetch_items_page_size=1)
    except Exception:
        logger.info(f"Creating dataset '{name}'")
        client.create_dataset(name=name, description=description)
        return client.get_dataset(name=name, fetch_items_page_size=1)


def _dataset_has_items(dataset: Any) -> bool:
    """Return True when dataset already contains items."""

    items = getattr(dataset, "items", None)
    return isinstance(items, list) and len(items) > 0


def main() -> None:
    """Entry point for Langfuse dataset setup."""

    parser = argparse.ArgumentParser(
        description="Upload ACM benchmark datasets to Langfuse"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=False,
        help="Skip dataset item creation when dataset already has items",
    )
    args = parser.parse_args()

    load_dotenv(override=False)
    client = _create_langfuse_client()

    created_items = 0

    for definition in DATASET_DEFINITIONS:
        name = definition["name"]
        description = definition["description"]
        csv_path: Path = definition["csv_path"]
        source_pdf_path: Path = definition["source_pdf_path"]

        records = _load_csv_records(csv_path)
        dataset = _ensure_dataset(client, name, description)

        if args.skip_existing and _dataset_has_items(dataset):
            logger.info(
                f"Dataset '{name}' already has items, skipping (--skip-existing)"
            )
            continue

        input_payload: Dict[str, Any] = {
            "source_pdf_path": str(source_pdf_path),
            "benchmark": name,
            "record_count": len(records),
        }

        expected_output: Dict[str, Any] = {
            "records": records,
            "record_count": len(records),
        }

        metadata: Dict[str, Any] = {
            "csv_path": str(csv_path),
            "source_pdf_path": str(source_pdf_path),
            "benchmark": name,
        }

        client.create_dataset_item(
            dataset_name=name,
            input=input_payload,
            expected_output=expected_output,
            metadata=metadata,
        )
        created_items += 1
        logger.info(f"Uploaded dataset item for '{name}' ({len(records)} records)")

    client.flush()
    logger.success(f"Langfuse dataset setup complete. Items created: {created_items}")


if __name__ == "__main__":
    main()
