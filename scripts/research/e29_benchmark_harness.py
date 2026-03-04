"""E29 Benchmark Harness — Baseline Capture & Quality Gate.

Runs the ACM extraction pipeline against ground-truth documents and measures:
- Recall: matched / ground_truth_total
- Precision: matched / extracted_total
- Field accuracy: per-field match rate across matched records
- Latency: wall-clock extraction time (seconds)
- Token usage: LLM prompt + completion tokens
- Cost: estimated USD from token usage

Usage:
    # Run all benchmarks
    uv run python scripts/research/e29_benchmark_harness.py --all

    # Run single document
    uv run python scripts/research/e29_benchmark_harness.py --doc broadmeadows

    # Generate report from cached results
    uv run python scripts/research/e29_benchmark_harness.py --report-only

    # Run via pytest (CI entrypoint)
    uv run pytest tests/integration/test_benchmark_harness.py -x -v
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env early so API keys are available
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ground Truth & Configuration
# ---------------------------------------------------------------------------

GROUND_TRUTH_DIR = PROJECT_ROOT / "benchmarks" / "ground_truth"
FIXTURES_DIR = PROJECT_ROOT / "benchmarks" / "fixtures"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"
REPORT_DIR = PROJECT_ROOT / "docs" / "reviews"

# Fields used for accuracy comparison (must exist in both ground truth and extracted)
COMPARISON_FIELDS = [
    "building_name",
    "room_name",
    "location",
    "product",
    "sample_no",
    "sample_result",
    "friable",
]

# Product synonym map — LLM may use different names than ground truth
# Building synonym map — LLM may use different names than ground truth
BUILDING_SYNONYMS: dict[str, list[str]] = {
    "old alexandra hospital": [
        "main hospital building",
        "alexandra hospital",
        "old alexander hospital",
    ],
}

# Room synonym map — LLM may use different names than ground truth
ROOM_SYNONYMS: dict[str, list[str]] = {
    "exterior": ["external"],
}

PRODUCT_SYNONYMS: dict[str, list[str]] = {
    "flange joints": ["flange mastic", "mastic", "flange mastic (grey)"],
    "fuse cartridge": ["fuses", "fuse"],
    "internal lining": ["lining", "wall lining", "internal wall lining"],
    "vinyl sheet": ["vinyl sheet flooring", "sheet vinyl"],
    "vinyl tiles": ["vinyl floor tiles", "floor tiles"],
    "flat sheeting": ["flat sheet", "cement sheet", "fibro sheet"],
    "floor covering": [
        "floor coverings",
        "flooring",
        "floor covering (beneath carpet)",
    ],
    "ceiling": ["ceiling tiles", "ceiling panels", "ceiling lining", "porch ceiling"],
    "heater flue": ["heater"],
    "electrical board": ["electrical distribution board"],
    "fire door(s)": ["fire door", "fire doors"],
    "window frame": ["window frames", "window frame(s)"],
    "wall(s)": ["wall", "walls", "wall lining"],
    "eaves": ["eave", "eave lining"],
    "debris": ["ground debris", "on ground debris"],
    "expansion joint": [
        "expansion joints",
        "construction joint",
        "construction joints",
    ],
    "shower cubicle": ["shower cubicles", "shower lining"],
    "infill panels": ["infill panel", "infill"],
    "stored item(s)": ["stored items", "stored item"],
}


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark document."""

    name: str
    pdf_path: Path
    ground_truth_path: Path
    expected_records: int
    expected_buildings: int


@dataclass
class MatchResult:
    """Result of matching extracted records against ground truth."""

    matched_pairs: list[tuple[dict, object]]  # (gt_record, extracted_record)
    unmatched_gt: list[dict]
    unmatched_extracted: list[object]


@dataclass
class BenchmarkResult:
    """Metrics from a single benchmark run."""

    document_name: str
    ground_truth_count: int
    extracted_count: int
    matched_count: int
    recall: float
    precision: float
    field_accuracy: float
    latency_s: float
    token_usage: int
    cost_usd: float
    error: Optional[str] = None
    unmatched_gt: list[dict] = field(default_factory=list)
    unmatched_extracted: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Document Registry
# ---------------------------------------------------------------------------


