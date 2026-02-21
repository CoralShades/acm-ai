"""E2E integration test: Broadmeadows Police Station ACM extraction.

Tests the full AI extraction pipeline against the known Broadmeadows Police
Station asbestos register PDF, verifying all 31 records from the reference CSV.

Requirements:
    - ANTHROPIC_API_KEY environment variable must be set
    - Run with: pytest tests/test_broadmeadows_e2e.py -m integration -v -s

The test will FAIL if any of the 31 expected records are not extracted —
this is intentional. It serves as a quality gate for the extraction pipeline.
"""

import csv
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

SAMPLE_PDF = Path(__file__).parent.parent / "docs/samplePDF/Clutch_Broadmeadows.pdf"
SAMPLE_CSV = Path(__file__).parent.parent / "docs/samplePDF/Clutch_Broadmeadows.csv"

pytestmark = pytest.mark.integration


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


def _match_extracted_to_expected(extracted_records, expected_records):
    """Match extracted ACMRecord objects to expected CSV records.

    Returns:
        found: set of indices into expected_records that were matched
        missing: list of expected records that were not found
    """
    # Build lookup structures from extracted records
    extracted_sample_nos = set()
    extracted_keys = set()

    for r in extracted_records:
        sno = (r.sample_no or "").strip()
        if sno and sno not in ("Not Sampled", ""):
            # Normalize "As Per XXXX" references to the base sample number
            if sno.upper().startswith("AS PER"):
                base = sno.split()[-1].strip()
                extracted_sample_nos.add(_normalize(base))
            else:
                extracted_sample_nos.add(_normalize(sno))

        # Also build composite key
        key = _record_key(
            r.room_name or "",
            r.location or "",
            r.product or r.material_description or "",
        )
        extracted_keys.add(key)

    found_indices = set()
    missing = []

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
            # Fallback: by room + location + item composite key
            key = _record_key(exp["room"], exp["location"], exp["item"])
            if key in extracted_keys:
                matched = True

        if matched:
            found_indices.add(i)
        else:
            missing.append(exp)

    return found_indices, missing


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY required for integration test",
)
@pytest.mark.skipif(
    not SAMPLE_PDF.exists(),
    reason=f"Sample PDF not found: {SAMPLE_PDF}",
)
@pytest.mark.asyncio
async def test_broadmeadows_all_records_extracted():
    """
    Upload Broadmeadows Police Station PDF and verify all 31 records are extracted.

    This test runs the full AI extraction pipeline with a real LLM (Anthropic Claude).
    All database operations are mocked — only the LLM calls are real.

    Expected: all 31 records from Clutch_Broadmeadows.csv are extracted.
    """
    from langchain_anthropic import ChatAnthropic

    from open_notebook.domain.acm import ACMRecord, ACMTableSection
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    # 1. Load expected records from CSV
    expected = _load_expected_records()
    assert len(expected) == 31, f"Expected 31 CSV records, got {len(expected)}"

    # 2. Extract PDF text using PyMuPDF
    pdf_text = _extract_pdf_text(SAMPLE_PDF)
    assert len(pdf_text) > 1000, "PDF text extraction produced insufficient content"
    print(f"\nPDF extracted: {len(pdf_text)} chars")

    # 3. Create mock Source with real PDF content
    from unittest.mock import MagicMock

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

    async def noop_auto_populate(document_metadata, source_id):
        pass

    # Provide a real Anthropic model (uses ANTHROPIC_API_KEY from environment)
    async def real_provision_model(content, model_id, default_type, **kwargs):
        model_name = (
            model_id or os.environ.get("TEST_MODEL", "claude-haiku-4-5-20251001")
        )
        # Use only supported kwargs for ChatAnthropic
        allowed_kwargs = {
            k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")
        }
        return ChatAnthropic(model=model_name, **allowed_kwargs)

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
    print(f"Matched: {len(found)}/{len(expected)} ({100 * len(found) // len(expected)}%)")

    if missing:
        print(f"\nMISSING RECORDS ({len(missing)}):")
        for i, rec in enumerate(missing, 1):
            print(
                f"  {i}. [{rec['level']}] {rec['room']} / {rec['location']} / {rec['item']}"
                f" (sample: {rec['sample_no']})"
            )

    # 7. Assert all 31 records were found
    assert len(missing) == 0, (
        f"{len(missing)}/{len(expected)} expected records not found in extraction.\n"
        f"Missing:\n"
        + "\n".join(
            f"  - [{r['level']}] {r['room']} / {r['location']} / {r['item']} (sample: {r['sample_no']})"
            for r in missing
        )
    )

    print(f"\n✓ All {len(expected)} records successfully extracted!")
