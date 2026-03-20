"""
Tests for Document Structure & TOC Extraction (E1-S16).

Tests cover:
- DocumentStructure Pydantic models (Task 1)
- Structure extraction prompt template (Task 2)
- extract_document_structure() function (Task 3)
- LangGraph pipeline integration (Task 4)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.document_structure import (
    DocumentStructure,
    DocumentType,
    Section,
    SubSection,
    extract_document_structure,
)


class TestDocumentTypeEnum:
    """Test DocumentType enum (Task 1.1)."""

    def test_samp_type(self):
        assert DocumentType.SAMP == "SAMP"

    def test_ara_type(self):
        assert DocumentType.ARA == "ARA"

    def test_division_5_type(self):
        assert DocumentType.DIVISION_5 == "Division_5"

    def test_unknown_type(self):
        assert DocumentType.UNKNOWN == "Unknown"


class TestSubSectionModel:
    """Test SubSection model (Task 1.3)."""

    def test_create_subsection(self):
        sub = SubSection(
            subsection_number="4.1",
            title="Building B001 Register",
            page_start=15,
            page_end=20,
        )
        assert sub.subsection_number == "4.1"
        assert sub.title == "Building B001 Register"
        assert sub.page_start == 15
        assert sub.page_end == 20

    def test_subsection_optional_page_end(self):
        sub = SubSection(
            subsection_number="4.2",
            title="Building B002 Register",
            page_start=21,
        )
        assert sub.page_end is None


class TestSectionModel:
    """Test Section model (Task 1.2)."""

    def test_create_section(self):
        section = Section(
            section_id=4,
            title="Asbestos Register",
            page_start=13,
            page_end=45,
        )
        assert section.section_id == 4
        assert section.title == "Asbestos Register"
        assert section.page_start == 13
        assert section.page_end == 45
        assert section.subsections == []

    def test_section_with_subsections(self):
        section = Section(
            section_id=4,
            title="Asbestos Register",
            page_start=13,
            page_end=45,
            subsections=[
                SubSection(
                    subsection_number="4.1", title="B001", page_start=13, page_end=25
                ),
                SubSection(
                    subsection_number="4.2", title="B002", page_start=26, page_end=45
                ),
            ],
        )
        assert len(section.subsections) == 2

    def test_section_id_range(self):
        """Section IDs must be 0-7 per taxonomy."""
        section = Section(section_id=0, title="Executive Summary", page_start=1)
        assert section.section_id == 0

        section = Section(section_id=7, title="Appendix", page_start=50)
        assert section.section_id == 7

    def test_section_id_out_of_range_accepted(self):
        """Section IDs outside 0-7 are accepted (constraints removed for LLM schema compat)."""
        section = Section(section_id=8, title="Invalid", page_start=1)
        assert section.section_id == 8

        section = Section(section_id=-1, title="Invalid", page_start=1)
        assert section.section_id == -1


class TestDocumentStructureModel:
    """Test DocumentStructure model (Task 1.4)."""

    def test_create_minimal(self):
        ds = DocumentStructure(
            document_type=DocumentType.UNKNOWN,
            total_pages=10,
        )
        assert ds.document_type == DocumentType.UNKNOWN
        assert ds.total_pages == 10
        assert ds.toc_present is False
        assert ds.sections == []
        assert ds.building_ids == []
        assert ds.register_start_page is None

    def test_create_full(self):
        ds = DocumentStructure(
            document_type=DocumentType.SAMP,
            toc_present=True,
            total_pages=55,
            register_start_page=13,
            building_ids=["B00A", "B00B", "D01"],
            sections=[
                Section(
                    section_id=0, title="Executive Summary", page_start=1, page_end=3
                ),
                Section(
                    section_id=4, title="Asbestos Register", page_start=13, page_end=50
                ),
            ],
            metadata={"consultant": "Prensa", "report_date": "2024-03-15"},
        )
        assert ds.document_type == DocumentType.SAMP
        assert ds.toc_present is True
        assert ds.total_pages == 55
        assert ds.register_start_page == 13
        assert len(ds.building_ids) == 3
        assert "B00A" in ds.building_ids
        assert "D01" in ds.building_ids
        assert len(ds.sections) == 2
        assert ds.metadata["consultant"] == "Prensa"

    def test_building_id_formats(self):
        """Verify both B000-series and D-series building IDs are supported."""
        ds = DocumentStructure(
            document_type=DocumentType.SAMP,
            total_pages=30,
            building_ids=["B00A", "B00B", "B00C", "D01", "D02"],
        )
        assert len(ds.building_ids) == 5


class TestExtractDocumentStructure:
    """Test extract_document_structure() function (Task 3)."""

    @pytest.mark.asyncio
    async def test_empty_content_returns_fallback(self):
        """Empty content should return a minimal DocumentStructure."""
        result = await extract_document_structure("")
        assert result is not None
        assert result.document_type == DocumentType.UNKNOWN
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_none_content_returns_fallback(self):
        """None content should return a minimal DocumentStructure."""
        result = await extract_document_structure(None)
        assert result is not None
        assert result.document_type == DocumentType.UNKNOWN

    @pytest.mark.asyncio
    async def test_page_count_extraction(self):
        """Should extract total page count from page markers."""
        content = """--- Page 1 ---
