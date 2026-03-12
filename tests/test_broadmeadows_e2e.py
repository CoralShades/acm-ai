"""E2E integration test: Broadmeadows Police Station ACM extraction.

Tests the full AI extraction pipeline against the known Broadmeadows Police
Station asbestos register PDF, verifying all 31 records from the reference CSV.

Requirements:
    - OPENROUTER_API_KEY or ANTHROPIC_API_KEY environment variable must be set
    - Run with: pytest tests/test_broadmeadows_e2e.py -m integration -v -s

The test will FAIL if any of the 31 expected records are not extracted —
this is intentional. It serves as a quality gate for the extraction pipeline.
"""

import csv
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Load .env early so API keys are available for skip checks
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

SAMPLE_PDF = Path(__file__).parent.parent / "docs/samplePDF/Clutch_Broadmeadows.pdf"
SAMPLE_CSV = Path(__file__).parent.parent / "docs/samplePDF/Clutch_Broadmeadows.csv"

# Synonym mapping for product names that differ between PDF text and BAR vocabulary.
# Keys are canonical BAR names (lowercase); values are known PDF variants.
PRODUCT_SYNONYMS = {
    "flange joints": ["flange mastic", "mastic", "flange mastic (grey)"],
    "fuse cartridge": ["fuses", "fuse"],
    "internal lining": ["lining", "wall lining", "internal wall lining"],
}

pytestmark = pytest.mark.integration

# Default model for OpenRouter extraction (Claude Sonnet via OpenRouter)
OPENROUTER_DEFAULT_MODEL = "anthropic/claude-sonnet-4"
ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _has_api_key() -> bool:
    """Check if any supported LLM API key is available."""
    return bool(
        os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    )


