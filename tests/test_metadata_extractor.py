"""
Unit tests for Document Metadata Extraction Enhancement.

Tests cover:
- Enhanced DocumentMeta Pydantic model (Task 1)
- Metadata extraction prompt template (Task 2)
- extract_document_metadata() function (Task 3)
- SiteConfig auto-fill logic (Task 4)
- LangGraph pipeline integration (Task 5)

Story: E1-S19 Document Metadata Extraction Enhancement
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# Task 1: Enhanced DocumentMeta Pydantic Model Tests
# ============================================================================


class TestDocumentMetaPydanticModel:
    """Test enhanced DocumentMeta Pydantic model (AC: #3, #5)."""

    def test_document_meta_is_pydantic_model(self):
        """DocumentMeta is a Pydantic BaseModel, not a dataclass."""
        from pydantic import BaseModel

        from open_notebook.extractors.parsers.base import DocumentMeta

        assert issubclass(DocumentMeta, BaseModel)

    def test_document_meta_creation_required_field(self):
        """DocumentMeta requires consultant_name."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Generic")
        assert meta.consultant_name == "Generic"

    def test_document_meta_preserves_existing_fields(self):
        """All original fields are preserved after Pydantic upgrade."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Prensa",
            site_name="Test School",
            site_address="123 Main St",
            report_date="2025-01-15",
            report_reference="REF-001",
            building_size="Large",
            building_age="1950",
            additional={"key": "value"},
        )
        assert meta.consultant_name == "Prensa"
        assert meta.site_name == "Test School"
        assert meta.site_address == "123 Main St"
        assert meta.report_date == "2025-01-15"
        assert meta.report_reference == "REF-001"
        assert meta.building_size == "Large"
        assert meta.building_age == "1950"
        assert meta.additional == {"key": "value"}

    def test_document_meta_optional_fields_default_none(self):
        """New optional fields default to None."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        assert meta.site_name is None
        assert meta.site_address is None
        assert meta.report_date is None
        assert meta.report_reference is None
        assert meta.suburb is None
        assert meta.postcode is None
        assert meta.organization is None
        assert meta.inspection_dates is None
        assert meta.inspector_names is None
        assert meta.document_scope is None
        assert meta.methodology is None
        assert meta.revision_date is None
        assert meta.regional_classification is None

    def test_document_meta_additional_defaults_empty_dict(self):
        """Additional field defaults to empty dict."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        assert meta.additional == {}

    def test_document_meta_field_confidence_defaults_empty_dict(self):
        """field_confidence defaults to empty dict."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        assert meta.field_confidence == {}

    def test_document_meta_new_fields_populated(self):
        """New fields can be populated."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Greencap",
            suburb="Richmond",
            postcode="3121",
            organization="DET",
            inspection_dates=["2025-01-10", "2025-01-11"],
            inspector_names=["John Smith", "Jane Doe"],
            document_scope="Full building assessment",
            methodology="Visual inspection with sampling",
            revision_date="2025-02-01",
            regional_classification="Metro",
        )
        assert meta.suburb == "Richmond"
        assert meta.postcode == "3121"
        assert meta.organization == "DET"
        assert meta.inspection_dates == ["2025-01-10", "2025-01-11"]
        assert meta.inspector_names == ["John Smith", "Jane Doe"]
        assert meta.document_scope == "Full building assessment"
        assert meta.methodology == "Visual inspection with sampling"
        assert meta.revision_date == "2025-02-01"
        assert meta.regional_classification == "Metro"

    def test_field_confidence_population(self):
        """field_confidence dict maps field_name -> confidence level."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            suburb="Richmond",
            field_confidence={
                "consultant_name": "extracted",
                "suburb": "extracted",
                "organization": "inferred",
                "document_scope": "missing",
            },
        )
        assert meta.field_confidence["consultant_name"] == "extracted"
        assert meta.field_confidence["suburb"] == "extracted"
        assert meta.field_confidence["organization"] == "inferred"
        assert meta.field_confidence["document_scope"] == "missing"

    def test_get_extracted_fields(self):
        """get_extracted_fields() returns only non-None fields."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Prensa",
            site_name="Test School",
            suburb="Richmond",
            postcode=None,
            organization=None,
        )
        extracted = meta.get_extracted_fields()
        assert "consultant_name" in extracted
        assert extracted["consultant_name"] == "Prensa"
        assert "site_name" in extracted
        assert extracted["site_name"] == "Test School"
        assert "suburb" in extracted
        assert extracted["suburb"] == "Richmond"
        assert "postcode" not in extracted
        assert "organization" not in extracted

    def test_get_extracted_fields_excludes_confidence_and_additional(self):
        """get_extracted_fields() excludes meta fields like field_confidence and additional."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            field_confidence={"consultant_name": "extracted"},
            additional={"key": "value"},
        )
        extracted = meta.get_extracted_fields()
        assert "field_confidence" not in extracted
        assert "additional" not in extracted
        assert "consultant_name" in extracted

    def test_get_site_config_mappings(self):
        """get_site_config_mappings() returns fields that map to SiteConfig."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            organization="DET",
            suburb="Richmond",
            postcode="3121",
        )
        mappings = meta.get_site_config_mappings()
        assert "agency" in mappings
        assert mappings["agency"] == "DET"

    def test_get_site_config_mappings_empty_when_no_org(self):
        """get_site_config_mappings() returns empty dict if no organization."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        mappings = meta.get_site_config_mappings()
        assert mappings == {}

    def test_document_meta_json_serializable(self):
        """DocumentMeta can be serialized to JSON (Pydantic feature)."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            inspection_dates=["2025-01-10"],
        )
        json_str = meta.model_dump_json()
        assert "consultant_name" in json_str
        assert "Test" in json_str