Some content
--- Page 5 ---
More content
--- Page 12 ---
Final content"""
        mock_structure = DocumentStructure(
            document_type=DocumentType.UNKNOWN,
            total_pages=10,  # LLM estimate - overridden by page markers
        )
        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            return_value=mock_structure,
        ):
            result = await extract_document_structure(content)
            # Page marker extraction (12) should override LLM estimate (10)
            assert result.total_pages == 12

    @pytest.mark.asyncio
    async def test_structure_extraction_with_mock_llm(self):
        """Test full extraction with mocked LLM response."""
        content = """--- Page 1 ---
# Broadmeadows SAMP
Table of Contents
1. Introduction ..................... 2
2. Site Description ................ 4
3. Methodology .................... 7
4. Asbestos Register .............. 13
5. Risk Assessment ................ 45
--- Page 13 ---
## Appendix B: Asbestos Register
### B00A - Admin Building
"""
        mock_structure = DocumentStructure(
            document_type=DocumentType.SAMP,
            toc_present=True,
            total_pages=50,
            register_start_page=13,
            building_ids=["B00A"],
            sections=[
                Section(section_id=1, title="Introduction", page_start=2, page_end=3),
                Section(
                    section_id=4, title="Asbestos Register", page_start=13, page_end=44
                ),
            ],
        )

        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            return_value=mock_structure,
        ):
            result = await extract_document_structure(content)
            assert result.document_type == DocumentType.SAMP
            assert result.toc_present is True
            assert result.register_start_page == 13
            assert "B00A" in result.building_ids

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """If LLM fails, should return heuristic-based fallback."""
        content = """--- Page 1 ---
Some intro
--- Page 13 ---
Appendix B: Asbestos Register
B001 - Main Building"""

        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            side_effect=Exception("LLM unavailable"),
        ):
            result = await extract_document_structure(content)
            assert result is not None
            assert result.document_type == DocumentType.UNKNOWN
            assert result.total_pages == 13

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """LLM failure on first attempt should retry; success on second attempt returns result."""
        content = """--- Page 1 ---
Some content
--- Page 5 ---
Appendix B: Asbestos Register"""

        success_structure = DocumentStructure(
            document_type=DocumentType.SAMP,
            total_pages=3,  # overridden by page markers
            building_ids=["B001"],
        )
        call_count = 0

        async def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Transient LLM error")
            return success_structure

        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            side_effect=fail_then_succeed,
        ):
            result = await extract_document_structure(content)

        assert call_count == 2
        assert result.document_type == DocumentType.SAMP
        assert result.total_pages == 5  # overridden by page marker
        assert "B001" in result.building_ids

    @pytest.mark.asyncio
    async def test_retry_exhausted_uses_heuristic_fallback(self):
        """When all retry attempts fail, heuristic fallback is returned with WARNING log."""
        content = """--- Page 1 ---
Some intro
--- Page 7 ---
Asbestos Register
B002 - Main Block"""

        call_count = 0

        async def always_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent LLM failure")

        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            side_effect=always_fail,
        ):
            result = await extract_document_structure(content)

        from open_notebook.extractors.document_structure import MAX_STRUCTURE_RETRIES

        assert call_count == MAX_STRUCTURE_RETRIES
        assert result is not None
        # Heuristic fallback returns UNKNOWN type
        assert result.document_type == DocumentType.UNKNOWN
        # Page markers still detected
        assert result.total_pages == 7

    @pytest.mark.asyncio
    async def test_retry_count_equals_max_structure_retries(self):
        """MAX_STRUCTURE_RETRIES constant controls the number of LLM attempts."""
        from open_notebook.extractors.document_structure import MAX_STRUCTURE_RETRIES

        assert MAX_STRUCTURE_RETRIES == 2


class TestHeuristicFallback:
    """Test heuristic-based fallback extraction (Task 5.2-5.5)."""

    def test_register_start_detection(self):
        """Should detect register start page from content markers (Task 5.5)."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 1 ---