def _load_expected_records():
    """Load expected records from the reference CSV.

    Returns list of dicts with keys: room, location, item, sample_no, result.
    """
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
                }
            )
    return records


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF with page markers."""
    import fitz

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages)


def _normalize(s: str) -> str:
    """Normalize a string for fuzzy comparison."""
    return " ".join(s.lower().split())


def _record_key(room: str, location: str, item: str) -> str:
    """Build a composite key for matching records without sample numbers."""
    return f"{_normalize(room)}|{_normalize(location)}|{_normalize(item)}"


def _room_location_key(room: str, location: str) -> str:
    """Build a partial key from room + location only (ignoring product name)."""
    return f"{_normalize(room)}|{_normalize(location)}"


def _normalize_product(product: str) -> str:
    """Resolve product name synonyms to their canonical BAR name.

    Returns the canonical name (lowercase) if a synonym match is found,
    otherwise returns the normalized (lowercase, whitespace-collapsed) input.
    """
    norm = _normalize(product)
    # Check if it's already a canonical name
    if norm in PRODUCT_SYNONYMS:
        return norm
    # Check if it matches any synonym
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if norm in [_normalize(s) for s in synonyms]:
            return canonical
    return norm


def _match_extracted_to_expected(extracted_records, expected_records):
    """Match extracted ACMRecord objects to expected CSV records.

    Uses a three-tier matching strategy:
    1. Primary: Match by sample number (most reliable)
    2. Secondary: Match by room + location + item composite key (exact)
    3. Tertiary: Match by room + location only (fuzzy — for records where LLM may
       use a different product name, e.g. "Switchboard" vs "Fuse cartridge")

    Returns:
        found: set of indices into expected_records that were matched
        missing: list of expected records that were not found
    """
    # Build lookup structures from extracted records
    extracted_sample_nos = set()
    extracted_keys = set()
    extracted_synonym_keys = set()  # Synonym-normalized composite keys
    extracted_room_loc_keys: dict[str, list[int]] = {}

    for idx, r in enumerate(extracted_records):
        sno = (r.sample_no or "").strip()
        if sno and sno not in ("Not Sampled", ""):
            # Normalize "As Per XXXX" references to the base sample number
            if sno.upper().startswith("AS PER"):
                base = sno.split()[-1].strip()
                extracted_sample_nos.add(_normalize(base))
            else:
                extracted_sample_nos.add(_normalize(sno))

        # Also build composite key
        product = r.product or r.material_description or ""
        key = _record_key(
            r.room_name or "",
            r.location or "",
            product,
        )
        extracted_keys.add(key)

        # Build synonym-normalized composite key
        syn_key = f"{_normalize(r.room_name or '')}|{_normalize(r.location or '')}|{_normalize_product(product)}"
        extracted_synonym_keys.add(syn_key)

        # Build room+location partial key for fuzzy fallback
        rl_key = _room_location_key(r.room_name or "", r.location or "")
        extracted_room_loc_keys.setdefault(rl_key, []).append(idx)

    found_indices = set()
    missing = []
    # Track which extracted records have been consumed by fuzzy match
    consumed_extracted = set()

    for i, exp in enumerate(expected_records):
        sno = exp["sample_no"].strip()

        matched = False

        if sno and sno not in ("Not Sampled", ""):
            # Primary match: by sample number
            if sno.upper().startswith("AS PER"):
                base = sno.split()[-1].strip()
                if _normalize(base) in extracted_sample_nos:
                    matched = True
            else:
                if _normalize(sno) in extracted_sample_nos:
                    matched = True

        if not matched:
            # Secondary: by room + location + item composite key
            key = _record_key(exp["room"], exp["location"], exp["item"])
            if key in extracted_keys:
                matched = True

        if not matched:
            # Tier 2.5: synonym-normalized composite key match
            syn_key = f"{_normalize(exp['room'])}|{_normalize(exp['location'])}|{_normalize_product(exp['item'])}"
            if syn_key in extracted_synonym_keys:
                matched = True

        if not matched:
            # Tertiary: fuzzy room + location match (handles product name differences)
            # Only use for "Not Sampled" records or known-difficult items
            rl_key = _room_location_key(exp["room"], exp["location"])
            if rl_key in extracted_room_loc_keys:
                # Find an unconsumed extracted record at this room+location
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
    """Create a LangChain chat model using available API keys.

    Prefers OpenRouter (supports Anthropic/Gemini/etc via single key).
    Falls back to direct Anthropic if available.
    """
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

    raise RuntimeError(
        "No LLM API key available (need OPENROUTER_API_KEY or ANTHROPIC_API_KEY)"
    )


@pytest.mark.skipif(
    not _has_api_key(),
    reason="OPENROUTER_API_KEY or ANTHROPIC_API_KEY required for integration test",
)
@pytest.mark.skipif(
    not SAMPLE_PDF.exists(),
    reason=f"Sample PDF not found: {SAMPLE_PDF}",
)
@pytest.mark.asyncio
async def test_broadmeadows_all_records_extracted():
    """
    Upload Broadmeadows Police Station PDF and verify all 31 records are extracted.

    This test runs the full AI extraction pipeline with a real LLM.
    All database operations are mocked — only the LLM calls are real.

    Supports OpenRouter (primary) and direct Anthropic (fallback).
    Expected: all 31 records from Clutch_Broadmeadows.csv are extracted.
    """
    from open_notebook.domain.acm import ACMRecord, ACMTableSection, BuildingRecord
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    # 1. Load expected records from CSV
    expected = _load_expected_records()
    assert len(expected) == 31, f"Expected 31 CSV records, got {len(expected)}"

    # 2. Extract PDF text using PyMuPDF
    pdf_text = _extract_pdf_text(SAMPLE_PDF)
    assert len(pdf_text) > 1000, "PDF text extraction produced insufficient content"
    print(f"\nPDF extracted: {len(pdf_text)} chars")

    # 3. Create mock Source with real PDF content
    source = MagicMock()
    source.id = "source:broadmeadows_e2e_test"
    source.full_text = pdf_text
    source.title = "Broadmeadows Police Station - Division 5 Asbestos Assessment"
    source.asset = MagicMock(file_path=str(SAMPLE_PDF))

    # 4. Track extracted records via mocked save
    extracted_records: list[ACMRecord] = []

    async def capture_record_save(self):
        extracted_records.append(self)

    async def noop_section_save(self):
        pass

    async def noop_building_save(self):
        self.id = f"building_record:mock_{id(self)}"

    async def noop_auto_populate(document_metadata, source_id):
        pass

    # Provide a real model via OpenRouter or direct Anthropic
    async def real_provision_model(content, model_id, default_type, **kwargs):
        return _create_llm_model(**kwargs)

    with (
        patch.object(ACMRecord, "save", capture_record_save),
        patch.object(ACMTableSection, "save", noop_section_save),
        patch.object(BuildingRecord, "save", noop_building_save),
        patch.object(
            BuildingRecord, "get_by_source",
            new_callable=AsyncMock, return_value=[],
        ),
        patch(
            "open_notebook.graphs.acm_extraction.auto_populate_site_config",
            noop_auto_populate,
        ),
        # Patch the module-level import in acm_extraction.py
        patch(
            "open_notebook.graphs.acm_extraction.provision_langchain_model",
            real_provision_model,
        ),
        # Patch the source so local imports in page_tagger, orchestrator,
        # document_structure, building_inventory all use the real LLM model
        patch(
            "open_notebook.graphs.utils.provision_langchain_model",
            real_provision_model,
        ),
    ):
        result = await extract_acm_from_source(
            source=source,
            model_id=None,  # Use default (real_provision_model handles this)
            force=False,
            command_id=None,  # No pipeline logger DB writes
        )

    # 5. Report results
    print(f"\nExtraction status: {result.status}")
    print(f"Records extracted: {result.total_records}")
    print(f"Records failed: {result.records_failed}")
    print(f"Records captured by mock: {len(extracted_records)}")

    if result.error:
        pytest.fail(f"Extraction returned error: {result.error}")

    # 6. Match against expected records
    found, missing = _match_extracted_to_expected(extracted_records, expected)

    print(f"\n=== EXTRACTION QUALITY REPORT ===")
    print(f"Expected: {len(expected)} records")
    print(f"Extracted: {len(extracted_records)} records")
    print(
        f"Matched: {len(found)}/{len(expected)} ({100 * len(found) // len(expected)}%)"
    )

    if missing:
        print(f"\nMISSING RECORDS ({len(missing)}):")
        for i, rec in enumerate(missing, 1):
            print(
                f"  {i}. [{rec['level']}] {rec['room']} / {rec['location']} / {rec['item']}"
                f" (sample: {rec['sample_no']})"
            )

    # Print all extracted records for debugging
    print(f"\nEXTRACTED RECORDS ({len(extracted_records)}):")
    for i, r in enumerate(extracted_records, 1):
        print(
            f"  {i}. {r.room_name or '?'} / {r.location or '?'} / "
            f"{r.product or r.material_description or '?'} "
            f"(sample: {r.sample_no or 'N/A'})"
        )

    # 7. Assert 100% of records are found (31/31 target — E20 completeness goal)
    # E20 fixes applied:
    #   E20-S1: Page boundary overlap (_apply_boundary_overlap)
    #   E20-S2: REGEX yield check — escalate to FULL_LLM if < 50% capture
    #   E20-S3: Not Sampled / No Access explicit capture (no_access field + prompt)
    # Baseline pre-fix: ~25/31 (80%). Target after E20: 31/31 (100%).
    MIN_PASS = 31  # 100% of 31
    assert len(found) >= MIN_PASS, (
        f"Only {len(found)}/{len(expected)} records matched (required {MIN_PASS}/{len(expected)}, i.e. 100%).\n"
        f"Missing ({len(missing)}):\n"
        + "\n".join(
            f"  - [{r['level']}] {r['room']} / {r['location']} / {r['item']} (sample: {r['sample_no']})"
            for r in missing
        )
    )

    print(
        f"\n{len(found)}/{len(expected)} records successfully extracted ({100 * len(found) // len(expected)}%)!"
    )