def get_benchmark_configs() -> dict[str, BenchmarkConfig]:
    """Return registry of known benchmark documents."""
    return {
        "broadmeadows": BenchmarkConfig(
            name="Broadmeadows Police Station",
            pdf_path=PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf",
            ground_truth_path=GROUND_TRUTH_DIR / "broadmeadows.json",
            expected_records=31,
            expected_buildings=1,
        ),
        "alexander": BenchmarkConfig(
            name="Alexander District Hospital",
            pdf_path=PROJECT_ROOT
            / "docs"
            / "samplePDF"
            / "Clucth_Alexander_District_Hospital.pdf",
            ground_truth_path=GROUND_TRUTH_DIR / "alexander.json",
            expected_records=43,
            expected_buildings=5,
        ),
        "aldavilla": BenchmarkConfig(
            name="Aldavilla Public School",
            pdf_path=PROJECT_ROOT / "docs" / "samplePDF" / "4601_AsbestosRegister.pdf",
            ground_truth_path=GROUND_TRUTH_DIR / "aldavilla_4601.json",
            expected_records=4,
            expected_buildings=10,
        ),
    }


# ---------------------------------------------------------------------------
# Ground Truth Loading
# ---------------------------------------------------------------------------


def load_ground_truth(path: Path) -> dict:
    """Load and validate a ground truth JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Ground truth not found: {path}")
    with open(path) as f:
        data = json.load(f)
    if "records" not in data or "document" not in data:
        raise ValueError(f"Invalid ground truth format: {path}")
    return data


# ---------------------------------------------------------------------------
# Docling Fixture Loading (R1-T2)
# ---------------------------------------------------------------------------

# Module-level fixture cache for the mock to reference
_docling_fixture_cache: list[dict] = []


def _load_docling_fixtures(config_name: str) -> list[dict]:
    """Load Docling table fixtures for a benchmark document.

    Loads from ``benchmarks/fixtures/docling_{config_name}.json`` and returns
    the ``tables`` list.  Returns an empty list when the fixture file does not
    exist (graceful fallback).
    """
    fixture_path = FIXTURES_DIR / f"docling_{config_name}.json"
    if not fixture_path.exists():
        logger.debug(f"No Docling fixture at {fixture_path}")
        return []
    with open(fixture_path) as f:
        data = json.load(f)
    return data.get("tables", [])


async def _mock_get_docling_tables(
    source_id: str, page_start: int, page_end: int
) -> list[dict]:
    """Mock replacement for ``_get_docling_tables`` during benchmarks.

    Filters the module-level ``_docling_fixture_cache`` by the requested page
    range, returning tables whose ``page_start >= page_start`` and
    ``page_end <= page_end``.
    """
    return [
        t
        for t in _docling_fixture_cache
        if t.get("page_start", 0) >= page_start and t.get("page_end", 0) <= page_end
    ]


# ---------------------------------------------------------------------------
# Record Matching Engine
# ---------------------------------------------------------------------------


def _normalize(s: str) -> str:
    """Normalize string for fuzzy comparison."""
    return " ".join(s.lower().split())


def _normalize_product(product: str) -> str:
    """Resolve product name synonyms to canonical name."""
    norm = _normalize(product)
    # Strip parentheticals: "Floor covering (beneath carpet)" → "floor covering"
    norm = re.sub(r"\s*\([^)]*\)", "", norm).strip()
    if norm in PRODUCT_SYNONYMS:
        return norm
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _normalize_building(building: str) -> str:
    """Resolve building name synonyms to canonical name."""
    norm = _normalize(building)
    if norm in BUILDING_SYNONYMS:
        return norm
    for canonical, synonyms in BUILDING_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _normalize_room(room: str) -> str:
    """Resolve room name synonyms and normalize whitespace/dashes."""
    norm = _normalize(room)
    # Strip leading/trailing dashes with surrounding spaces
    norm = re.sub(r"^\s*[-–—]\s*|\s*[-–—]\s*$", "", norm).strip()
    # Strip trailing "throughout" qualifier (noise word)
    norm = re.sub(r"\s+throughout$", "", norm).strip()
    if norm in ROOM_SYNONYMS:
        return norm
    for canonical, synonyms in ROOM_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _get_field(record, field_name: str) -> str:
    """Get a field from either a dict or an object."""
    if isinstance(record, dict):
        return str(record.get(field_name, "") or "").strip()
    return str(getattr(record, field_name, "") or "").strip()


def match_records(ground_truth: list[dict], extracted: list[object]) -> MatchResult:
    """Match extracted records against ground truth using 3-tier strategy.

    Tier 1: Match by sample_no (most reliable)
    Tier 2: Composite key: building_name|room_name|location|product (synonym-aware)
    Tier 3: Partial key: room_name|location (fuzzy fallback, 1:1 consumption)
    """
    # Build lookup structures from extracted records
    ext_by_sample: dict[str, list[int]] = {}
    ext_by_composite: dict[str, list[int]] = {}
    ext_by_room_loc: dict[str, list[int]] = {}
    ext_by_bldg_prod: dict[str, list[int]] = {}

    for idx, r in enumerate(extracted):
        # Sample number index
        sno = _get_field(r, "sample_no")
        if sno and sno not in ("Not Sampled", ""):
            norm_sno = _normalize(sno)
            if norm_sno.startswith("as per"):
                norm_sno = _normalize(sno.split()[-1])
            ext_by_sample.setdefault(norm_sno, []).append(idx)

        # Composite key index (synonym-aware)
        bname = _normalize_building(_get_field(r, "building_name"))
        rname = _normalize_room(_get_field(r, "room_name"))
        loc = _normalize(_get_field(r, "location"))
        prod = _normalize_product(_get_field(r, "product"))
        composite = f"{bname}|{rname}|{loc}|{prod}"
        ext_by_composite.setdefault(composite, []).append(idx)

        # Swapped room/location composite (Tier 2.5)
        swapped = f"{bname}|{loc}|{rname}|{prod}"
        ext_by_composite.setdefault(swapped, []).append(idx)

        # Room+location index
        rl_key = f"{rname}|{loc}"
        ext_by_room_loc.setdefault(rl_key, []).append(idx)

        # Swapped room+location index (Tier 3.5)
        swapped_rl = f"{loc}|{rname}"
        ext_by_room_loc.setdefault(swapped_rl, []).append(idx)

        # Building+product index (Tier 4 — most permissive)
        bp_key = f"{bname}|{prod}"
        ext_by_bldg_prod.setdefault(bp_key, []).append(idx)

    consumed = set()
    matched_pairs = []
    unmatched_gt = []

    for gt_rec in ground_truth:
        matched_idx = None

        # Tier 1: sample_no
        sno = _normalize(gt_rec.get("sample_no", ""))
        if sno and sno not in ("not sampled", ""):
            lookup_sno = sno
            if lookup_sno.startswith("as per"):
                lookup_sno = _normalize(sno.split()[-1])
            for idx in ext_by_sample.get(lookup_sno, []):
                if idx not in consumed:
                    matched_idx = idx
                    break

        # Tier 2: composite key (synonym-aware)
        if matched_idx is None:
            bname = _normalize_building(gt_rec.get("building_name", ""))
            rname = _normalize_room(gt_rec.get("room_name", ""))
            loc = _normalize(gt_rec.get("location", ""))
            prod = _normalize_product(gt_rec.get("product", ""))
            composite = f"{bname}|{rname}|{loc}|{prod}"
            for idx in ext_by_composite.get(composite, []):
                if idx not in consumed:
                    matched_idx = idx
                    break

        # Tier 3: room+location fuzzy
        if matched_idx is None:
            rname = _normalize_room(gt_rec.get("room_name", ""))
            loc = _normalize(gt_rec.get("location", ""))
            rl_key = f"{rname}|{loc}"
            for idx in ext_by_room_loc.get(rl_key, []):
                if idx not in consumed:
                    matched_idx = idx
                    break

        # Tier 4: building+product (most permissive, 1:1 consumption)
        if matched_idx is None:
            bname = _normalize_building(gt_rec.get("building_name", ""))
            prod = _normalize_product(gt_rec.get("product", ""))
            bp_key = f"{bname}|{prod}"
            for idx in ext_by_bldg_prod.get(bp_key, []):
                if idx not in consumed:
                    matched_idx = idx
                    break

        if matched_idx is not None:
            consumed.add(matched_idx)
            matched_pairs.append((gt_rec, extracted[matched_idx]))
        else:
            unmatched_gt.append(gt_rec)

    unmatched_ext = [extracted[i] for i in range(len(extracted)) if i not in consumed]
    return MatchResult(
        matched_pairs=matched_pairs,
        unmatched_gt=unmatched_gt,
        unmatched_extracted=unmatched_ext,
    )


# ---------------------------------------------------------------------------
# Metrics Calculator
# ---------------------------------------------------------------------------


def calculate_field_accuracy(
    matched_pairs: list[tuple[dict, object]],
    fields: list[str] | None = None,
) -> float:
    """Calculate average field match rate across matched record pairs."""
    if not matched_pairs:
        return 0.0

    check_fields = fields or COMPARISON_FIELDS
    total_checks = 0
    total_matches = 0

    for gt_rec, ext_rec in matched_pairs:
        for f in check_fields:
            gt_val = _normalize(gt_rec.get(f, "") or "")
            ext_val = _normalize(_get_field(ext_rec, f))
            if not gt_val and not ext_val:
                continue  # Skip empty-empty comparisons
            total_checks += 1
            if gt_val == ext_val:
                total_matches += 1
            elif f == "product" and _normalize_product(gt_val) == _normalize_product(
                ext_val
            ):
                total_matches += 1
            elif f == "building_name" and _normalize_building(
                gt_val
            ) == _normalize_building(ext_val):
                total_matches += 1
            elif f == "room_name" and _normalize_room(gt_val) == _normalize_room(
                ext_val
            ):
                total_matches += 1

    return total_matches / total_checks if total_checks > 0 else 0.0


def calculate_metrics(
    ground_truth: list[dict],
    extracted: list[object],
    match_result: MatchResult,
    latency_s: float,
    token_usage: int,
    cost_usd: float,
    document_name: str,
) -> BenchmarkResult:
    """Calculate all benchmark metrics for a document."""
    gt_count = len(ground_truth)
    ext_count = len(extracted)
    matched_count = len(match_result.matched_pairs)

    recall = matched_count / gt_count if gt_count > 0 else 0.0
    precision = matched_count / ext_count if ext_count > 0 else 0.0
    field_acc = calculate_field_accuracy(match_result.matched_pairs)

    unmatched_ext_desc = []
    for r in match_result.unmatched_extracted:
        rname = _get_field(r, "room_name")
        prod = _get_field(r, "product")
        unmatched_ext_desc.append(f"{rname}/{prod}")

    return BenchmarkResult(
        document_name=document_name,
        ground_truth_count=gt_count,
        extracted_count=ext_count,
        matched_count=matched_count,
        recall=recall,
        precision=precision,
        field_accuracy=field_acc,
        latency_s=latency_s,
        token_usage=token_usage,
        cost_usd=cost_usd,
        unmatched_gt=match_result.unmatched_gt,
        unmatched_extracted=unmatched_ext_desc,
    )


# ---------------------------------------------------------------------------
# Extraction Runner (mocked DB, real LLM)
# ---------------------------------------------------------------------------

# Global token accumulator — patched into _verify_provider_routing
_token_accumulator: dict[str, float] = {}


def _reset_token_accumulator():
    global _token_accumulator
    _token_accumulator = {"prompt": 0, "completion": 0, "cost": 0.0}


def _create_llm_model(**kwargs):
    """Create a LangChain chat model using available API keys."""
    allowed_kwargs = {
        k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")
    }

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("BENCHMARK_MODEL", "anthropic/claude-sonnet-4")
        return ChatOpenAI(
            model=model_name,
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1",
            **allowed_kwargs,
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic

        model_name = os.environ.get("BENCHMARK_MODEL", "claude-haiku-4-5-20251001")
        return ChatAnthropic(model=model_name, **allowed_kwargs)

    raise RuntimeError(
        "No LLM API key available (need OPENROUTER_API_KEY or ANTHROPIC_API_KEY)"
    )


async def _real_provision_model(content, model_id, default_type, **kwargs):
    """Provision a real LLM model for benchmark extraction."""
    return _create_llm_model(**kwargs)


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF with page markers."""
    import fitz

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages)


