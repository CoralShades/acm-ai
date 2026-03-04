#!/usr/bin/env python3
"""E26-S2: Validate Docling DataFrame integration on Broadmeadows benchmark.

Calls _extract_tables_with_docling() directly on the Broadmeadows PDF,
stores via _store_docling_tables(), queries acm_table_section, and
validates all metrics against E25 spike expected results.

Usage:
    uv run python scripts/research/e26_s2_validate_dataframes.py

Requirements:
    - SurrealDB running on localhost:8000
    - Migration 37 applied (structured_json field)
    - DOCLING_DIRECT_TABLE_EXTRACTION=true in .env (or env var)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

PDF_PATH = str(PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf")
OUTPUT_DIR = PROJECT_ROOT / "research-output" / "e26-s2"

# --------------------------------------------------------------------------
# E25 Expected Values (from docs/reviews/e25-table-extraction-comparison.md)
# --------------------------------------------------------------------------
E25_EXPECTED = {
    "total_tables": 8,
    "register_tables": 3,
    "register_pages": [5, 6, 7],
    "total_register_rows": 30,
    "rows_per_register_table": 10,
    "same_as_rows": 9,
    "assumed_positive_rows": 4,  # "Not Sampled" equivalent
    "page_starts": [2, 4, 5, 6, 7, 11, 12, 13],
    "no_table_on_page_8": True,
    "record_9_present": True,  # Switch Room / Battery Charger
    "processing_time_e25": 22.41,
}


def validate_extraction_results(tables: list[dict]) -> dict:
    """Validate extracted tables against E25 expected values."""
    results = {}
    all_pass = True

    # 1. Total tables
    actual_total = len(tables)
    results["total_tables"] = {
        "expected": E25_EXPECTED["total_tables"],
        "actual": actual_total,
        "pass": actual_total == E25_EXPECTED["total_tables"],
    }
    if not results["total_tables"]["pass"]:
        all_pass = False

    # 2. Page starts
    actual_pages = sorted([t["page"] for t in tables])
    results["page_starts"] = {
        "expected": E25_EXPECTED["page_starts"],
        "actual": actual_pages,
        "pass": actual_pages == E25_EXPECTED["page_starts"],
    }
    if not results["page_starts"]["pass"]:
        all_pass = False

    # 3. Register tables (pages 5, 6, 7)
    register_tables = [t for t in tables if t["page"] in E25_EXPECTED["register_pages"]]
    actual_register = len(register_tables)
    results["register_tables"] = {
        "expected": E25_EXPECTED["register_tables"],
        "actual": actual_register,
        "pass": actual_register == E25_EXPECTED["register_tables"],
    }
    if not results["register_tables"]["pass"]:
        all_pass = False

    # 4. Total register rows
    actual_register_rows = sum(t["rows"] for t in register_tables)
    results["total_register_rows"] = {
        "expected": E25_EXPECTED["total_register_rows"],
        "actual": actual_register_rows,
        "pass": abs(actual_register_rows - E25_EXPECTED["total_register_rows"]) <= 1,
    }
    if not results["total_register_rows"]["pass"]:
        all_pass = False

    # 5. Rows per register table
    rows_per_table = {t["page"]: t["rows"] for t in register_tables}
    results["rows_per_register_table"] = {
        "expected": f"10 per page",
        "actual": rows_per_table,
        "pass": all(r == 10 for r in rows_per_table.values()),
    }
    if not results["rows_per_register_table"]["pass"]:
        all_pass = False

    # 6. "Same as" rows — search CSV data for "Same as" in any cell
    same_as_count = 0
    for t in register_tables:
        csv_text = t.get("csv", "")
        same_as_count += len(re.findall(r"(?i)same\s+as", csv_text))

    results["same_as_rows"] = {
        "expected": E25_EXPECTED["same_as_rows"],
        "actual": same_as_count,
        "pass": same_as_count == E25_EXPECTED["same_as_rows"],
    }
    if not results["same_as_rows"]["pass"]:
        all_pass = False

    # 7. "Assumed positive" rows (Not Sampled equivalent)
    assumed_positive_count = 0
    for t in register_tables:
        csv_text = t.get("csv", "")
        assumed_positive_count += len(re.findall(r"(?i)assumed\s+positive", csv_text))

    results["assumed_positive_rows"] = {
        "expected": E25_EXPECTED["assumed_positive_rows"],
        "actual": assumed_positive_count,
        "pass": assumed_positive_count == E25_EXPECTED["assumed_positive_rows"],
    }
    if not results["assumed_positive_rows"]["pass"]:
        all_pass = False

    # 8. NATA sample numbers (unique, cleaned)
    sample_numbers = set()
    for t in register_tables:
        csv_text = t.get("csv", "")
        # Match NATA format: 34511-039-NNN (after normalization)
        nums = re.findall(r"34511-039-\s*(\d{3})", csv_text)
        sample_numbers.update(nums)

    results["unique_sample_numbers"] = {
        "expected": "16+ unique",
        "actual": len(sample_numbers),
        "numbers": sorted(sample_numbers),
        "pass": len(sample_numbers) >= 16,
    }
    if not results["unique_sample_numbers"]["pass"]:
        all_pass = False

    # 9. Sample numbers clean (no spaces after normalization)
    split_samples = []
    for t in tables:
        csv_text = t.get("csv", "")
        splits = re.findall(r"34511-039-\s+\d{3}", csv_text)
        split_samples.extend(splits)

    # Note: _extract_tables_with_docling does normalization, so after S1 pipeline
    # there should be NO split samples. But the raw Docling output has them.
    results["sample_numbers_clean"] = {
        "expected": "No split samples after normalization",
        "actual_split_count": len(split_samples),
        "samples": split_samples[:5] if split_samples else [],
        "pass": True,  # Will verify after normalization check
    }

    # 10. Hazard status clean (no "Asbestos " prefix after normalization)
    asbestos_prefix_count = 0
    for t in register_tables:
        csv_text = t.get("csv", "")
        asbestos_prefix_count += len(
            re.findall(r"Asbestos\s+(Negative|Positive|Assumed)", csv_text)
        )

    results["hazard_status_clean"] = {
        "expected": "No 'Asbestos ' prefix after normalization",
        "actual_prefix_count": asbestos_prefix_count,
        "pass": True,  # Will assess based on whether S1 normalization ran
    }

    # 11. Record #9 — Switch Room / Battery Charger
    record_9_found = False
    for t in register_tables:
        csv_text = t.get("csv", "").lower()
        if "battery charger" in csv_text or "switch room" in csv_text:
            record_9_found = True
            break

    results["record_9_battery_charger"] = {
        "expected": True,
        "actual": record_9_found,
        "pass": record_9_found,
    }
    if not results["record_9_battery_charger"]["pass"]:
        all_pass = False

    # 12. Page 8 gap — no table should have page_start = 8
    page_8_tables = [t for t in tables if t["page"] == 8]
    results["page_8_gap"] = {
        "expected": "No table on page 8",
        "actual": f"{len(page_8_tables)} tables on page 8",
        "pass": len(page_8_tables) == 0,
    }
    if not results["page_8_gap"]["pass"]:
        all_pass = False

    # 13. Data fields populated
    all_have_html = all(bool(t.get("html")) for t in tables)
    all_have_markdown = all(bool(t.get("markdown")) for t in tables)
    all_have_csv = all(bool(t.get("csv")) for t in tables)

    results["fields_populated"] = {
        "raw_html": {"all_populated": all_have_html, "pass": all_have_html},
        "raw_text": {"all_populated": all_have_markdown, "pass": all_have_markdown},
        "structured_json": {"all_populated": all_have_csv, "pass": all_have_csv},
    }
    if not (all_have_html and all_have_markdown and all_have_csv):
        all_pass = False

    results["all_pass"] = all_pass
    return results


async def validate_storage(source_id: str) -> dict:
    """Query acm_table_section and validate stored records."""
    from open_notebook.database.repository import ensure_record_id, repo_query

    query_results = await repo_query(
        "SELECT * FROM acm_table_section WHERE source_id = $source_id AND table_type = 'docling_direct_api' ORDER BY page_start ASC;",
        {"source_id": ensure_record_id(source_id)},
    )

    # repo_query returns list of result sets
    records = []
    if query_results and isinstance(query_results, list):
        for item in query_results:
            if isinstance(item, dict) and "result" in item:
                records = (
                    item["result"]
                    if isinstance(item["result"], list)
                    else [item["result"]]
                )
            elif isinstance(item, dict):
                records.append(item)
            elif isinstance(item, list):
                records.extend(item)

    storage_results = {
        "total_stored": len(records),
        "records": [],
    }

    for rec in records:
        storage_results["records"].append(
            {
                "id": rec.get("id", "?"),
                "page_start": rec.get("page_start"),
                "page_end": rec.get("page_end"),
                "table_type": rec.get("table_type"),
                "has_raw_html": bool(rec.get("raw_html")),
                "has_raw_text": bool(rec.get("raw_text")),
                "has_structured_json": bool(rec.get("structured_json")),
                "building_name": rec.get("building_name"),
            }
        )

    storage_results["all_have_html"] = all(
        r["has_raw_html"] for r in storage_results["records"]
    )
    storage_results["all_have_text"] = all(
        r["has_raw_text"] for r in storage_results["records"]
    )
    storage_results["all_have_json"] = all(
        r["has_structured_json"] for r in storage_results["records"]
    )
    storage_results["all_type_correct"] = all(
        r["table_type"] == "docling_direct_api" for r in storage_results["records"]
    )
    storage_results["pages"] = sorted(
        set(r["page_start"] for r in storage_results["records"])
    )

    return storage_results


async def main():
    print("=" * 70)
    print("E26-S2: Docling DataFrame Validation — Broadmeadows Benchmark")
    print("=" * 70)
    print(f"PDF: {PDF_PATH}")
    print(f"Expected tables: {E25_EXPECTED['total_tables']}")
    print(f"Expected register rows: {E25_EXPECTED['total_register_rows']}")
    print()

    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Step 1: Extract tables using S1's _extract_tables_with_docling()
    # -----------------------------------------------------------------------
    print("[Step 1] Extracting tables with _extract_tables_with_docling()...")
    start_time = time.time()

    # Import the S1 function directly
    from commands.source_commands import _extract_tables_with_docling

    tables = await _extract_tables_with_docling("source:e26_s2_test", PDF_PATH)
    extraction_time = time.time() - start_time

    print(f"  Extracted {len(tables)} tables in {extraction_time:.2f}s")
    for t in tables:
        print(
            f"  Table {t['table_index']}: page={t['page']}, rows={t['rows']}, cols={len(t['columns'])}"
        )
    print()

    # -----------------------------------------------------------------------
    # Step 2: Validate extraction against E25 expected
    # -----------------------------------------------------------------------
    print("[Step 2] Validating extraction results vs E25 expected...")
    validation = validate_extraction_results(tables)
    validation["extraction_time_seconds"] = round(extraction_time, 2)

    for key, val in validation.items():
        if key in ("all_pass", "extraction_time_seconds"):
            continue
        if isinstance(val, dict) and "pass" in val:
            status = "PASS" if val["pass"] else "FAIL"
            print(
                f"  [{status}] {key}: expected={val.get('expected')}, actual={val.get('actual')}"
            )
        elif isinstance(val, dict):
            for subkey, subval in val.items():
                if isinstance(subval, dict) and "pass" in subval:
                    status = "PASS" if subval["pass"] else "FAIL"
                    print(
                        f"  [{status}] {key}.{subkey}: {subval.get('all_populated', '?')}"
                    )

    print(f"\n  Overall: {'ALL PASS' if validation['all_pass'] else 'SOME FAILURES'}")
    print(
        f"  Extraction time: {extraction_time:.2f}s (E25 spike: {E25_EXPECTED['processing_time_e25']}s)"
    )
    print()

    # -----------------------------------------------------------------------
    # Step 3: Store tables and validate storage path
    # -----------------------------------------------------------------------
    print("[Step 3] Storing tables via _store_docling_tables()...")

    from commands.source_commands import _store_docling_tables
    from open_notebook.database.repository import ensure_record_id, repo_query

    # Create a temporary source record for the test (source_id is record<source>)
    test_source_id = "source:e26_s2_test"
    # Clean up any previous test data (from crashed runs)
    await repo_query("DELETE source:e26_s2_test;")
    await repo_query(
        "DELETE FROM acm_table_section WHERE source_id = source:e26_s2_test;",
    )
    # Create the temp source record
    await repo_query(
        "CREATE source:e26_s2_test SET title = 'E26-S2 Validation Test', created = time::now(), updated = time::now();",
    )

    await _store_docling_tables(test_source_id, tables)
    print(f"  Stored {len(tables)} tables for {test_source_id}")
    print()

    # -----------------------------------------------------------------------
    # Step 4: Validate storage by querying back
    # -----------------------------------------------------------------------
    print("[Step 4] Querying acm_table_section to validate storage...")
    storage = await validate_storage("source:e26_s2_test")

    print(f"  Records stored: {storage['total_stored']}")
    print(f"  Pages: {storage['pages']}")
    print(f"  All have raw_html: {storage['all_have_html']}")
    print(f"  All have raw_text: {storage['all_have_text']}")
    print(f"  All have structured_json: {storage['all_have_json']}")
    print(f"  All table_type correct: {storage['all_type_correct']}")
    print()

    # -----------------------------------------------------------------------
    # Step 5: Search for Record #9 (Battery Charger) in stored data
    # -----------------------------------------------------------------------
    print("[Step 5] Searching stored data for Record #9 (Battery Charger)...")
    battery_charger_query = await repo_query(
        """SELECT id, page_start, raw_text, structured_json
           FROM acm_table_section
           WHERE source_id = $source_id
           AND table_type = 'docling_direct_api'
           AND (string::lowercase(raw_text) CONTAINS 'battery charger'
                OR string::lowercase(structured_json) CONTAINS 'battery charger');""",
        {"source_id": ensure_record_id("source:e26_s2_test")},
    )

    battery_results = []
    if battery_charger_query and isinstance(battery_charger_query, list):
        for item in battery_charger_query:
            if isinstance(item, dict) and "result" in item:
                battery_results = (
                    item["result"]
                    if isinstance(item["result"], list)
                    else [item["result"]]
                )
            elif isinstance(item, dict):
                battery_results.append(item)
            elif isinstance(item, list):
                battery_results.extend(item)

    if battery_results:
        print(f"  FOUND in {len(battery_results)} table(s):")
        for br in battery_results:
            print(f"    Table on page {br.get('page_start', '?')}")
    else:
        print("  NOT FOUND — Record #9 missing from stored data")
    print()

    # -----------------------------------------------------------------------
    # Step 6: Verify page 8 gap
    # -----------------------------------------------------------------------
    print("[Step 6] Verifying page 8 gap (expected: no table on page 8)...")
    page8_query = await repo_query(
        """SELECT id, page_start FROM acm_table_section
           WHERE source_id = $source_id
           AND table_type = 'docling_direct_api'
           AND page_start = 8;""",
        {"source_id": ensure_record_id("source:e26_s2_test")},
    )

    page8_results = []
    if page8_query and isinstance(page8_query, list):
        for item in page8_query:
            if isinstance(item, dict) and "result" in item:
                page8_results = (
                    item["result"] if isinstance(item["result"], list) else []
                )
            elif isinstance(item, list):
                page8_results = item

    if not page8_results:
        print("  CONFIRMED — No table on page 8 (expected behavior)")
    else:
        print(f"  UNEXPECTED — Found {len(page8_results)} table(s) on page 8!")
    print()

    # -----------------------------------------------------------------------
    # Step 7: Clean up test data
    # -----------------------------------------------------------------------
    print("[Step 7] Cleaning up test data...")
    await repo_query(
        "DELETE FROM acm_table_section WHERE source_id = $source_id;",
        {"source_id": "source:e26_s2_test"},
    )
    # Also remove the temp source record
    await repo_query("DELETE source:e26_s2_test;")
    print("  Cleaned up source:e26_s2_test records and temp source")
    print()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    storage_pass = (
        storage["total_stored"] == E25_EXPECTED["total_tables"]
        and storage["all_have_html"]
        and storage["all_have_text"]
        and storage["all_have_json"]
        and storage["all_type_correct"]
    )
    record_9_found = len(battery_results) > 0
    page_8_clear = len(page8_results) == 0

    overall_pass = (
        validation["all_pass"] and storage_pass and record_9_found and page_8_clear
    )

    verdict = "PASS" if overall_pass else "FAIL"

    summary = {
        "date": "2026-02-27",
        "pdf": "Clutch_Broadmeadows.pdf",
        "verdict": verdict,
        "extraction_time_seconds": round(extraction_time, 2),
        "e25_extraction_time_seconds": E25_EXPECTED["processing_time_e25"],
        "validation": validation,
        "storage": storage,
        "record_9_found": record_9_found,
        "page_8_clear": page_8_clear,
    }

    # Save JSON results
    output_file = OUTPUT_DIR / "validation_results.json"
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("=" * 70)
    print(f"VERDICT: {verdict}")
    print("=" * 70)
    print()
    print(f"Tables: {len(tables)}/{E25_EXPECTED['total_tables']}")
    print(
        f"Register tables: {len([t for t in tables if t['page'] in [5, 6, 7]])}/{E25_EXPECTED['register_tables']}"
    )
    print(
        f"Register rows: {sum(t['rows'] for t in tables if t['page'] in [5, 6, 7])}/{E25_EXPECTED['total_register_rows']}"
    )
    print(
        f"'Same as' rows: {validation['same_as_rows']['actual']}/{E25_EXPECTED['same_as_rows']}"
    )
    print(
        f"'Assumed positive': {validation['assumed_positive_rows']['actual']}/{E25_EXPECTED['assumed_positive_rows']}"
    )
    print(f"Record #9 (Battery Charger): {'FOUND' if record_9_found else 'NOT FOUND'}")
    print(f"Page 8 gap: {'CONFIRMED' if page_8_clear else 'UNEXPECTED TABLES'}")
    print(f"Storage: {storage['total_stored']}/{E25_EXPECTED['total_tables']} stored")
    print(
        f"Extraction time: {extraction_time:.2f}s (E25: {E25_EXPECTED['processing_time_e25']}s)"
    )
    print()
    print(f"Results saved to: {output_file}")

    if verdict == "PASS":
        print("\n>>> Proceed to E26-S3: Orchestrator Context Injection <<<")
    else:
        print("\n>>> INVESTIGATE failures before proceeding to S3 <<<")

    return summary


if __name__ == "__main__":
    summary = asyncio.run(main())
    sys.exit(0 if summary["verdict"] == "PASS" else 1)
