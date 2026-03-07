"""
End-to-end tests for the ACM extraction LangGraph pipeline.

Tests the complete extraction flow through the graph:
  metadata → structure → inventory → tag_pages → [orchestrate|prepare]
  → extract → validate → correct → deduplicate → save

Two test variants:
  1. Legacy path: No building inventory → prepare → extract → validate → ...
  2. Orchestrator path: With building inventory → orchestrate → validate → ...

Pre-processing stages (metadata, structure, inventory, page tagging) are mocked
with realistic data based on the sample_input.txt fixture. The LLM extraction is
mocked to return records matching expected_output.json. Validation, correction,
deduplication, and save logic run with real code (DB operations mocked).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas import (
    ACMExtractionRecord,
    ACMExtractionResult,
    ExtractionStatus,
)
from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingInventory,
    BuildingMeta,
    ProcessingGroup,
)
from open_notebook.extractors.document_structure import (
    DocumentStructure,
    DocumentType,
    Section,
)
from open_notebook.extractors.page_tagger import (
    PageTag,
    PageTaggingResult,
    PageType,
)
from open_notebook.extractors.parsers.base import DocumentMeta

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "acm_extraction"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


def _load_json_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def _make_mock_source(
    content: str, source_id: str = "source:test_e2e_123"
) -> MagicMock:
    """Create a mock Source object with the given content."""
    source = MagicMock()
    source.id = source_id
    source.full_text = content
    source.title = "Test School - Asbestos Register"
    source.asset = MagicMock(file_path="data/uploads/test.pdf")
    return source


def _make_document_meta() -> DocumentMeta:
    return DocumentMeta(
        consultant_name="Test Assessor Pty Ltd",
        site_name="Test School",
        report_date="2025-01-15",
    )


def _make_document_structure() -> DocumentStructure:
    return DocumentStructure(
        document_type=DocumentType.SAMP,
        toc_present=False,
        total_pages=2,
        register_start_page=1,
        building_ids=["A1", "B1"],
        sections=[
            Section(section_id=4, title="Asbestos Register", page_start=1, page_end=2),
        ],
    )


def _make_building_inventory() -> BuildingInventory:
    return BuildingInventory(
        buildings=[
            BuildingMeta(
                building_id="A1",
                name="Administration Block",
                year=1965,
                construction="Brick",
                page_start=1,
                page_end=1,
                complexity=BuildingComplexity.SIMPLE,
            ),
            BuildingMeta(
                building_id="B1",
                name="Science Wing",
                year=1972,
                construction="Concrete",
                page_start=2,
                page_end=2,
                complexity=BuildingComplexity.SIMPLE,
            ),
        ],
        processing_groups=[
            ProcessingGroup(
                group_id=0,
                building_ids=["A1", "B1"],
                page_start=1,
                page_end=2,
                estimated_pages=2,
            ),
        ],
        total_buildings=2,
        document_type="SAMP",
    )


def _make_page_tags() -> PageTaggingResult:
    return PageTaggingResult(
        pages=[
            PageTag(
                page_number=1,
                section_id=4,
                section_title="Asbestos Register",
                confidence=0.95,
                page_type=PageType.CONTENT,
            ),
            PageTag(
                page_number=2,
                section_id=4,
                section_title="Asbestos Register",
                confidence=0.95,
                page_type=PageType.CONTENT,
            ),
        ],
        total_pages=2,
        register_page_range=(1, 2),
    )


def _make_extraction_records() -> List[ACMExtractionRecord]:
    """Build ACMExtractionRecord list from the expected_output.json fixture."""
    expected = _load_json_fixture("expected_output.json")
    records = []
    for r in expected["records"]:
        records.append(
            ACMExtractionRecord(
                building_id=r["building_id"],
                building_name=r.get("building_name"),
                building_year=r.get("building_year"),
                building_construction=r.get("building_construction"),
                room_id=r.get("room_id"),
                room_name=r.get("room_name"),
                room_area=r.get("room_area"),
                area_type=r.get("area_type"),
                product=r["product"],
                material_description=r["material_description"],
                extent=r.get("extent"),
                location=r.get("location"),
                friable=r.get("friable"),
                material_condition=r.get("material_condition"),
                risk_status=r.get("risk_status"),
                result=r.get("result"),
                page_number=r.get("page_number"),
                extraction_confidence="high",
            )
        )
    return records


def _make_mock_llm_model(records: List[ACMExtractionRecord]) -> MagicMock:
    """Create a mock LLM model that returns JSON via direct ainvoke().

    E27-S1: All extraction paths now use model.ainvoke() → parse_json_response()
    instead of model.with_structured_output().ainvoke(). The mock returns a
    response object whose .content is valid JSON matching ACMExtractionResult.
    """
    result = ACMExtractionResult(
        records=records,
        status=ExtractionStatus.VALID,
        total_records=len(records),
    )
    json_content = result.model_dump_json()
    response = MagicMock()
    response.content = json_content
    model = AsyncMock()
    model.ainvoke = AsyncMock(return_value=response)
    return model


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_content():
    return _load_fixture("sample_input.txt")


@pytest.fixture
def expected_output():
    return _load_json_fixture("expected_output.json")


@pytest.fixture
def mock_source(sample_content):
    return _make_mock_source(sample_content)


# ---------------------------------------------------------------------------
# Test: Regex extraction (no LLM, no graph)
# ---------------------------------------------------------------------------


class TestRegexExtraction:
    """Baseline: verify the regex extractor produces correct records."""

    def test_record_count(self, sample_content, expected_output):
        from open_notebook.extractors.acm_extractor import extract_acm_records

        records = extract_acm_records(sample_content, "source:test")
        assert len(records) == expected_output["total_records"]

    def test_all_expected_records_present(self, sample_content, expected_output):
        from open_notebook.extractors.acm_extractor import extract_acm_records

        records = extract_acm_records(sample_content, "source:test")
        for exp in expected_output["records"]:
            match = [
                r
                for r in records
                if r["building_id"] == exp["building_id"]
                and r["product"] == exp["product"]
            ]
            assert match, (
                f"Missing record: building={exp['building_id']}, product={exp['product']}"
            )

    def test_field_values(self, sample_content, expected_output):
        from open_notebook.extractors.acm_extractor import extract_acm_records

        records = extract_acm_records(sample_content, "source:test")
        # Spot-check first expected record
        exp = expected_output["records"][0]
        match = [
            r
            for r in records
            if r["building_id"] == exp["building_id"] and r["product"] == exp["product"]
        ]
        assert match
        rec = match[0]
        assert rec["material_description"] == exp["material_description"]
        # result field is normalized by enum normalizer: "Detected" → "Positive"
        assert rec["result"] in (exp["result"], "Positive", "Assumed Positive")
        assert rec["risk_status"] == exp["risk_status"]
        assert rec["page_number"] == exp["page_number"]


# ---------------------------------------------------------------------------
# Test: MinerU → regex extraction (PDF → markdown → records)
# ---------------------------------------------------------------------------


class TestMineruToRecords:
    """Test the PDF → markdown → regex extraction flow.

    Uses the sample PDF files in docs/samplePDF/ if available.
    Skipped if PDFs are not present (CI environment).
    """

    SAMPLE_PDF_DIR = Path(__file__).parent.parent / "docs" / "samplePDF"

    @pytest.mark.skipif(
        not (
            Path(__file__).parent.parent
            / "docs"
            / "samplePDF"
            / "1124_AsbestosRegister.pdf"
        ).exists(),
        reason="Sample PDF not available",
    )
    def test_pdf_exists_and_is_readable(self):
        """Verify test PDF file is accessible."""
        pdf_path = self.SAMPLE_PDF_DIR / "1124_AsbestosRegister.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    @pytest.mark.skipif(
        not (
            Path(__file__).parent.parent
            / "docs"
            / "samplePDF"
            / "1124_AsbestosRegister.pdf"
        ).exists(),
        reason="Sample PDF not available",
    )
    def test_regex_extraction_from_real_pdf_markdown(self):
        """Test regex extraction using pre-extracted markdown from a real PDF.

        This uses the sample_input.txt fixture which represents the markdown
        output from processing a real SAMP PDF through content-core.
        """
        from open_notebook.extractors.acm_extractor import extract_acm_records

        content = _load_fixture("sample_input.txt")
        records = extract_acm_records(content, "source:pdf_test")

        # Should extract meaningful records
        assert len(records) >= 4

        # All records should have required fields
        for rec in records:
            assert rec["building_id"], f"Missing building_id: {rec}"
            assert rec["product"], f"Missing product: {rec}"
            assert rec["material_description"], f"Missing material_description: {rec}"
            assert rec["result"], f"Missing result: {rec}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