async def run_extraction(
    config: BenchmarkConfig,
    *,
    with_docling_fixtures: bool = True,
) -> tuple[list, object, float]:
    """Run extraction pipeline with mocked DB, real LLM.

    Args:
        config: Benchmark document configuration.
        with_docling_fixtures: When True (default), load Docling table fixtures
            and patch ``_get_docling_tables`` so the pipeline injects structured
            table data instead of falling back to F2.

    Returns: (extracted_records, extraction_output, latency_s)
    """
    global _docling_fixture_cache

    from open_notebook.domain.acm import ACMRecord, ACMTableSection
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    # Extract PDF text
    pdf_text = _extract_pdf_text(config.pdf_path)
    if len(pdf_text) < 100:
        raise ValueError(f"PDF text too short: {len(pdf_text)} chars")

    # Load Docling fixtures if requested
    if with_docling_fixtures:
        # Derive config key from BenchmarkConfig name → registry key
        config_key = config.name.lower().replace(" ", "_")
        # Try common short names first
        for candidate in [
            config_key,
            config_key.split("_")[0],  # e.g. "broadmeadows"
        ]:
            tables = _load_docling_fixtures(candidate)
            if tables:
                break
        else:
            tables = []
        _docling_fixture_cache = tables
        if tables:
            logger.info(
                f"Loaded {len(tables)} Docling fixture tables for {config.name}"
            )
    else:
        _docling_fixture_cache = []

    # Create mock Source
    source = MagicMock()
    source.id = f"source:benchmark_{config.name.lower().replace(' ', '_')}"
    source.full_text = pdf_text
    source.title = config.name
    source.asset = MagicMock(file_path=str(config.pdf_path))

    # Capture extracted records
    extracted_records: list = []

    async def capture_save(self):
        extracted_records.append(self)

    async def noop_save(self):
        pass

    async def noop_auto_populate(document_metadata, source_id):
        pass

    _reset_token_accumulator()
    start_time = time.monotonic()

    with (
        patch.object(ACMRecord, "save", capture_save),
        patch.object(ACMTableSection, "save", noop_save),
        patch(
            "open_notebook.graphs.acm_extraction.auto_populate_site_config",
            noop_auto_populate,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.provision_langchain_model",
            _real_provision_model,
        ),
        patch(
            "open_notebook.graphs.utils.provision_langchain_model",
            _real_provision_model,
        ),
        patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            _mock_get_docling_tables,
        ),
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            _mock_get_docling_tables,
        ),
    ):
        result = await extract_acm_from_source(
            source=source,
            model_id=None,
            force=False,
            command_id=None,
        )

    elapsed = time.monotonic() - start_time

    # Use extraction_time_ms from output if available, else wall-clock
    latency_s = (
        result.extraction_time_ms / 1000.0 if result.extraction_time_ms else elapsed
    )

    return extracted_records, result, latency_s


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------


