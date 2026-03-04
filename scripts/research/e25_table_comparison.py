#!/usr/bin/env python3
"""E25-S2: Head-to-head comparison — PyMuPDF vs Docling Direct API.

Compares table extraction quality on Broadmeadows benchmark PDF against
31 ground truth records from Clutch_Broadmeadows.csv.

Usage:
    uv run python scripts/research/e25_table_comparison.py \
        docs/samplePDF/Clutch_Broadmeadows.pdf \
        docs/samplePDF/Clutch_Broadmeadows.csv \
        research-output/e25/

Output:
    research-output/e25/
    ├── pymupdf/
    │   ├── full_text.txt
    │   └── summary.json
    ├── docling_direct_api/
    │   ├── table_N.csv
    │   ├── table_N.md
    │   ├── table_N.html
    │   ├── table_N_analysis.json
    │   ├── markdown_full.md
    │   └── summary.json
    ├── cross_reference.json
    └── comparison_summary.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Part A: PyMuPDF Baseline Extraction
# ---------------------------------------------------------------------------


def extract_pymupdf(pdf_path: str) -> dict:
    """Extract full text with page markers (production method)."""
    import fitz

    start = time.time()
    doc = fitz.open(pdf_path)

    pages = []
    full_text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        full_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        pages.append(
            {
                "page": page_num + 1,
                "char_count": len(text),
                "line_count": text.count("\n"),
            }
        )

    full_text = "\n".join(full_text_parts)
    duration = time.time() - start
    doc.close()

    return {
        "method": "pymupdf",
        "duration_seconds": round(duration, 3),
        "total_chars": len(full_text),
        "total_lines": full_text.count("\n"),
        "total_pages": len(pages),
        "tables_found": 0,
        "tables": [],
        "full_text": full_text,
        "pages": pages,
    }


# ---------------------------------------------------------------------------
# Part B: Docling Direct API Extraction
# ---------------------------------------------------------------------------


def _normalize_column(col: str) -> str:
    """Normalize compound column headers from Docling.

    Strips site address prefix and other compound naming.
    E.g. 'Site Address: Broadmeadows Police Station.Sample Number' -> 'Sample Number'
    """
    parts = str(col).split(".")
    # Take the last meaningful segment
    normalized = parts[-1].strip()
    # If empty after strip, fall back to full string
    if not normalized:
        normalized = str(col).strip()
    return normalized


def _clean_cell_value(x: object) -> str:
    """Clean a cell value — join split strings, handle Series objects."""
    if x is None:
        return ""
    if hasattr(x, "iloc"):
        # pandas Series in cell (from merged cells) — take first value
        try:
            return " ".join(str(x.iloc[0]).split())
        except (IndexError, AttributeError):
            return str(x)
    if isinstance(x, str):
        # Join split strings (e.g. '34511-039- 001' -> '34511-039-001')
        return " ".join(x.split())
    return str(x)


def extract_docling_direct(pdf_path: str) -> dict:
    """Extract tables as DataFrames + HTML + markdown via Docling Direct API."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TableFormerMode,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    start = time.time()

    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    conv_result = converter.convert(pdf_path)
    doc = conv_result.document

    tables = []
    for table_ix, table in enumerate(doc.tables):
        try:
            df = table.export_to_dataframe(doc=doc)

            # 1. Save raw columns before normalization
            raw_columns = list(df.columns)

            # 2. Normalize column headers
            normalized_cols = [_normalize_column(c) for c in df.columns]
            # Handle duplicate normalized names by appending suffix
            seen: dict[str, int] = {}
            deduped = []
            for col in normalized_cols:
                if col in seen:
                    seen[col] += 1
                    deduped.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    deduped.append(col)
            df.columns = deduped

            # 3. Clean cell values
            for col in df.columns:
                df[col] = df[col].apply(_clean_cell_value)

            # 4. Get HTML (with doc= to suppress deprecation warning)
            try:
                html = table.export_to_html(doc=doc)
            except TypeError:
                html = table.export_to_html()

            # 5. Get page provenance
            page_no = table.prov[0].page_no if table.prov else -1

            # 6. Detect ACM indicators in this table
            flat_text = df.to_string().lower()
            indicators = {}
            for term in [
                "same as",
                "as per",
                "not sampled",
                "assumed positive",
                "assumed",
                "no access",
                "34511",
                "negative",
                "positive",
                "battery charger",
                "fuse cartridge",
                "internal lining",
                "disabled toilet",
                "lift foyer",
                "switch room",
            ]:
                indicators[term] = term in flat_text

            tables.append(
                {
                    "table_index": table_ix,
                    "page": page_no,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "raw_column_names": raw_columns,
                    "normalized_column_names": list(df.columns),
                    "markdown": df.to_markdown(index=False),
                    "html": html,
                    "csv": df.to_csv(index=False),
                    "dataframe": df,
                    "sample_rows": df.head(5).to_dict(orient="records"),
                    "has_merged_cells": "colspan" in html or "rowspan" in html,
                    "acm_indicators": indicators,
                }
            )
        except Exception as e:
            tables.append(
                {
                    "table_index": table_ix,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

    # Also get the full markdown export (Approach C comparison)
    markdown_text = doc.export_to_markdown()

    duration = time.time() - start

    return {
        "method": "docling_direct_api",
        "duration_seconds": round(duration, 3),
        "total_chars": len(markdown_text),
        "total_lines": markdown_text.count("\n"),
        "tables_found": len(tables),
        "tables_with_errors": sum(1 for t in tables if "error" in t),
        "tables": tables,
        "markdown_full": markdown_text,
    }


# ---------------------------------------------------------------------------
# Part C: Ground Truth Cross-Reference
# ---------------------------------------------------------------------------


def cross_reference_ground_truth(docling_result: dict, gt_csv_path: str) -> dict:
    """Compare Docling DataFrame rows against ground truth CSV.

    Strategy:
    1. Load ground truth CSV
    2. For each register table (pages 5, 6, 7), collect rows
    3. Match by NATA sample number (primary) or room+product (fallback)
    4. Count: matched, missing, extra, special categories
    """
    gt = pd.read_csv(gt_csv_path)
    gt_records = len(gt)

    sample_col = "NATA Endorsed Sample number (if available)"
    result_col = "Sample Result"
    room_col = "Room or Area"
    location_col = "Location in Room"
    item_col = "Specific Item/ACM Name"

    # Categorize ground truth
    gt_nata = []
    gt_as_per = []
    gt_not_sampled = []

    for i, row in gt.iterrows():
        sample = str(row[sample_col]).strip()
        rec = {
            "gt_index": int(i) + 1,
            "room": str(row[room_col]).strip(),
            "location": str(row[location_col]).strip(),
            "item": str(row[item_col]).strip(),
            "sample": sample,
            "result": str(row[result_col]).strip(),
        }
        if sample.startswith("As Per") or sample.startswith("as per"):
            gt_as_per.append(rec)
        elif sample == "Not Sampled":
            gt_not_sampled.append(rec)
        else:
            gt_nata.append(rec)

    # Collect all register table rows from Docling
    register_pages = set()
    docling_rows = []
    for table in docling_result["tables"]:
        if "error" in table:
            continue
        page = table.get("page", -1)
        # Register tables are on pages 5, 6, 7 per S1
        if page in [5, 6, 7]:
            register_pages.add(page)
            df = table["dataframe"]
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                row_dict["_source_page"] = page
                row_dict["_source_table"] = table["table_index"]
                docling_rows.append(row_dict)

    # Build analysis
    analysis = {
        "ground_truth_records": gt_records,
        "ground_truth_nata": len(gt_nata),
        "ground_truth_as_per": len(gt_as_per),
        "ground_truth_not_sampled": len(gt_not_sampled),
        "docling_register_pages": sorted(register_pages),
        "docling_register_rows": len(docling_rows),
        "matches": {
            "by_sample_number": 0,
            "by_as_per_reference": 0,
            "by_room_product": 0,
        },
        "indicators": {
            "as_per_rows_found": 0,
            "not_sampled_rows_found": 0,
            "assumed_positive_found": 0,
            "no_access_found": 0,
        },
        "missing_record_hunt": [],
        "sample_numbers_found": [],
        "as_per_references_found": [],
    }

    # Search for sample numbers
    for row in docling_rows:
        row_str = " ".join(str(v) for v in row.values()).lower()

        # Sample number matching
        for gt_rec in gt_nata:
            sample_num = gt_rec["sample"].lower()
            if sample_num in row_str:
                analysis["matches"]["by_sample_number"] += 1
                if gt_rec["sample"] not in analysis["sample_numbers_found"]:
                    analysis["sample_numbers_found"].append(gt_rec["sample"])

        # As Per reference matching
        for gt_rec in gt_as_per:
            ref = gt_rec["sample"].lower().replace("as per ", "")
            if ref in row_str and ("same as" in row_str or "as per" in row_str):
                analysis["matches"]["by_as_per_reference"] += 1
                if gt_rec["sample"] not in analysis["as_per_references_found"]:
                    analysis["as_per_references_found"].append(gt_rec["sample"])

        # Indicator detection
        if "same as" in row_str or "as per" in row_str:
            analysis["indicators"]["as_per_rows_found"] += 1
        if "not sampled" in row_str:
            analysis["indicators"]["not_sampled_rows_found"] += 1
        if "assumed positive" in row_str or "assumed" in row_str:
            analysis["indicators"]["assumed_positive_found"] += 1
        if "no access" in row_str:
            analysis["indicators"]["no_access_found"] += 1

    # Hunt for the 3 missing E23 records
    missing_records = [
        {
            "id": "MISSING-1",
            "gt_index": 9,
            "description": "Switch Room / Automatic Battery Charger / Fuse cartridge",
            "search_terms": ["battery charger", "fuse cartridge"],
            "found": False,
            "matching_rows": [],
        },
        {
            "id": "MISSING-2",
            "gt_index": 30,
            "description": "Lift Foyer / Lift / Internal lining",
            "search_terms": ["lift foyer", "internal lining"],
            "found": False,
            "matching_rows": [],
        },
        {
            "id": "MISSING-3",
            "gt_index": 31,
            "description": "Main Foyer / Room Adjacent Disabled Toilet / Unknown",
            "search_terms": ["disabled toilet", "no access"],
            "found": False,
            "matching_rows": [],
        },
    ]

    for rec in missing_records:
        for row in docling_rows:
            row_str = " ".join(str(v) for v in row.values()).lower()
            for term in rec["search_terms"]:
                if term in row_str:
                    rec["found"] = True
                    # Serialize row without internal keys
                    clean_row = {
                        k: v
                        for k, v in row.items()
                        if not k.startswith("_")
                    }
                    if clean_row not in rec["matching_rows"]:
                        rec["matching_rows"].append(clean_row)

    analysis["missing_record_hunt"] = missing_records

    # Also search in ALL tables (not just register pages)
    all_table_search = []
    for table in docling_result["tables"]:
        if "error" in table:
            continue
        df = table["dataframe"]
        flat = df.to_string().lower()
        for rec in missing_records:
            for term in rec["search_terms"]:
                if term in flat:
                    all_table_search.append(
                        {
                            "term": term,
                            "table_index": table["table_index"],
                            "page": table.get("page", -1),
                        }
                    )

    analysis["all_table_search_hits"] = all_table_search

    return analysis


# ---------------------------------------------------------------------------
# Approach C: Markdown Export Analysis
# ---------------------------------------------------------------------------


def analyze_markdown_export(docling_result: dict) -> dict:
    """Analyze the full markdown export for Approach C comparison."""
    md = docling_result.get("markdown_full", "")

    lines = md.split("\n")
    table_lines = [line for line in lines if "|" in line]
    page_markers = [
        line for line in lines if "page" in line.lower() and ("---" in line or "##" in line.lower())
    ]

    # Search for ACM indicators in markdown
    md_lower = md.lower()
    indicators = {}
    for term in [
        "same as",
        "as per",
        "not sampled",
        "assumed positive",
        "no access",
        "34511",
        "battery charger",
        "fuse cartridge",
        "internal lining",
        "disabled toilet",
        "lift foyer",
    ]:
        count = md_lower.count(term)
        indicators[term] = count

    return {
        "total_chars": len(md),
        "total_lines": len(lines),
        "table_lines": len(table_lines),
        "page_markers": len(page_markers),
        "page_marker_samples": page_markers[:5],
        "acm_indicators": indicators,
    }


# ---------------------------------------------------------------------------
# Output Generation
# ---------------------------------------------------------------------------


def save_outputs(
    pymupdf_result: dict,
    docling_result: dict,
    cross_ref: dict,
    markdown_analysis: dict,
    output_dir: Path,
) -> None:
    """Save all output files."""
    # PyMuPDF outputs
    pymupdf_dir = output_dir / "pymupdf"
    pymupdf_dir.mkdir(parents=True, exist_ok=True)

    (pymupdf_dir / "full_text.txt").write_text(
        pymupdf_result["full_text"], encoding="utf-8"
    )

    pymupdf_summary = {k: v for k, v in pymupdf_result.items() if k != "full_text"}
    (pymupdf_dir / "summary.json").write_text(
        json.dumps(pymupdf_summary, indent=2, default=str), encoding="utf-8"
    )

    # Docling outputs
    docling_dir = output_dir / "docling_direct_api"
    docling_dir.mkdir(parents=True, exist_ok=True)

    for table in docling_result["tables"]:
        idx = table["table_index"]

        if "error" in table:
            (docling_dir / f"table_{idx}_error.json").write_text(
                json.dumps(table, indent=2, default=str), encoding="utf-8"
            )
            continue

        # CSV
        (docling_dir / f"table_{idx}.csv").write_text(
            table["csv"], encoding="utf-8"
        )

        # Markdown
        (docling_dir / f"table_{idx}.md").write_text(
            table["markdown"], encoding="utf-8"
        )

        # HTML
        (docling_dir / f"table_{idx}.html").write_text(
            table["html"], encoding="utf-8"
        )

        # Analysis JSON (without large fields)
        analysis = {
            k: v
            for k, v in table.items()
            if k not in ("markdown", "html", "csv", "dataframe")
        }
        (docling_dir / f"table_{idx}_analysis.json").write_text(
            json.dumps(analysis, indent=2, default=str), encoding="utf-8"
        )

    # Full markdown export
    (docling_dir / "markdown_full.md").write_text(
        docling_result.get("markdown_full", ""), encoding="utf-8"
    )

    # Docling summary (without large fields)
    docling_summary = {
        k: v
        for k, v in docling_result.items()
        if k not in ("tables", "markdown_full")
    }
    docling_summary["tables_overview"] = [
        {
            "table_index": t.get("table_index"),
            "page": t.get("page"),
            "rows": t.get("rows"),
            "columns": t.get("columns"),
            "has_merged_cells": t.get("has_merged_cells"),
            "acm_indicators": t.get("acm_indicators"),
            "error": t.get("error"),
        }
        for t in docling_result["tables"]
    ]
    (docling_dir / "summary.json").write_text(
        json.dumps(docling_summary, indent=2, default=str), encoding="utf-8"
    )

    # Cross-reference
    (output_dir / "cross_reference.json").write_text(
        json.dumps(cross_ref, indent=2, default=str), encoding="utf-8"
    )

    # Markdown analysis
    (output_dir / "markdown_analysis.json").write_text(
        json.dumps(markdown_analysis, indent=2, default=str), encoding="utf-8"
    )

    # Comparison summary
    comparison = {
        "pymupdf": {
            "duration_seconds": pymupdf_result["duration_seconds"],
            "total_chars": pymupdf_result["total_chars"],
            "total_lines": pymupdf_result["total_lines"],
            "total_pages": pymupdf_result["total_pages"],
            "tables_found": 0,
        },
        "docling_direct_api": {
            "duration_seconds": docling_result["duration_seconds"],
            "total_chars": docling_result["total_chars"],
            "total_lines": docling_result["total_lines"],
            "tables_found": docling_result["tables_found"],
            "tables_with_errors": docling_result["tables_with_errors"],
            "register_tables": len(cross_ref.get("docling_register_pages", [])),
            "register_rows": cross_ref.get("docling_register_rows", 0),
        },
        "cross_reference": {
            "ground_truth_records": cross_ref["ground_truth_records"],
            "sample_numbers_matched": cross_ref["matches"]["by_sample_number"],
            "as_per_references_matched": cross_ref["matches"]["by_as_per_reference"],
            "unique_sample_numbers_found": len(
                cross_ref.get("sample_numbers_found", [])
            ),
            "unique_as_per_found": len(
                cross_ref.get("as_per_references_found", [])
            ),
            "indicators": cross_ref["indicators"],
            "missing_records_found": sum(
                1
                for r in cross_ref.get("missing_record_hunt", [])
                if r["found"]
            ),
        },
        "markdown_analysis": markdown_analysis,
    }
    (output_dir / "comparison_summary.json").write_text(
        json.dumps(comparison, indent=2, default=str), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Console Report
# ---------------------------------------------------------------------------


def print_report(
    pymupdf_result: dict,
    docling_result: dict,
    cross_ref: dict,
    markdown_analysis: dict,
) -> None:
    """Print summary to console."""
    print("\n" + "=" * 70)
    print("  E25-S2: PyMuPDF vs Docling Direct API — Comparison Results")
    print("=" * 70)

    print("\n--- Performance ---")
    print(f"  PyMuPDF:           {pymupdf_result['duration_seconds']:.2f}s")
    print(f"  Docling Direct API: {docling_result['duration_seconds']:.2f}s")

    print("\n--- Output Size ---")
    print(
        f"  PyMuPDF:  {pymupdf_result['total_chars']:,} chars, "
        f"{pymupdf_result['total_lines']:,} lines"
    )
    print(
        f"  Docling:  {docling_result['total_chars']:,} chars, "
        f"{docling_result['total_lines']:,} lines"
    )

    print("\n--- Tables ---")
    print(f"  Docling tables found: {docling_result['tables_found']}")
    print(f"  Docling table errors: {docling_result['tables_with_errors']}")

    for table in docling_result["tables"]:
        if "error" in table:
            print(
                f"    Table {table['table_index']}: ERROR — {table['error'][:60]}"
            )
        else:
            print(
                f"    Table {table['table_index']}: page={table['page']}, "
                f"{table['rows']}x{table['columns']}, "
                f"merged={'Y' if table['has_merged_cells'] else 'N'}"
            )

    print("\n--- Register Tables (pages 5, 6, 7) ---")
    for table in docling_result["tables"]:
        if "error" not in table and table.get("page") in [5, 6, 7]:
            print(f"\n  Table {table['table_index']} (page {table['page']}):")
            print(f"    Size: {table['rows']} rows × {table['columns']} columns")
            print(f"    Columns: {table['normalized_column_names']}")
            acm = table.get("acm_indicators", {})
            active = [k for k, v in acm.items() if v]
            print(f"    ACM indicators: {active}")

    print("\n--- Ground Truth Cross-Reference ---")
    cr = cross_ref
    print(f"  Ground truth: {cr['ground_truth_records']} records")
    print(f"    NATA-sampled: {cr['ground_truth_nata']}")
    print(f"    As Per: {cr['ground_truth_as_per']}")
    print(f"    Not Sampled: {cr['ground_truth_not_sampled']}")
    print(f"  Docling register rows: {cr['docling_register_rows']}")
    print(f"  Sample numbers matched: {cr['matches']['by_sample_number']}")
    print(
        f"  Unique sample numbers: {len(cr.get('sample_numbers_found', []))}"
    )
    print(
        f"  As Per references matched: {cr['matches']['by_as_per_reference']}"
    )
    print(f"  Unique As Per refs: {len(cr.get('as_per_references_found', []))}")

    print("\n  Indicators in register tables:")
    ind = cr["indicators"]
    for k, v in ind.items():
        print(f"    {k}: {v}")

    print("\n--- THE 3 MISSING RECORDS HUNT ---")
    for rec in cr.get("missing_record_hunt", []):
        status = "FOUND" if rec["found"] else "NOT FOUND"
        print(f"\n  [{status}] {rec['description']}")
        if rec["found"]:
            for row in rec["matching_rows"]:
                # Print first 5 fields
                items = list(row.items())[:5]
                print(f"    Row: {dict(items)}...")

    print("\n  All-table search hits:")
    for hit in cr.get("all_table_search_hits", []):
        print(
            f"    '{hit['term']}' in table {hit['table_index']} (page {hit['page']})"
        )

    print("\n--- Approach C: Markdown Export ---")
    ma = markdown_analysis
    print(f"  Total chars: {ma['total_chars']:,}")
    print(f"  Total lines: {ma['total_lines']:,}")
    print(f"  Table lines (with |): {ma['table_lines']}")
    print(f"  Page markers: {ma['page_markers']}")
    if ma.get("page_marker_samples"):
        for pm in ma["page_marker_samples"]:
            print(f"    '{pm[:80]}'")
    print("  ACM indicators in markdown:")
    for k, v in ma.get("acm_indicators", {}).items():
        print(f"    {k}: {v} occurrences")

    print("\n" + "=" * 70)

    # Final verdict
    missing_found = sum(
        1 for r in cr.get("missing_record_hunt", []) if r["found"]
    )
    print(f"\n  VERDICT: {missing_found}/3 missing E23 records found in DataFrames")

    if missing_found == 3:
        print("  => SUCCESS: Path to 31/31 confirmed!")
    elif missing_found > 0:
        print("  => PARTIAL: Some missing records recovered")
    else:
        as_per = cr["indicators"]["as_per_rows_found"]
        not_sampled = cr["indicators"]["not_sampled_rows_found"]
        if as_per > 0 or not_sampled > 0:
            print(
                f"  => PARTIAL SUCCESS: {as_per} 'As Per' rows, "
                f"{not_sampled} 'Not Sampled' rows in DataFrames"
            )
        else:
            print("  => FAILURE: No special rows found — possible fragmentation")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "Usage: python e25_table_comparison.py <pdf_path> <csv_path> <output_dir>"
        )
        return 1

    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    output_dir = Path(sys.argv[3])

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        return 1
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Running PyMuPDF extraction...")
    pymupdf_result = extract_pymupdf(pdf_path)
    print(
        f"  Done: {pymupdf_result['duration_seconds']:.2f}s, "
        f"{pymupdf_result['total_chars']:,} chars"
    )

    print("\n[2/4] Running Docling Direct API extraction...")
    docling_result = extract_docling_direct(pdf_path)
    print(
        f"  Done: {docling_result['duration_seconds']:.2f}s, "
        f"{docling_result['tables_found']} tables"
    )

    print("\n[3/4] Cross-referencing with ground truth...")
    cross_ref = cross_reference_ground_truth(docling_result, csv_path)
    markdown_analysis = analyze_markdown_export(docling_result)
    print("  Done")

    print("\n[4/4] Saving outputs...")
    save_outputs(
        pymupdf_result, docling_result, cross_ref, markdown_analysis, output_dir
    )
    print(f"  Saved to {output_dir}/")

    print_report(pymupdf_result, docling_result, cross_ref, markdown_analysis)

    return 0


if __name__ == "__main__":
    sys.exit(main())