Introduction to the SAMP
--- Page 5 ---
Methodology section
--- Page 13 ---
Appendix B: Asbestos Register
B001 - Main Building
"""
        result = _heuristic_fallback(content)
        assert result.register_start_page == 13

    def test_register_start_detection_alternative_marker(self):
        """Should detect register with alternative marker text."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 1 ---
Intro
--- Page 10 ---
Asbestos Register
B00A - Admin"""
        result = _heuristic_fallback(content)
        assert result.register_start_page == 10

    def test_building_id_enumeration(self):
        """Should extract building IDs from content (Task 5.4)."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 13 ---
B00A - Admin Building - 1950
B00B - Science Block - 1975
B00C - Library - 2001
D01 - Demountable 1
D02 - Demountable 2"""
        result = _heuristic_fallback(content)
        assert "B00A" in result.building_ids
        assert "B00B" in result.building_ids
        assert "B00C" in result.building_ids
        assert "D01" in result.building_ids
        assert "D02" in result.building_ids

    def test_document_without_toc(self):
        """Should handle documents without TOC gracefully (Task 5.6)."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 1 ---
Some random content without table of contents
--- Page 3 ---
More content"""
        result = _heuristic_fallback(content)
        assert result.toc_present is False
        assert result.document_type == DocumentType.UNKNOWN
        assert result.total_pages == 3

    def test_page_count_from_markers(self):
        """Should extract total page count from page markers."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 1 ---
Page one
--- Page 15 ---
Page fifteen
--- Page 30 ---
Page thirty"""
        result = _heuristic_fallback(content)
        assert result.total_pages == 30

    def test_no_register_marker_returns_none(self):
        """Should return None for register_start_page if no marker found."""
        from open_notebook.extractors.document_structure import _heuristic_fallback

        content = """--- Page 1 ---
Just some content without any register section"""
        result = _heuristic_fallback(content)
        assert result.register_start_page is None

    @pytest.mark.asyncio
    async def test_samp_format_toc_parsing(self):
        """Test TOC parsing with SAMP-format markdown (Task 5.2)."""
        content = """--- Page 1 ---
# Broadmeadows Primary School
# School Asbestos Management Plan

## Table of Contents
1. Introduction ..................... 2
2. Site Description ................ 4
3. Methodology ..................... 7
4. Results ......................... 10
Appendix B: Asbestos Register ...... 13
--- Page 2 ---
## 1. Introduction
--- Page 13 ---
## Appendix B: Asbestos Register
### B00A - Admin Building - 1950
### B00B - Science Block - 1975"""

        mock_structure = DocumentStructure(
            document_type=DocumentType.SAMP,
            toc_present=True,
            total_pages=13,
            register_start_page=13,
            building_ids=["B00A", "B00B"],
            sections=[
                Section(section_id=1, title="Introduction", page_start=2, page_end=3),
                Section(
                    section_id=2, title="Site Description", page_start=4, page_end=6
                ),
                Section(section_id=4, title="Asbestos Register", page_start=13),
            ],
        )

        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            return_value=mock_structure,
        ):
            result = await extract_document_structure(content)
            assert result.document_type == DocumentType.SAMP
            assert result.toc_present is True
            assert len(result.building_ids) == 2

    @pytest.mark.asyncio
    async def test_document_type_detection_samp(self):
        """Test SAMP document type detection (Task 5.3)."""
        content = "--- Page 1 ---\nSchool Asbestos Management Plan"
        mock_struct = DocumentStructure(document_type=DocumentType.SAMP, total_pages=1)
        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            return_value=mock_struct,
        ):
            result = await extract_document_structure(content)
            assert result.document_type == DocumentType.SAMP

    @pytest.mark.asyncio
    async def test_document_type_detection_ara(self):
        """Test ARA document type detection (Task 5.3)."""
        content = "--- Page 1 ---\nAsbestos Risk Assessment Report"
        mock_struct = DocumentStructure(document_type=DocumentType.ARA, total_pages=1)
        with patch(
            "open_notebook.extractors.document_structure._llm_extract_structure",
            new_callable=AsyncMock,
            return_value=mock_struct,
        ):
            result = await extract_document_structure(content)
            assert result.document_type == DocumentType.ARA