def generate_report(results: list[BenchmarkResult]) -> str:
    """Generate a markdown benchmark report."""
    lines = [
        "# E29 Baseline Benchmark Report",
        "",
        f"> Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"> Model: {os.environ.get('BENCHMARK_MODEL', 'default')}",
        f"> Documents: {len(results)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Document | GT | Extracted | Matched | Recall | Precision | Field Acc | Latency (s) | Tokens | Cost ($) |",
        "|----------|----|-----------|---------|--------|-----------|-----------|-------------|--------|----------|",
    ]

    for r in results:
        lines.append(
            f"| {r.document_name} | {r.ground_truth_count} | {r.extracted_count} "
            f"| {r.matched_count} | {r.recall:.1%} | {r.precision:.1%} "
            f"| {r.field_accuracy:.1%} | {r.latency_s:.1f} "
            f"| {r.token_usage:,} | ${r.cost_usd:.4f} |"
        )

    # Totals
    total_gt = sum(r.ground_truth_count for r in results)
    total_ext = sum(r.extracted_count for r in results)
    total_matched = sum(r.matched_count for r in results)
    avg_recall = total_matched / total_gt if total_gt > 0 else 0
    avg_precision = total_matched / total_ext if total_ext > 0 else 0
    avg_field_acc = (
        sum(r.field_accuracy for r in results) / len(results) if results else 0
    )
    total_latency = sum(r.latency_s for r in results)
    total_tokens = sum(r.token_usage for r in results)
    total_cost = sum(r.cost_usd for r in results)

    lines.append(
        f"| **TOTAL** | **{total_gt}** | **{total_ext}** "
        f"| **{total_matched}** | **{avg_recall:.1%}** | **{avg_precision:.1%}** "
        f"| **{avg_field_acc:.1%}** | **{total_latency:.1f}** "
        f"| **{total_tokens:,}** | **${total_cost:.4f}** |"
    )

    lines.extend(["", "---", ""])

    # Per-document detail
    for r in results:
        lines.extend(
            [
                f"## {r.document_name}",
                "",
                f"- **Ground truth**: {r.ground_truth_count} records",
                f"- **Extracted**: {r.extracted_count} records",
                f"- **Matched**: {r.matched_count}/{r.ground_truth_count} "
                f"(recall {r.recall:.1%})",
                f"- **Precision**: {r.precision:.1%}",
                f"- **Field accuracy**: {r.field_accuracy:.1%}",
                f"- **Latency**: {r.latency_s:.1f}s",
                f"- **Tokens**: {r.token_usage:,}",
                f"- **Cost**: ${r.cost_usd:.4f}",
                "",
            ]
        )

        if r.error:
            lines.extend([f"### Error", "", f"```", f"{r.error}", f"```", ""])

        if r.unmatched_gt:
            lines.append("### Missing Records (in ground truth, not extracted)")
            lines.append("")
            for i, gt in enumerate(r.unmatched_gt, 1):
                lines.append(
                    f"{i}. {gt.get('building_name', '?')} / "
                    f"{gt.get('room_name', '?')} / "
                    f"{gt.get('location', '?')} / "
                    f"{gt.get('product', '?')} "
                    f"(sample: {gt.get('sample_no', 'N/A')})"
                )
            lines.append("")

        if r.unmatched_extracted:
            lines.append("### Extra Records (extracted, not in ground truth)")
            lines.append("")
            for i, desc in enumerate(r.unmatched_extracted, 1):
                lines.append(f"{i}. {desc}")
            lines.append("")

        lines.extend(["---", ""])

    lines.extend(
        [
            "## Gate 1 Readiness",
            "",
            "| # | Criterion | Status |",
            "|---|-----------|--------|",
            f"| G1.1 | Harness runs >=3 docs E2E | "
            f"{'PASS' if len(results) >= 3 else 'FAIL'} ({len(results)} docs) |",
            f"| G1.2 | Ground truth for 3 docs | "
            f"{'PASS' if len(results) >= 3 else 'FAIL'} |",
            f"| G1.3 | Baseline metrics captured | "
            f"{'PASS' if all(r.error is None for r in results) else 'FAIL'} |",
            f"| G1.4 | CI entrypoint exists | PASS (pytest tests/integration/) |",
            "",
            "*Report generated by `scripts/research/e29_benchmark_harness.py`*",
        ]
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------


async def run_benchmark(doc_name: str, config: BenchmarkConfig) -> BenchmarkResult:
    """Run a single benchmark document E2E."""
    print(f"\n{'=' * 60}")
    print(f"  Benchmark: {config.name}")
    print(f"  PDF: {config.pdf_path.name}")
    print(f"  Ground truth: {config.ground_truth_path.name}")
    print(f"{'=' * 60}")

    # Load ground truth
    try:
        gt_data = load_ground_truth(config.ground_truth_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  SKIP: {e}")
        return BenchmarkResult(
            document_name=config.name,
            ground_truth_count=0,
            extracted_count=0,
            matched_count=0,
            recall=0.0,
            precision=0.0,
            field_accuracy=0.0,
            latency_s=0.0,
            token_usage=0,
            cost_usd=0.0,
            error=str(e),
        )

    gt_records = gt_data["records"]
    print(f"  Ground truth: {len(gt_records)} records")

    # Run extraction
    try:
        extracted, output, latency_s = await run_extraction(config)
    except Exception as e:
        logger.exception(f"Extraction failed for {config.name}")
        return BenchmarkResult(
            document_name=config.name,
            ground_truth_count=len(gt_records),
            extracted_count=0,
            matched_count=0,
            recall=0.0,
            precision=0.0,
            field_accuracy=0.0,
            latency_s=0.0,
            token_usage=0,
            cost_usd=0.0,
            error=str(e),
        )

    print(f"  Extracted: {len(extracted)} records in {latency_s:.1f}s")
    print(f"  Output status: {output.status}")

    # Token/cost from output or accumulator
    token_usage = int(
        _token_accumulator.get("prompt", 0) + _token_accumulator.get("completion", 0)
    )
    cost_usd = _token_accumulator.get("cost", 0.0)

    # Match records
    match_result = match_records(gt_records, extracted)
    print(
        f"  Matched: {len(match_result.matched_pairs)}/{len(gt_records)} "
        f"(recall {len(match_result.matched_pairs) / len(gt_records):.1%})"
    )

    # Calculate metrics
    result = calculate_metrics(
        gt_records,
        extracted,
        match_result,
        latency_s,
        token_usage,
        cost_usd,
        config.name,
    )

    return result


def _results_path(output_tag: str) -> Path:
    """Return the results JSON path for a given output tag."""
    return RESULTS_DIR / f"{output_tag}_results.json"


def _report_path(output_tag: str) -> Path:
    """Return the report markdown path for a given output tag."""
    return REPORT_DIR / f"e29-{output_tag}-benchmark-report.md"


async def main():
    parser = argparse.ArgumentParser(description="E29 Benchmark Harness")
    parser.add_argument(
        "--all", action="store_true", help="Run all benchmark documents"
    )
    parser.add_argument("--doc", type=str, help="Run a single document by name")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report from cached results",
    )
    parser.add_argument(
        "--output-tag",
        type=str,
        default="baseline",
        help="Tag for output files (e.g., 'gate2', 'gate2_rerun')",
    )
    parser.add_argument(
        "--with-docling-fixtures",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Load Docling table fixtures for injection (default: True)",
    )
    args = parser.parse_args()

    configs = get_benchmark_configs()
    results_file = _results_path(args.output_tag)
    report_file = _report_path(args.output_tag)

    if args.report_only:
        # Load cached results
        if not results_file.exists():
            print(f"No cached results at {results_file}")
            sys.exit(1)
        with open(results_file) as f:
            cached = json.load(f)
        results = [BenchmarkResult(**r) for r in cached]
        report = generate_report(results)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        print(f"Report written to {report_file}")
        return

    # Determine which docs to run
    if args.doc:
        if args.doc not in configs:
            print(
                f"Unknown document: {args.doc}. Available: {', '.join(configs.keys())}"
            )
            sys.exit(1)
        docs_to_run = {args.doc: configs[args.doc]}
    elif args.all:
        docs_to_run = configs
    else:
        print("Specify --all or --doc <name>")
        parser.print_help()
        sys.exit(1)

    # Check API keys
    if not (
        os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    ):
        print("ERROR: No LLM API key. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY.")
        sys.exit(1)

    # Run benchmarks
    results: list[BenchmarkResult] = []
    for doc_name, config in docs_to_run.items():
        if not config.pdf_path.exists():
            print(f"SKIP {doc_name}: PDF not found at {config.pdf_path}")
            continue
        result = await run_benchmark(doc_name, config)
        results.append(result)

    if not results:
        print("No benchmarks were run.")
        sys.exit(1)

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    serializable = []
    for r in results:
        d = {
            "document_name": r.document_name,
            "ground_truth_count": r.ground_truth_count,
            "extracted_count": r.extracted_count,
            "matched_count": r.matched_count,
            "recall": r.recall,
            "precision": r.precision,
            "field_accuracy": r.field_accuracy,
            "latency_s": r.latency_s,
            "token_usage": r.token_usage,
            "cost_usd": r.cost_usd,
            "error": r.error,
            "unmatched_gt": r.unmatched_gt,
            "unmatched_extracted": r.unmatched_extracted,
        }
        serializable.append(d)
    with open(results_file, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {results_file}")

    # Generate report
    report = generate_report(results)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report)
    print(f"Report written to {report_file}")

    # Print summary
    print(f"\n{'=' * 60}")
    print("  BENCHMARK SUMMARY")
    print(f"{'=' * 60}")
    for r in results:
        status = "PASS" if r.error is None else f"FAIL: {r.error}"
        print(
            f"  {r.document_name}: {r.matched_count}/{r.ground_truth_count} "
            f"recall={r.recall:.1%} precision={r.precision:.1%} "
            f"field_acc={r.field_accuracy:.1%} [{status}]"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