# ============================================================================
# Task 3: extract_document_metadata() Tests
# ============================================================================


class TestHeuristicRegexExtraction:
    """Test heuristic regex extraction patterns (AC: #1, #2, #6)."""

    def test_extract_address_pattern(self):
        """Extracts Australian street address from cover page."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """SAMP Report
        123 Smith Street
        Richmond VIC 3121
        """
        result = _heuristic_extract(content)
        assert result.site_address is not None
        assert "Smith Street" in result.site_address or "123" in result.site_address

    def test_extract_suburb_postcode(self):
        """Extracts suburb and postcode from address."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Report
        45 Main Road
        Ballarat VIC 3350
        """
        result = _heuristic_extract(content)
        assert result.suburb is not None
        assert result.postcode is not None

    def test_extract_report_reference_report_no(self):
        """Extracts report reference with 'Report No.' format."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Report No. REF-2025-001
        Prepared for Test School
        """
        result = _heuristic_extract(content)
        assert result.report_reference is not None
        assert "REF-2025-001" in result.report_reference

    def test_extract_report_reference_job_number(self):
        """Extracts report reference with 'Job No.' format."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Job No. J12345
        Site: School
        """
        result = _heuristic_extract(content)
        assert result.report_reference is not None

    def test_extract_date_dd_mm_yyyy(self):
        """Extracts date in DD/MM/YYYY format."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Report Date: 15/01/2025
        Inspection carried out.
        """
        result = _heuristic_extract(content)
        assert result.report_date is not None

    def test_extract_date_month_year(self):
        """Extracts date in 'Month YYYY' format."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """January 2025
        This report presents findings.
        """
        result = _heuristic_extract(content)
        assert result.report_date is not None

    def test_extract_consultant_prepared_by(self):
        """Extracts consultant name from 'Prepared by' pattern."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Prepared by Prensa Pty Ltd
        123 Example Street
        """
        result = _heuristic_extract(content)
        assert result.consultant_name is not None
        assert "Prensa" in result.consultant_name

    def test_extract_inspector_names(self):
        """Extracts inspector names from 'Inspector:' pattern."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Inspector: John Smith
        Assessor: Jane Doe
        """
        result = _heuristic_extract(content)
        assert result.inspector_names is not None
        assert len(result.inspector_names) >= 1

    def test_extract_inspection_date(self):
        """Extracts inspection date from 'Inspection Date:' pattern."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Inspection Date: 10/01/2025
        Report compiled.
        """
        result = _heuristic_extract(content)
        assert result.inspection_dates is not None
        assert len(result.inspection_dates) >= 1

    def test_extract_address_all_caps(self):
        """Extracts address even when PDF text is ALL CAPS."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """SAMP REPORT
        123 SMITH STREET
        RICHMOND VIC 3121
        """
        result = _heuristic_extract(content)
        assert result.site_address is not None
        assert "SMITH" in result.site_address or "Smith" in result.site_address

    def test_extract_suburb_all_caps(self):
        """Extracts suburb and postcode from ALL CAPS address."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """REPORT
        45 MAIN ROAD
        BALLARAT VIC 3350
        """
        result = _heuristic_extract(content)
        assert result.suburb is not None
        assert result.postcode == "3350"

    def test_date_regex_rejects_short_years(self):
        """Date regex requires 4-digit year, rejects ambiguous patterns."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        # Should NOT match version-like patterns
        content = """Version 1/2/3
        No real dates here.
        """
        result = _heuristic_extract(content)
        assert result.report_date is None

    def test_heuristic_empty_content(self):
        """Heuristic returns minimal DocumentMeta for empty content."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        result = _heuristic_extract("")
        assert result.consultant_name == "Unknown"

    def test_heuristic_prensa_format(self):
        """Extracts metadata from Prensa-style cover page."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """SCHOOL ASBESTOS MANAGEMENT PLAN (SAMP)

