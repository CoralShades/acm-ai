"""E26-S4 Accuracy Validation — Decision Gate

Full pipeline: PyMuPDF text + Docling DataFrames (from DB) → LLM extraction
→ Ground truth cross-reference.

Uses Docling tables pre-stored in DB from E26-S2 validation (source:e26_s2_test).
These tables were verified to match E25 spike results exactly (8 tables, 30 register
rows, Record #9 present).

Usage:
    cd $CLAUDE_PROJECT_DIR
    uv run python scripts/research/e26_s4_accuracy_validation.py

Requirements:
    - SurrealDB running (port 8000)
    - OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .env
    - Docling tables stored in DB for source:e26_s2_test (from S2 validation)
"""

import asyncio
import csv
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# ── Constants ──────────────────────────────────────────────────────────────

SAMPLE_PDF = PROJECT_ROOT / "docs/samplePDF/Clutch_Broadmeadows.pdf"
SAMPLE_CSV = PROJECT_ROOT / "docs/samplePDF/Clutch_Broadmeadows.csv"
SOURCE_ID = "source:e26_s2_test"

OPENROUTER_DEFAULT_MODEL = "anthropic/claude-sonnet-4"
ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Product synonym mapping (from E2E test)
PRODUCT_SYNONYMS = {
    "flange joints": ["flange mastic", "mastic", "flange mastic (grey)"],
    "fuse cartridge": ["fuses", "fuse"],
    "internal lining": ["lining", "wall lining", "internal wall lining"],
}


# ── Helpers ────────────────────────────────────────────────────────────────


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF with page markers."""
    import fitz

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages)


def _load_expected_records():
    """Load ground truth from CSV."""
    records = []
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_no = row["NATA Endorsed Sample number (if available)"].strip()
            records.append(
                {
                    "room": row["Room or Area"].strip(),
                    "location": row["Location in Room"].strip(),
                    "item": row["Specific Item/ACM Name"].strip(),
                    "sample_no": sample_no,
                    "result": row["Sample Result"].strip(),
                    "level": row["Level"].strip(),
                    "internal_external": row["Internal / External"].strip(),
                    # Categorize for reporting
                    "category": _categorize_record(sample_no, row["Sample Result"].strip()),
                }
            )
    return records


def _categorize_record(sample_no: str, result: str) -> str:
    """Categorize a record for per-category reporting."""
    if sample_no.upper().startswith("AS PER"):
        return "as_per"
    if sample_no == "Not Sampled":
        return "not_sampled"
    return "nata_sampled"


def _normalize(s: str) -> str:
    return " ".join(s.lower().split())


def _normalize_product(product: str) -> str:
    norm = _normalize(product)
    if norm in PRODUCT_SYNONYMS:
        return norm
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _record_key(room: str, location: str, item: str) -> str:
    return f"{_normalize(room)}|{_normalize(location)}|{_normalize(item)}"


def _room_location_key(room: str, location: str) -> str:
    return f"{_normalize(room)}|{_normalize(location)}"


def _match_extracted_to_expected(extracted_records, expected_records):
    """Match extracted records to expected. Returns (found_indices, missing)."""
    extracted_sample_nos = set()
    extracted_keys = set()
    extracted_synonym_keys = set()
    extracted_room_loc_keys: dict[str, list[int]] = {}

    for idx, r in enumerate(extracted_records):
        sno = (r.sample_no or "").strip()
        if sno and sno not in ("Not Sampled", ""):
            if sno.upper().startswith("AS PER"):
                base = sno.split()[-1].strip()
                extracted_sample_nos.add(_normalize(base))
            else:
                extracted_sample_nos.add(_normalize(sno))

        product = r.product or r.material_description or ""
        key = _record_key(r.room_name or "", r.location or "", product)
        extracted_keys.add(key)

        syn_key = f"{_normalize(r.room_name or '')}|{_normalize(r.location or '')}|{_normalize_product(product)}"
        extracted_synonym_keys.add(syn_key)

        rl_key = _room_location_key(r.room_name or "", r.location or "")
        extracted_room_loc_keys.setdefault(rl_key, []).append(idx)

    found_indices = set()
    missing = []
    consumed_extracted = set()

    for i, exp in enumerate(expected_records):
        sno = exp["sample_no"].strip()
        matched = False

        if sno and sno not in ("Not Sampled", ""):
            if sno.upper().startswith("AS PER"):
                base = sno.split()[-1].strip()
                if _normalize(base) in extracted_sample_nos:
                    matched = True
            else:
                if _normalize(sno) in extracted_sample_nos:
                    matched = True

        if not matched:
            key = _record_key(exp["room"], exp["location"], exp["item"])
            if key in extracted_keys:
                matched = True

        if not matched:
            syn_key = f"{_normalize(exp['room'])}|{_normalize(exp['location'])}|{_normalize_product(exp['item'])}"
            if syn_key in extracted_synonym_keys:
                matched = True

        if not matched:
            rl_key = _room_location_key(exp["room"], exp["location"])
            if rl_key in extracted_room_loc_keys:
                for ext_idx in extracted_room_loc_keys[rl_key]:
                    if ext_idx not in consumed_extracted:
                        consumed_extracted.add(ext_idx)
                        matched = True
                        break

        if matched:
            found_indices.add(i)
        else:
            missing.append(exp)

    return found_indices, missing


def _create_llm_model(**kwargs):
    """Create LLM model using available API keys."""
    allowed_kwargs = {
        k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")
    }

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("TEST_MODEL", OPENROUTER_DEFAULT_MODEL)
        return ChatOpenAI(
            model=model_name,
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1",
            **allowed_kwargs,
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic

        model_name = os.environ.get("TEST_MODEL", ANTHROPIC_DEFAULT_MODEL)
        return ChatAnthropic(model=model_name, **allowed_kwargs)

    raise RuntimeError("No LLM API key (need OPENROUTER_API_KEY or ANTHROPIC_API_KEY)")


def _check_record_9(extracted_records) -> bool:
    """Check if Record #9 (Switch Room / Battery Charger / Fuse cartridge) was captured."""
    for r in extracted_records:
        room = _normalize(r.room_name or "")
        location = _normalize(r.location or "")
        product = _normalize(r.product or r.material_description or "")
        if (
            "switch room" in room
            and ("battery" in location or "battery" in product)
        ):
            return True
        if (
            "switch room" in room
            and ("fuse" in location or "fuse" in product)
            and "switchboard" not in location
        ):
            return True
    return False


