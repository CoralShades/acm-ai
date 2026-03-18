#!/usr/bin/env python3
"""E36-S4: Ollama Multi-Model Benchmark Runner.

Runs ACM extraction with 6 Ollama models against 2 ground-truth PDFs,
compares results, and generates per-run detail files + summary table.

Usage:
    uv run python scripts/benchmark_ollama.py [--model MODEL] [--pdf PDF]

Options:
    --model MODEL   Run only this model (e.g., "qwen2.5:7b")
    --pdf PDF       Run only this PDF ("broadmeadows" or "alexander")
    --timeout SECS  Max seconds to wait per extraction (default: 600)
"""

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import requests

# Force unbuffered output for background runs
sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]

API_BASE = "http://localhost:5055"

# Model name -> record ID mapping
MODELS = {
    "qwen2.5:7b": "model:6uszykjp9wrwe2jkwsea",
    "llama3.1:8b": "model:m7tdn5b7lavy0z1yg14j",
    "mistral:7b": "model:wmmp7o4sgz0qs09bo9p6",
    "qwen3:32b": "model:jb3rgqhs31vws1zth4h2",
    "qwen2.5:32b": "model:znay2wr8u9q39lxj2q37",
    "phi4:14b": "model:wpfnb5ks1sq5ncqbqjzb",
}