Prepared by Prensa Pty Ltd

Report No. PRE-2025-0042

Ballarat Primary School
45 Main Road
Ballarat VIC 3350

Inspection Date: 10/01/2025
Inspector: John Smith
"""
        result = _heuristic_extract(content)
        assert "Prensa" in (result.consultant_name or "")
        assert result.report_reference is not None

    def test_heuristic_greencap_format(self):
        """Extracts metadata from Greencap-style cover page."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Asbestos Risk Assessment

Consultant: Greencap Group
Reference: GC-2025-789

Richmond High School
123 Smith Street
Richmond VIC 3121

Assessor: Jane Doe
"""
        result = _heuristic_extract(content)
        assert "Greencap" in (result.consultant_name or "")
        assert result.report_reference is not None


class TestCoverPageExtraction:
    """Test cover page text extraction (first 3-5 pages)."""

    def test_extract_cover_pages(self):
        """Extracts first 3-5 pages for cover page analysis."""
        from open_notebook.extractors.metadata_extractor import _extract_cover_pages

        content = """--- Page 1 ---
Page 1 content
--- Page 2 ---
Page 2 content
--- Page 3 ---
Page 3 content
--- Page 4 ---
Page 4 content
--- Page 5 ---
Page 5 content
--- Page 6 ---
Page 6 content
"""
        cover = _extract_cover_pages(content)
        assert "Page 1 content" in cover
        assert "Page 5 content" in cover
        assert "Page 6 content" not in cover

    def test_extract_cover_pages_short_doc(self):
        """Returns full content for documents shorter than 5 pages."""
        from open_notebook.extractors.metadata_extractor import _extract_cover_pages

        content = """--- Page 1 ---