class TestPromptTemplate:
    """Test structure_extraction.jinja prompt template (Task 2)."""

    def test_prompt_renders(self):
        """Prompt template should render with content variable."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/structure_extraction")
        result = prompter.render(data={"content": "Sample SAMP document content"})
        assert "Document Structure Analysis" in result

    def test_prompt_contains_taxonomy(self):
        """Prompt should include the 0-7 section taxonomy."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/structure_extraction")
        result = prompter.render(data={"content": "test"})
        assert "Executive Summary" in result
        assert "Asbestos Register" in result
        assert "Appendix" in result

    def test_prompt_contains_building_id_instructions(self):
        """Prompt should include building ID detection instructions."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/structure_extraction")
        result = prompter.render(data={"content": "test"})
        assert "B000-series" in result
        assert "D-series" in result

    def test_prompt_contains_document_type_heuristics(self):
        """Prompt should include document type classification heuristics."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/structure_extraction")
        result = prompter.render(data={"content": "test"})
        assert "SAMP" in result
        assert "ARA" in result
        assert "Division_5" in result

    def test_prompt_contains_toc_examples(self):
        """Prompt should include Prensa and Greencap TOC examples."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/structure_extraction")
        result = prompter.render(data={"content": "test"})
        assert "Prensa" in result
        assert "Greencap" in result


class TestLangGraphIntegration:
    """Test LangGraph pipeline integration (Task 4, Task 5.8)."""

    def test_extraction_state_has_document_structure(self):
        """ExtractionState should have document_structure field."""
        from open_notebook.graphs.acm_extraction import ExtractionState

        # Verify the TypedDict has the field
        annotations = ExtractionState.__annotations__
        assert "document_structure" in annotations

    def test_graph_structure_before_prepare(self):
        """S4: Combined metadata_and_structure node wired before inventory."""
        from open_notebook.graphs.acm_extraction import agent_state

        # S4 merged flow:
        #   START -> metadata_and_structure -> inventory -> save_intelligence
        #         -> extract_building -> extract_items -> ...
        edges = agent_state.edges
        assert ("__start__", "metadata_and_structure") in edges or any(
            e == ("__start__", "metadata_and_structure") for e in edges
        ), "START should connect to metadata_and_structure (S4)"
        assert ("metadata_and_structure", "inventory") in edges or any(
            e == ("metadata_and_structure", "inventory") for e in edges
        ), "metadata_and_structure should connect to inventory (S4)"
        assert ("inventory", "save_intelligence") in edges or any(
            e == ("inventory", "save_intelligence") for e in edges
        ), "inventory should connect to save_intelligence (S4)"
        # MCS13: save_intelligence -> schema_inference -> extract_building
        assert ("save_intelligence", "schema_inference") in edges or any(
            e == ("save_intelligence", "schema_inference") for e in edges
        ), "save_intelligence should connect to schema_inference (MCS13)"
        assert ("schema_inference", "extract_building") in edges or any(
            e == ("schema_inference", "extract_building") for e in edges
        ), "schema_inference should connect to extract_building (MCS13)"
        # E32-S2: extract_building -> extract_items (replaces direct edge to orchestrate)
        assert ("extract_building", "extract_items") in edges or any(
            e == ("extract_building", "extract_items") for e in edges
        ), "extract_building should connect to extract_items (E32-S2)"


class TestSectionTaxonomy:
    """Test standardized 0-7 section taxonomy (Task 5.7)."""

    def test_all_taxonomy_ids(self):
        """Verify sections can be created for all taxonomy IDs 0-7."""
        taxonomy = [
            (0, "Executive Summary"),
            (1, "Introduction"),
            (2, "Site Description"),
            (3, "Methodology"),
            (4, "Asbestos Register"),
            (5, "Risk Assessment"),
            (6, "Conclusion"),
            (7, "Appendix"),
        ]
        for section_id, title in taxonomy:
            section = Section(section_id=section_id, title=title, page_start=1)
            assert section.section_id == section_id
            assert section.title == title
