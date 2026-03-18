"""Convert BAR export CSVs to normalized ground truth CSVs.

Reads the full BAR CSVs from docs/samplePDF/ and outputs normalized CSVs
using ACMExtractionRecord field names into scripts/eval/ground_truth/.

Usage:
    cd $CLAUDE_PROJECT_DIR
    uv run python scripts/eval/convert_ground_truth.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Output fields matching ACMExtractionRecord
OUTPUT_FIELDS = [
    "room_name",
    "floor_level",
    "location",
    "product",
    "material_description",
    "friable",
    "sample_no",
    "sample_result",
    "area_type",
    "material_condition",
    "disturbance_potential",
]


def convert_broadmeadows():
    """Convert Broadmeadows BAR CSV to normalized ground truth."""
    src = PROJECT_ROOT / "docs/samplePDF/Clutch_Broadmeadows.csv"
    dst = PROJECT_ROOT / "scripts/eval/ground_truth/broadmeadows.csv"

    # BAR column → ACMExtractionRecord field
    col_map = {
        "Room or Area": "room_name",
        "Level": "floor_level",
        "Location in Room": "location",
        "Specific Item/ACM Name": "product",
        "ACM Product Type": "material_description",
        "Friability of material": "friable",
        "NATA Endorsed Sample number (if available)": "sample_no",
        "Sample Result": "sample_result",
        "Internal / External": "area_type",
        "Condition": "material_condition",
        "Disturbance Potential": "disturbance_potential",
    }

    rows = []
    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out = {}
            for bar_col, field in col_map.items():
                val = row.get(bar_col, "").strip()
                out[field] = val if val else ""
            rows.append(out)

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Broadmeadows: {len(rows)} records → {dst}")
    return len(rows)


def convert_alexander():
    """Convert Alexander ground truth CSV to normalized format.

    Alexander_GroundTruth.csv has a simpler schema (7 fields) with comment lines.
    We map what's available and leave other fields empty.
    """
    src = PROJECT_ROOT / "docs/samplePDF/Alexander_GroundTruth.csv"
    dst = PROJECT_ROOT / "scripts/eval/ground_truth/alexander.csv"

    # Alexander GT column → ACMExtractionRecord field
    col_map = {
        "room_name": "room_name",
        "location": "location",
        "product": "product",
        "sample_no": "sample_no",
        "sample_result": "sample_result",
        "friable": "friable",
    }

    rows = []
    with open(src, newline="", encoding="utf-8") as f:
        # Skip comment lines starting with #
        lines = [line for line in f if not line.startswith("#")]

    reader = csv.DictReader(lines)
    for row in reader:
        out = {field: "" for field in OUTPUT_FIELDS}
        for gt_col, field in col_map.items():
            val = row.get(gt_col, "").strip()
            out[field] = val if val else ""
        # building_name is not in OUTPUT_FIELDS but useful for matching
        # We don't include it in the normalized CSV since ACMExtractionRecord
        # uses building_id instead
        rows.append(out)

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Alexander: {len(rows)} records → {dst}")
    return len(rows)


if __name__ == "__main__":
    b = convert_broadmeadows()
    a = convert_alexander()
    print(f"\nTotal: {b + a} ground truth records")
    if b != 30:
        print(f"WARNING: Expected 30 Broadmeadows records, got {b}", file=sys.stderr)
    if a != 43:
        print(f"WARNING: Expected 43 Alexander records, got {a}", file=sys.stderr)