Short doc
--- Page 2 ---
Only 2 pages
"""
        cover = _extract_cover_pages(content)
        assert "Short doc" in cover
        assert "Only 2 pages" in cover

    def test_extract_cover_pages_no_markers(self):
        """Returns full content when no page markers exist."""
        from open_notebook.extractors.metadata_extractor import _extract_cover_pages

        content = "Just plain text without page markers"
        cover = _extract_cover_pages(content)
        assert cover == content


class TestMetadataExtractionFunction:
    """Test extract_document_metadata() main function (AC: #1-3, #5-6)."""

    @pytest.mark.asyncio
    async def test_extract_with_empty_content(self):
        """Returns None for empty content."""
        from open_notebook.extractors.metadata_extractor import (
            extract_document_metadata,
        )

        result = await extract_document_metadata("")
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_with_none_content(self):
        """Returns None for None content."""
        from open_notebook.extractors.metadata_extractor import (
            extract_document_metadata,
        )

        result = await extract_document_metadata(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_heuristic_fallback_on_llm_failure(self):
        """Falls back to heuristic when LLM fails."""
        from open_notebook.extractors.metadata_extractor import (
            extract_document_metadata,
        )

        content = """--- Page 1 ---
Prepared by Prensa Pty Ltd
Report No. REF-001
45 Main Road
Ballarat VIC 3350
"""
        # Force LLM failure by patching provision_langchain_model to raise
        with patch(
            "open_notebook.extractors.metadata_extractor.provision_langchain_model",
            side_effect=Exception("LLM unavailable"),
        ):
            result = await extract_document_metadata(content)

        assert result is not None
        assert "Prensa" in (result.consultant_name or "")
        assert result.report_reference is not None

    @pytest.mark.asyncio
    async def test_extract_with_mocked_llm(self):
        """LLM extraction produces DocumentMeta with fields populated."""
        from open_notebook.extractors.metadata_extractor import (
            extract_document_metadata,
        )
        from open_notebook.extractors.parsers.base import DocumentMeta

        mock_llm_result = DocumentMeta(
            consultant_name="Prensa Pty Ltd",
            site_name="Test School",
            site_address="123 Main St",
            suburb="Richmond",
            postcode="3121",
            organization="DET",
            report_date="2025-01-15",
            report_reference="PRE-2025-001",
        )

        mock_model = AsyncMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_llm_result)
        mock_model.with_structured_output = MagicMock(return_value=mock_chain)

        with patch(
            "open_notebook.extractors.metadata_extractor.provision_langchain_model",
            return_value=mock_model,
        ):
            result = await extract_document_metadata("Some cover page content")

        assert result is not None
        assert result.consultant_name == "Prensa Pty Ltd"
        assert result.site_name == "Test School"
        assert result.suburb == "Richmond"

    @pytest.mark.asyncio
    async def test_merge_llm_and_heuristic(self):
        """LLM results take priority, heuristic fills gaps."""
        from open_notebook.extractors.metadata_extractor import _merge_metadata
        from open_notebook.extractors.parsers.base import DocumentMeta

        llm_result = DocumentMeta(
            consultant_name="Prensa Pty Ltd",
            site_name="Test School",
        )
        heuristic_result = DocumentMeta(
            consultant_name="Unknown Firm",
            report_reference="REF-001",
            suburb="Richmond",
            postcode="3121",
        )
        merged = _merge_metadata(llm_result, heuristic_result)

        # LLM takes priority
        assert merged.consultant_name == "Prensa Pty Ltd"
        assert merged.site_name == "Test School"
        # Heuristic fills gaps
        assert merged.report_reference == "REF-001"
        assert merged.suburb == "Richmond"
        assert merged.postcode == "3121"

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Confidence scoring marks extracted vs inferred vs missing."""
        from open_notebook.extractors.metadata_extractor import _compute_confidence
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Prensa",
            site_name="Test School",
            suburb=None,
            postcode=None,
        )
        confidence = _compute_confidence(
            meta, llm_fields={"consultant_name", "site_name"}
        )
        assert confidence["consultant_name"] == "extracted"
        assert confidence["site_name"] == "extracted"
        assert confidence["suburb"] == "missing"
        assert confidence["postcode"] == "missing"

    @pytest.mark.asyncio
    async def test_confidence_scoring_inferred(self):
        """Fields from heuristic (not LLM) are marked 'inferred'."""
        from open_notebook.extractors.metadata_extractor import _compute_confidence
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Prensa",
            site_name="Test School",
            report_reference="REF-001",
        )
        # Only consultant_name came from LLM; site_name and report_reference from heuristic
        confidence = _compute_confidence(meta, llm_fields={"consultant_name"})
        assert confidence["consultant_name"] == "extracted"
        assert confidence["site_name"] == "inferred"
        assert confidence["report_reference"] == "inferred"

    @pytest.mark.asyncio
    async def test_confidence_scoring_no_llm_fields(self):
        """All non-None fields are 'inferred' when no LLM was used."""
        from open_notebook.extractors.metadata_extractor import _compute_confidence
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Prensa",
            report_reference="REF-001",
            suburb=None,
        )
        confidence = _compute_confidence(meta, llm_fields=None)
        assert confidence["consultant_name"] == "inferred"
        assert confidence["report_reference"] == "inferred"
        assert confidence["suburb"] == "missing"


# ============================================================================
# Task 4: SiteConfig Auto-Fill Tests
# ============================================================================


class TestSiteConfigAutoFill:
    """Test SiteConfig auto-fill logic (AC: #4)."""

    @pytest.mark.asyncio
    async def test_auto_populate_with_organization(self):
        """Auto-fills agency from organization."""
        from open_notebook.extractors.metadata_extractor import (
            auto_populate_site_config,
        )
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            organization="DET",
        )

        # Mock SiteConfig.get_by_source to return None (no existing config)
        with patch(
            "open_notebook.domain.site_config.SiteConfig.get_by_source",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "open_notebook.domain.site_config.SiteConfig.upsert",
                new_callable=AsyncMock,
            ) as mock_upsert:
                await auto_populate_site_config(meta, "source:test123")

                mock_upsert.assert_called_once()
                call_kwargs = mock_upsert.call_args
                assert call_kwargs[1]["agency"] == "DET"

    @pytest.mark.asyncio
    async def test_auto_populate_skips_existing_fields(self):
        """Does not overwrite existing SiteConfig fields."""
        from open_notebook.extractors.metadata_extractor import (
            auto_populate_site_config,
        )
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            organization="DET",
        )

        # Mock existing config with agency already set
        mock_existing = MagicMock()
        mock_existing.agency = "Existing Agency"

        with patch(
            "open_notebook.domain.site_config.SiteConfig.get_by_source",
            new_callable=AsyncMock,
            return_value=mock_existing,
        ):
            with patch(
                "open_notebook.domain.site_config.SiteConfig.upsert",
                new_callable=AsyncMock,
            ) as mock_upsert:
                await auto_populate_site_config(meta, "source:test123")

                # Should NOT call upsert since agency is already set
                mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_populate_no_metadata(self):
        """Does nothing when no mappable fields exist."""
        from open_notebook.extractors.metadata_extractor import (
            auto_populate_site_config,
        )
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")

        with patch(
            "open_notebook.domain.site_config.SiteConfig.get_by_source",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "open_notebook.domain.site_config.SiteConfig.upsert",
                new_callable=AsyncMock,
            ) as mock_upsert:
                await auto_populate_site_config(meta, "source:test123")

                mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_populate_logs_audit_trail(self):
        """Logs auto-filled fields for audit trail."""
        from open_notebook.extractors.metadata_extractor import (
            auto_populate_site_config,
        )
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            organization="DET",
        )

        with patch(
            "open_notebook.domain.site_config.SiteConfig.get_by_source",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "open_notebook.domain.site_config.SiteConfig.upsert",
                new_callable=AsyncMock,
            ):
                with patch(
                    "open_notebook.extractors.metadata_extractor.logger"
                ) as mock_logger:
                    await auto_populate_site_config(meta, "source:test123")
                    mock_logger.info.assert_called()