def _check_specific_record(extracted_records, room_substr: str, loc_substr: str) -> bool:
    """Check if a specific record was captured by room+location substring match."""
    for r in extracted_records:
        room = _normalize(r.room_name or "")
        loc = _normalize(r.location or "")
        if room_substr.lower() in room and loc_substr.lower() in loc:
            return True
    return False


# ── Main Validation ───────────────────────────────────────────────────────


async def run_validation():
    from open_notebook.domain.acm import ACMRecord, ACMTableSection
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    print("=" * 70)
    print("E26-S4 ACCURACY VALIDATION — DECISION GATE")
    print("=" * 70)

    # 1. Pre-flight
    print("\n[1/5] Pre-flight checks...")
    assert SAMPLE_PDF.exists(), f"PDF not found: {SAMPLE_PDF}"
    assert SAMPLE_CSV.exists(), f"CSV not found: {SAMPLE_CSV}"
    assert os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
        "ANTHROPIC_API_KEY"
    ), "No API key"

    flag = os.environ.get("DOCLING_DIRECT_TABLE_EXTRACTION", "false")
    print(f"  DOCLING_DIRECT_TABLE_EXTRACTION = {flag}")
    model_name = os.environ.get("TEST_MODEL", OPENROUTER_DEFAULT_MODEL)
    print(f"  Model: {model_name}")
    print(f"  Source ID: {SOURCE_ID}")

    # 2. Load ground truth
    print("\n[2/5] Loading ground truth...")
    expected = _load_expected_records()
    print(f"  Ground truth: {len(expected)} records")

    nata_count = sum(1 for r in expected if r["category"] == "nata_sampled")
    as_per_count = sum(1 for r in expected if r["category"] == "as_per")
    not_sampled_count = sum(1 for r in expected if r["category"] == "not_sampled")
    print(f"  NATA-sampled: {nata_count}, As Per: {as_per_count}, Not Sampled: {not_sampled_count}")

    # 3. Extract PDF text
    print("\n[3/5] Extracting PDF text (PyMuPDF)...")
    pdf_text = _extract_pdf_text(SAMPLE_PDF)
    print(f"  PDF text: {len(pdf_text)} chars")

    # 4. Run extraction
    print("\n[4/5] Running full extraction pipeline (LLM + Docling context)...")
    print(f"  This will take ~3-5 minutes (LLM extraction)...")

    source = MagicMock()
    source.id = SOURCE_ID
    source.full_text = pdf_text
    source.title = "Broadmeadows Police Station - Division 5 Asbestos Assessment"
    source.asset = MagicMock(file_path=str(SAMPLE_PDF))

    extracted_records: list = []

    async def capture_record_save(self):
        extracted_records.append(self)

    async def noop_section_save(self):
        pass

    async def noop_auto_populate(document_metadata, source_id):
        pass

    async def real_provision_model(content, model_id, default_type, **kwargs):
        return _create_llm_model(**kwargs)

    start_time = time.time()

    with (
        patch.object(ACMRecord, "save", capture_record_save),
        patch.object(ACMTableSection, "save", noop_section_save),
        patch(
            "open_notebook.graphs.acm_extraction.auto_populate_site_config",
            noop_auto_populate,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.provision_langchain_model",
            real_provision_model,
        ),
        patch(
            "open_notebook.graphs.utils.provision_langchain_model",
            real_provision_model,
        ),
    ):
        result = await extract_acm_from_source(
            source=source,
            model_id=None,
            force=False,
            command_id=None,
        )

    elapsed = time.time() - start_time

    print(f"  Extraction status: {result.status}")
    print(f"  Records extracted: {result.total_records}")
    print(f"  Records captured: {len(extracted_records)}")
    print(f"  Duration: {elapsed:.1f}s")

    if result.error:
        print(f"\n  ERROR: {result.error}")
        return

    # 5. Cross-reference
    print("\n[5/5] Cross-referencing against ground truth...")
    found_indices, missing = _match_extracted_to_expected(extracted_records, expected)

    total_matched = len(found_indices)
    total_expected = len(expected)
    pct = 100 * total_matched / total_expected

    # Per-category breakdown
    nata_matched = sum(1 for i in found_indices if expected[i]["category"] == "nata_sampled")
    as_per_matched = sum(1 for i in found_indices if expected[i]["category"] == "as_per")
    not_sampled_matched = sum(1 for i in found_indices if expected[i]["category"] == "not_sampled")

    # Specific record checks
    record_9_found = _check_record_9(extracted_records)
    record_30_found = _check_specific_record(extracted_records, "lift foyer", "lift")
    record_31_found = _check_specific_record(extracted_records, "main foyer", "disabled toilet") or \
                      _check_specific_record(extracted_records, "foyer", "toilet")

    # Count Docling tables injected (from orchestrator stats)
    orch_stats = result.orchestrator_stats or {}
    docling_tables_injected = "unknown"
    if isinstance(orch_stats, dict):
        # Check building stats for Docling injection info
        for key, val in orch_stats.items():
            if "docling" in str(val).lower():
                docling_tables_injected = str(val)

    # ── Report ──────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    print(f"\n  Total: {total_matched}/{total_expected} ({pct:.1f}%)")
    print(f"  NATA-sampled: {nata_matched}/{nata_count}")
    print(f"  'As Per' (Same as): {as_per_matched}/{as_per_count}")
    print(f"  'Not Sampled': {not_sampled_matched}/{not_sampled_count}")
    print(f"  Record #9 (Battery Charger): {'FOUND' if record_9_found else 'MISSING'}")
    print(f"  Record #30 (Lift Foyer): {'FOUND' if record_30_found else 'MISSING'}")
    print(f"  Record #31 (Disabled Toilet): {'FOUND' if record_31_found else 'MISSING'}")
    print(f"  Duration: {elapsed:.1f}s")

    if missing:
        print(f"\n  MISSING RECORDS ({len(missing)}):")
        for i, rec in enumerate(missing, 1):
            print(
                f"    {i}. [{rec['level']}] {rec['room']} / {rec['location']} / "
                f"{rec['item']} (sample: {rec['sample_no']}, category: {rec['category']})"
            )

    print(f"\n  EXTRACTED RECORDS ({len(extracted_records)}):")
    for i, r in enumerate(extracted_records, 1):
        print(
            f"    {i}. {r.room_name or '?'} / {r.location or '?'} / "
            f"{r.product or r.material_description or '?'} "
            f"(sample: {r.sample_no or 'N/A'})"
        )

    # ── Decision Gate ──────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("DECISION GATE")
    print("=" * 70)

    if total_matched >= 30 and total_matched > 28:
        decision = "PROMOTE"
        print(f"\n  Result: PROMOTE")
        print(f"  {total_matched}/31 >= 30/31 threshold")
    elif total_matched >= 28:
        decision = "INVESTIGATE"
        print(f"\n  Result: INVESTIGATE")
        print(f"  {total_matched}/31 — above baseline but below 30/31 target")
    else:
        decision = "ROLLBACK"
        print(f"\n  Result: ROLLBACK")
        print(f"  {total_matched}/31 — regression from E23 baseline (28/31)")

    # Save results to JSON
    results = {
        "date": time.strftime("%Y-%m-%d"),
        "model": model_name,
        "flag": flag,
        "source_id": SOURCE_ID,
        "duration_s": round(elapsed, 1),
        "total_matched": total_matched,
        "total_expected": total_expected,
        "pct": round(pct, 1),
        "nata_sampled": {"matched": nata_matched, "total": nata_count},
        "as_per": {"matched": as_per_matched, "total": as_per_count},
        "not_sampled": {"matched": not_sampled_matched, "total": not_sampled_count},
        "record_9_found": record_9_found,
        "record_30_found": record_30_found,
        "record_31_found": record_31_found,
        "decision": decision,
        "missing": [
            {
                "level": r["level"],
                "room": r["room"],
                "location": r["location"],
                "item": r["item"],
                "sample_no": r["sample_no"],
                "category": r["category"],
            }
            for r in missing
        ],
    }

    output_dir = PROJECT_ROOT / "research-output" / "e26-s4"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "validation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {output_file}")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_validation())
    if results:
        sys.exit(0 if results["decision"] in ("PROMOTE", "INVESTIGATE") else 1)
    else:
        sys.exit(1)