SOURCES = {
    "broadmeadows": "source:25pxnu7ot2oy2oi7dmc0",
    "alexander": "source:ubbsh2i0b6ypy64vs1hh",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "docs" / "sprint-artifacts" / "e36" / "benchmark-results"
GT_BROADMEADOWS = (
    PROJECT_ROOT
    / "tests"
    / "e2e"
    / "fixtures"
    / "ara-documents"
    / "broadmeadows-expected-results.json"
)
GT_ALEXANDER = PROJECT_ROOT / "docs" / "samplePDF" / "Alexander_GroundTruth.csv"


@dataclass
class RunResult:
    model: str
    pdf: str
    source_id: str
    command_id: str = ""
    status: str = "pending"
    records_extracted: int = 0
    ground_truth_count: int = 0
    matched_records: int = 0
    record_recall_pct: float = 0.0
    field_accuracy_pct: float = 0.0
    elapsed_seconds: float = 0.0
    error: str = ""
    field_scores: dict = field(default_factory=dict)
    extracted_records: list = field(default_factory=list)


def load_broadmeadows_gt() -> list[dict]:
    with open(GT_BROADMEADOWS, encoding="utf-8") as f:
        data = json.load(f)
    return data["ground_truth_records"]


def load_alexander_gt() -> list[dict]:
    records = []
    with open(GT_ALEXANDER, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def fuzzy_match(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def normalize(val) -> str:
    if val is None:
        return ""
    return str(val).lower().strip()


def match_records(
    extracted: list[dict], ground_truth: list[dict], pdf_name: str
) -> tuple[int, dict]:
    """Match extracted records to ground truth and compute field accuracy."""
    matched = 0
    total_field_checks = 0
    correct_field_checks = 0
    field_correct = {}
    field_total = {}

    gt_used = set()

    for ext in extracted:
        best_score = 0.0
        best_idx = -1
        ext_room = normalize(ext.get("room_name", ""))
        ext_product = normalize(ext.get("product", ""))
        ext_building = normalize(ext.get("building_name", ""))

        for i, gt in enumerate(ground_truth):
            if i in gt_used:
                continue
            gt_room = normalize(gt.get("room_name", ""))
            gt_product = normalize(gt.get("product", ""))

            room_sim = fuzzy_match(ext_room, gt_room)
            product_sim = fuzzy_match(ext_product, gt_product)

            if pdf_name == "alexander":
                gt_building = normalize(gt.get("building_name", ""))
                building_sim = fuzzy_match(ext_building, gt_building)
                score = building_sim * 0.3 + room_sim * 0.4 + product_sim * 0.3
            else:
                score = room_sim * 0.5 + product_sim * 0.5

            if score > best_score:
                best_score = score
                best_idx = i

        if best_score >= 0.5 and best_idx >= 0:
            matched += 1
            gt_used.add(best_idx)
            gt_rec = ground_truth[best_idx]

            # Compare fields
            if pdf_name == "broadmeadows":
                compare_fields = [
                    ("room_name", "room_name"),
                    ("product", "product"),
                    ("friable", "friable"),
                    ("material_condition", "material_condition"),
                    ("risk_status", "risk_status"),
                    ("sample_no", "sample_no"),
                ]
            else:
                compare_fields = [
                    ("room_name", "room_name"),
                    ("product", "product"),
                    ("friable", "friable"),
                    ("sample_no", "sample_no"),
                    ("building_name", "building_name"),
                ]

            for ext_field, gt_field in compare_fields:
                ext_val = normalize(ext.get(ext_field, ""))
                gt_val = normalize(gt_rec.get(gt_field, ""))
                total_field_checks += 1
                field_total[ext_field] = field_total.get(ext_field, 0) + 1
                if fuzzy_match(ext_val, gt_val) >= 0.8:
                    correct_field_checks += 1
                    field_correct[ext_field] = field_correct.get(ext_field, 0) + 1

    field_accuracy = {}
    for f in field_total:
        field_accuracy[f] = (
            round(100 * field_correct.get(f, 0) / field_total[f], 1)
            if field_total[f]
            else 0.0
        )

    overall = (
        round(100 * correct_field_checks / total_field_checks, 1)
        if total_field_checks
        else 0.0
    )
    return matched, {"overall": overall, "per_field": field_accuracy}


def set_extraction_model(model_id: str) -> bool:
    resp = requests.put(
        f"{API_BASE}/api/models/defaults",
        json={"default_extraction_model": model_id},
        timeout=10,
    )
    return resp.status_code == 200


def trigger_extraction(source_id: str) -> str:
    resp = requests.post(
        f"{API_BASE}/api/acm/extract",
        json={"source_id": source_id, "force": True},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["command_id"]


def poll_extraction(command_id: str, source_id: str, timeout: int = 600) -> str:
    """Poll for extraction completion using dual strategy:
    1. Check extraction-progress status (primary)
    2. Check if records have appeared for the source (fallback)

    The extraction_progress table sometimes gets stuck at 'running' even
    after the worker completes. The record-count check is more reliable.
    """
    start = time.time()
    # Wait a bit for records to be deleted (force=true) before polling
    time.sleep(10)
    while time.time() - start < timeout:
        # Strategy 1: Check extraction-progress status
        try:
            resp = requests.get(
                f"{API_BASE}/api/acm/extraction-progress/{command_id}",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                if status in ("completed", "failed", "partial"):
                    return status
        except requests.RequestException:
            pass

        # Strategy 2: Check if new records have appeared and stabilized.
        # force=true deletes all records first. Once records reappear
        # and the count is stable across 2 checks, extraction is done.
        if time.time() - start > 60:
            try:
                resp = requests.get(
                    f"{API_BASE}/api/acm/records",
                    params={"source_id": source_id, "limit": 1},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    count = data.get("total", 0)
                    if count > 0:
                        # Wait 15s and re-check for stability
                        print(f"    Records detected ({count}), verifying stability...")
                        time.sleep(15)
                        resp2 = requests.get(
                            f"{API_BASE}/api/acm/records",
                            params={"source_id": source_id, "limit": 1},
                            timeout=10,
                        )
                        if resp2.status_code == 200:
                            count2 = resp2.json().get("total", 0)
                            if count2 >= count:
                                print(
                                    f"    Stable at {count2} records — extraction complete"
                                )
                                return "completed"
            except requests.RequestException:
                pass

        time.sleep(10)
    return "timeout"


def get_records(source_id: str) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/acm/records",
        params={"source_id": source_id, "limit": 500},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("records", [])


def write_run_detail(result: RunResult):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = result.model.replace(":", "").replace(".", "") + "-" + result.pdf
    path = RESULTS_DIR / f"{slug}.md"

    lines = [
        f"# Benchmark Run: {result.model} x {result.pdf.title()}",
        f"",
        f"- **Model**: {result.model}",
        f"- **PDF**: {result.pdf}",
        f"- **Source ID**: {result.source_id}",
        f"- **Command ID**: {result.command_id}",
        f"- **Status**: {result.status}",
        f"- **Elapsed**: {result.elapsed_seconds:.1f}s",
        f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"## Record Counts",
        f"- Ground truth: {result.ground_truth_count}",
        f"- Extracted: {result.records_extracted}",
        f"- Matched: {result.matched_records}",
        f"- Record recall: {result.record_recall_pct:.1f}%",
        f"",
        f"## Field Accuracy",
        f"- Overall: {result.field_scores.get('overall', 0):.1f}%",
        f"",
        f"| Field | Accuracy |",
        f"|-------|----------|",
    ]

    for fname, acc in sorted(result.field_scores.get("per_field", {}).items()):
        lines.append(f"| {fname} | {acc:.1f}% |")

    if result.error:
        lines.extend(["", f"## Error", f"```", result.error, f"```"])

    lines.extend(["", f"## Extracted Records ({result.records_extracted} total)", ""])
    for i, rec in enumerate(result.extracted_records[:10], 1):
        lines.append(
            f"{i}. {rec.get('building_name', '?')} / {rec.get('room_name', '?')} / {rec.get('product', '?')}"
        )
    if result.records_extracted > 10:
        lines.append(f"... and {result.records_extracted - 10} more")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {path.name}")


def write_summary(results: list[RunResult]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "summary.md"

    lines = [
        "# E36-S4: Ollama Multi-Model Benchmark Summary",
        "",
        f"**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Total runs**: {len(results)}",
        "",
        "## Results Table",
        "",
        "| Model | PDF | GT | Extracted | Matched | Recall% | Field Acc% | Time(s) | Status |",
        "|-------|-----|----|-----------|---------|---------|------------|---------|--------|",
    ]

    for r in results:
        lines.append(
            f"| {r.model} | {r.pdf} | {r.ground_truth_count} | "
            f"{r.records_extracted} | {r.matched_records} | "
            f"{r.record_recall_pct:.1f} | {r.field_scores.get('overall', 0):.1f} | "
            f"{r.elapsed_seconds:.0f} | {r.status} |"
        )

    # Per-model average
    lines.extend(["", "## Per-Model Average", ""])
    lines.append("| Model | Avg Recall% | Avg Field Acc% | Avg Time(s) |")
    lines.append("|-------|-------------|----------------|-------------|")

    model_groups = {}
    for r in results:
        model_groups.setdefault(r.model, []).append(r)

    best_model = ""
    best_score = 0.0
    for model, runs in sorted(model_groups.items()):
        avg_recall = sum(r.record_recall_pct for r in runs) / len(runs)
        avg_field = sum(r.field_scores.get("overall", 0) for r in runs) / len(runs)
        avg_time = sum(r.elapsed_seconds for r in runs) / len(runs)
        composite = avg_recall * 0.5 + avg_field * 0.5
        if composite > best_score:
            best_score = composite
            best_model = model
        lines.append(
            f"| {model} | {avg_recall:.1f} | {avg_field:.1f} | {avg_time:.0f} |"
        )

    lines.extend(
        [
            "",
            "## Best Performing Model",
            "",
            f"**{best_model}** with composite score {best_score:.1f}% "
            f"(50% recall + 50% field accuracy)",
            "",
            "## Methodology",
            "",
            "- Each model ran extraction with `force=true` (clean slate per run)",
            "- Record matching uses fuzzy string similarity (threshold: 0.5)",
            "- Field accuracy uses fuzzy match (threshold: 0.8 for correct)",
            "- Composite score = 50% record recall + 50% field accuracy",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSummary written: {path}")
    print(f"\nBest model: {best_model} (composite: {best_score:.1f}%)")


def run_benchmark(model_name: str, pdf_name: str, timeout: int) -> RunResult:
    model_id = MODELS[model_name]
    source_id = SOURCES[pdf_name]

    result = RunResult(
        model=model_name,
        pdf=pdf_name,
        source_id=source_id,
        ground_truth_count=31 if pdf_name == "broadmeadows" else 43,
    )

    print(f"\n{'=' * 60}")
    print(f"  {model_name} x {pdf_name}")
    print(f"{'=' * 60}")

    # 1. Set model
    print(f"  Setting extraction model to {model_name} ({model_id})...")
    if not set_extraction_model(model_id):
        result.status = "error"
        result.error = "Failed to set extraction model"
        print(f"  ERROR: {result.error}")
        return result

    # Brief pause to let model change propagate
    time.sleep(2)

    # 2. Trigger extraction
    print(f"  Triggering extraction (force=true)...")
    start_time = time.time()
    try:
        command_id = trigger_extraction(source_id)
        result.command_id = command_id
        print(f"  Command ID: {command_id}")
    except Exception as e:
        result.status = "error"
        result.error = f"Trigger failed: {e}"
        result.elapsed_seconds = time.time() - start_time
        print(f"  ERROR: {result.error}")
        return result

    # 3. Poll for completion
    print(f"  Waiting for completion (timeout: {timeout}s)...")
    status = poll_extraction(command_id, source_id=source_id, timeout=timeout)
    result.elapsed_seconds = time.time() - start_time
    result.status = status
    print(f"  Status: {status} ({result.elapsed_seconds:.1f}s)")

    if status not in ("completed", "partial"):
        result.error = f"Extraction ended with status: {status}"
        print(f"  ERROR: {result.error}")
        write_run_detail(result)
        return result

    # 4. Retrieve records
    print(f"  Retrieving records...")
    try:
        records = get_records(source_id)
        result.records_extracted = len(records)
        result.extracted_records = records
        print(f"  Records extracted: {len(records)}")
    except Exception as e:
        result.error = f"Record retrieval failed: {e}"
        print(f"  ERROR: {result.error}")
        write_run_detail(result)
        return result

    # 5. Compare to ground truth
    print(f"  Comparing to ground truth...")
    if pdf_name == "broadmeadows":
        gt = load_broadmeadows_gt()
    else:
        gt = load_alexander_gt()

    matched, field_scores = match_records(records, gt, pdf_name)
    result.matched_records = matched
    result.record_recall_pct = (
        round(100 * matched / result.ground_truth_count, 1)
        if result.ground_truth_count
        else 0.0
    )
    result.field_scores = field_scores
    result.field_accuracy_pct = field_scores.get("overall", 0.0)

    print(
        f"  Matched: {matched}/{result.ground_truth_count} ({result.record_recall_pct:.1f}% recall)"
    )
    print(f"  Field accuracy: {result.field_accuracy_pct:.1f}%")

    # 6. Write detail file
    write_run_detail(result)
    return result


def main():
    parser = argparse.ArgumentParser(description="E36-S4 Ollama Multi-Model Benchmark")
    parser.add_argument("--model", help="Run only this model")
    parser.add_argument("--pdf", help="Run only this PDF (broadmeadows/alexander)")
    parser.add_argument(
        "--timeout", type=int, default=600, help="Max seconds per extraction"
    )
    args = parser.parse_args()

    # Validate API is up
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        resp.raise_for_status()
    except Exception:
        print("ERROR: API not reachable at", API_BASE)
        sys.exit(1)

    # Filter models/pdfs if specified
    models = {args.model: MODELS[args.model]} if args.model else MODELS
    pdfs = {args.pdf: SOURCES[args.pdf]} if args.pdf else SOURCES

    total_runs = len(models) * len(pdfs)
    print(
        f"\nE36-S4 Benchmark: {len(models)} models x {len(pdfs)} PDFs = {total_runs} runs"
    )
    print(f"Timeout per run: {args.timeout}s")

    results = []
    for i, model_name in enumerate(models):
        for j, pdf_name in enumerate(pdfs):
            run_num = i * len(pdfs) + j + 1
            print(f"\n--- Run {run_num}/{total_runs} ---")
            result = run_benchmark(model_name, pdf_name, args.timeout)
            results.append(result)

    # Write summary
    write_summary(results)

    # Save raw results as JSON for further analysis
    raw_path = RESULTS_DIR / "raw_results.json"
    raw_data = []
    for r in results:
        raw_data.append(
            {
                "model": r.model,
                "pdf": r.pdf,
                "status": r.status,
                "records_extracted": r.records_extracted,
                "ground_truth_count": r.ground_truth_count,
                "matched_records": r.matched_records,
                "record_recall_pct": r.record_recall_pct,
                "field_accuracy_pct": r.field_accuracy_pct,
                "elapsed_seconds": r.elapsed_seconds,
                "field_scores": r.field_scores,
                "error": r.error,
                "command_id": r.command_id,
            }
        )
    raw_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")
    print(f"Raw results: {raw_path}")


if __name__ == "__main__":
    main()