# ============================================================================
# Task 5: LangGraph Pipeline Integration Tests
# ============================================================================


class TestPipelineIntegration:
    """Test LangGraph node integration (AC: #7)."""

    def test_extraction_state_has_document_metadata(self):
        """ExtractionState TypedDict includes document_metadata field."""
        from open_notebook.graphs.acm_extraction import ExtractionState

        # TypedDict annotations should include document_metadata
        annotations = ExtractionState.__annotations__
        assert "document_metadata" in annotations

    def test_graph_has_extract_metadata_node(self):
        """Graph includes extract_metadata node."""
        from open_notebook.graphs.acm_extraction import graph

        # Check the node names in the compiled graph
        node_names = set(graph.nodes.keys())
        assert "extract_metadata" in node_names

    def test_initial_state_document_metadata_none(self):
        """Initial state initializes document_metadata to None."""
        # Verify the pattern in extract_acm_from_source
        import inspect

        from open_notebook.graphs import acm_extraction

        source_code = inspect.getsource(acm_extraction.extract_acm_from_source)
        assert "document_metadata" in source_code

    @pytest.mark.asyncio
    async def test_extract_metadata_node_success(self):
        """extract_metadata node updates state with DocumentMeta."""
        from open_notebook.extractors.parsers.base import DocumentMeta
        from open_notebook.graphs.acm_extraction import extract_metadata_node

        mock_source = MagicMock()
        mock_source.id = "source:test"
        mock_source.full_text = """--- Page 1 ---
Prepared by Prensa Pty Ltd
Report No. REF-001
"""

        state = {
            "source": mock_source,
            "model_id": None,
        }
        config = MagicMock()

        with patch(
            "open_notebook.graphs.acm_extraction.extract_document_metadata",
            return_value=DocumentMeta(consultant_name="Prensa"),
        ):
            result = await extract_metadata_node(state, config)

        assert "document_metadata" in result
        assert result["document_metadata"] is not None
        assert result["document_metadata"].consultant_name == "Prensa"

    @pytest.mark.asyncio
    async def test_extract_metadata_node_failure_returns_none(self):
        """extract_metadata node returns None on failure (graceful fallback)."""
        from open_notebook.graphs.acm_extraction import extract_metadata_node

        mock_source = MagicMock()
        mock_source.id = "source:test"
        mock_source.full_text = "Some content"

        state = {
            "source": mock_source,
            "model_id": None,
        }
        config = MagicMock()

        with patch(
            "open_notebook.graphs.acm_extraction.extract_document_metadata",
            side_effect=Exception("Extraction failed"),
        ):
            result = await extract_metadata_node(state, config)

        assert result["document_metadata"] is None

    @pytest.mark.asyncio
    async def test_extract_metadata_node_empty_content(self):
        """extract_metadata node handles source with no content."""
        from open_notebook.graphs.acm_extraction import extract_metadata_node

        mock_source = MagicMock()
        mock_source.id = "source:test"
        mock_source.full_text = ""

        state = {
            "source": mock_source,
            "model_id": None,
        }
        config = MagicMock()

        result = await extract_metadata_node(state, config)
        assert result["document_metadata"] is None


