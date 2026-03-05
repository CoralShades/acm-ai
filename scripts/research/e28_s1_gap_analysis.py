"""E28-S1 Gap Analysis — Identify missing Alexander 'Not Sampled' records.

Usage:
    cd $CLAUDE_PROJECT_DIR
    uv run python scripts/research/e28_s1_gap_analysis.py
"""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALEXANDER_GT = PROJECT_ROOT / "docs/samplePDF/Alexander_GroundTruth.csv"
ALEXANDER_PDF = PROJECT_ROOT / "docs/samplePDF/Clucth_Alexander_District_Hospital.pdf"


def analyze_ground_truth():
    """Identify all Not Sampled records in ground truth."""
    with open(ALEXANDER_GT, encoding="utf-8") as f:
        # Skip comment lines starting with #
        lines = [line for line in f if not line.startswith("#")]
    rows = list(csv.DictReader(lines))

    print(f"Total ground truth records: {len(rows)}")
    print()

    not_sampled = []
    sampled = []
    as_per = []
    for i, row in enumerate(rows, 1):
        sno = row["sample_no"].strip()
        if sno == "Not Sampled":
            not_sampled.append((i, row))
        elif sno.upper().startswith("AS PER"):
            as_per.append((i, row))
        else:
            sampled.append((i, row))

    print(f"NATA-sampled: {len(sampled)}")
    print(f"As Per: {len(as_per)}")
    print(f"Not Sampled: {len(not_sampled)}")
    print()

    print("=== NOT SAMPLED RECORDS ===")
    for i, row in not_sampled:
        print(
            f"  #{i:2d}. [{row['building_name'][:25]}] "
            f"{row['room_name'][:25]} | "
            f"{row['location'][:30]} | "
            f"{row['product'][:20]} | "
            f"result={row['sample_result']}"
        )

    print()
    print("=== AS PER RECORDS ===")
    for i, row in as_per:
        print(
            f"  #{i:2d}. [{row['building_name'][:25]}] "
            f"{row['room_name'][:25]} | "
            f"{row['location'][:30]} | "
            f"{row['product'][:20]} | "
            f"sample={row['sample_no'][:20]}"
        )

    print()
    print("=== ALL RECORDS ===")
    for i, row in enumerate(rows, 1):
        marker = ""
        if row["sample_no"] == "Not Sampled":
            marker = " *** NOT SAMPLED"
        elif row["sample_no"].upper().startswith("AS PER"):
            marker = " (as per)"
        print(
            f"  {i:2d}. [{row['building_name'][:25]}] "
            f"{row['room_name'][:25]} | "
            f"{row['product'][:20]} | "
            f"sample={row['sample_no'][:20]}{marker}"
        )


def scan_pdf_not_sampled():
    """Scan the Alexander PDF for 'Not Sampled' patterns."""
    try:
        import fitz
    except ImportError:
        print("PyMuPDF not available, skipping PDF scan")
        return

    doc = fitz.open(str(ALEXANDER_PDF))
    print(f"\n\n=== PDF SCAN: {doc.page_count} pages ===\n")

    for i, page in enumerate(doc):
        text = page.get_text()
        if "Not Sampled" not in text:
            continue

        # Find item numbers followed by Not Sampled
        lines = text.split("\n")
        for j, line in enumerate(lines):
            if "Not Sampled" in line:
                start = max(0, j - 5)
                end = min(len(lines), j + 5)
                context = lines[start:end]
                print(
                    f"  Page {i + 1}, line {j}: {' | '.join(ln.strip() for ln in context if ln.strip())}"
                )
                print()


if __name__ == "__main__":
    analyze_ground_truth()
    scan_pdf_not_sampled()