# ============================================================================
# Task 6: Backward Compatibility Tests
# ============================================================================


class TestBackwardCompatibility:
    """Test that DocumentMeta upgrade doesn't break existing code."""

    def test_generic_parser_extract_metadata_returns_pydantic(self):
        """GenericParser.extract_metadata() returns Pydantic DocumentMeta."""
        from pydantic import BaseModel

        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        result = parser.extract_metadata({1: "Page 1 content"})
        assert isinstance(result, BaseModel)
        assert result.consultant_name == "Generic"

    def test_document_meta_import_from_init(self):
        """DocumentMeta can be imported from parsers __init__."""
        from open_notebook.extractors.parsers import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        assert meta.consultant_name == "Test"

    def test_document_meta_additional_dict_access(self):
        """meta.additional['key'] access pattern still works."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(
            consultant_name="Test",
            additional={"key": "value"},
        )
        assert meta.additional["key"] == "value"

    def test_document_meta_keyword_creation(self):
        """DocumentMeta creation with keyword args works (same as dataclass)."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Generic")
        assert meta.consultant_name == "Generic"
        assert meta.additional == {}


# ============================================================================
# Task 6 (continued): Multi-format support tests
# ============================================================================


class TestMultiFormatSupport:
    """Test metadata extraction across different document formats (AC: #6)."""

    def test_prensa_style_metadata(self):
        """Extracts from Prensa-style SAMP document."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """SCHOOL ASBESTOS MANAGEMENT PLAN

Prepared by Prensa Pty Ltd

Report No. PRE-2025-0042

Ballarat Primary School
45 Main Road
Ballarat VIC 3350

Inspection Date: 10/01/2025
Inspector: J. Smith
"""
        result = _heuristic_extract(content)
        assert "Prensa" in (result.consultant_name or "")

    def test_greencap_style_metadata(self):
        """Extracts from Greencap-style assessment."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """ASBESTOS RISK ASSESSMENT

Consultant: Greencap Group

Reference: GC-2025-789

Richmond High School
123 Smith Street
Richmond VIC 3121
"""
        result = _heuristic_extract(content)
        assert "Greencap" in (result.consultant_name or "")

    def test_generic_samp_metadata(self):
        """Extracts from generic SAMP format."""
        from open_notebook.extractors.metadata_extractor import _heuristic_extract

        content = """Site Asbestos Management Plan

Job No. ABC-123

Assessed by Environmental Consulting Pty Ltd

15 January 2025
"""
        result = _heuristic_extract(content)
        assert result.report_reference is not None
