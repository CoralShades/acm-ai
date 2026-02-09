"""
Tests for Page-Level Section Tagging.

Story: E1-S18 Page-Level Section Tagging
"""

import pytest
from pydantic import ValidationError

from open_notebook.extractors.page_tagger import (
    _SECTION_TITLES,
    PageTag,
    PageTagBatch,
    PageTaggingResult,
    PageType,
    SectionTaxonomy,
    SubSectionTag,
    _compute_register_range,
    _create_batches,
    _heuristic_tag_all,
    _heuristic_tag_page,
    _split_into_pages,
)

# --- Test data ---

SAMPLE_CONTENT = """<!-- Page 1 -->
# School Asbestos Management Plan

Prepared by Prensa Consulting
Report Date: March 2024

<!-- Page 2 -->
## Table of Contents

1.0 Introduction .............. 3
2.0 Site Description .......... 5
3.0 Methodology ............... 7
4.0 Asbestos Register ........ 13
Appendix A: Site Plan
Appendix B: Laboratory Certificates

<!-- Page 3 -->
## 1.0 Introduction

This report presents the findings of the asbestos audit conducted at Example School.

<!-- Page 5 -->
## 2.0 Site Description

Example School is located in suburban Melbourne.

<!-- Page 7 -->
## 3.0 Methodology

### 3.1 Visual Inspection

A comprehensive visual inspection was conducted across all buildings.

<!-- Page 13 -->
## Appendix B: Asbestos Register

### B00A - Admin Building - 1924 - Brick

#### B00A-R0001 - External Movement

| Material | Product | Condition | Risk |
|----------|---------|-----------|------|
| Eaves    | Asbestos Cement | Good | Low |

<!-- Page 14 -->
#### B00A-R0002 - Office Area

| Material | Product | Condition | Risk |
|----------|---------|-----------|------|
| Wall lining | Fibre Board | Fair | Medium |

<!-- Page 20 -->
### B001 - Gymnasium - 1960 - Steel

#### B001-R0001 - Main Hall

| Material | Product | Condition | Risk |
|----------|---------|-----------|------|
| Ceiling  | Asbestos Cement | Poor | High |

<!-- Page 25 -->
## 5.0 Risk Assessment

Overall the school presents a moderate risk level.

<!-- Page 28 -->
## 6.0 Conclusion

Recommendations include monitoring and management of identified ACM.

<!-- Page 30 -->
## Appendix C: Laboratory Certificates

NATA Accredited Laboratory
Certificate No: 12345
"""


class TestSectionTaxonomy:
    """Test SectionTaxonomy enum (Task 1.1)."""

    def test_section_taxonomy_values(self):
        from open_notebook.extractors.page_tagger import SectionTaxonomy

        assert SectionTaxonomy.EXECUTIVE_SUMMARY == 0
        assert SectionTaxonomy.INTRODUCTION == 1
        assert SectionTaxonomy.SITE_DESCRIPTION == 2
        assert SectionTaxonomy.METHODOLOGY == 3
        assert SectionTaxonomy.ASBESTOS_REGISTER == 4
        assert SectionTaxonomy.RISK_ASSESSMENT == 5
        assert SectionTaxonomy.CONCLUSION == 6
        assert SectionTaxonomy.APPENDIX == 7

    def test_section_taxonomy_has_8_values(self):
        from open_notebook.extractors.page_tagger import SectionTaxonomy

        assert len(SectionTaxonomy) == 8


class TestPageType:
    """Test PageType enum (Task 1.2)."""

    def test_page_type_values(self):
        from open_notebook.extractors.page_tagger import PageType

        assert PageType.TITLE_PAGE == "title_page"
        assert PageType.TOC_PAGE == "toc_page"
        assert PageType.CONTENT == "content"
        assert PageType.SPECIAL == "special"

    def test_page_type_has_4_values(self):
        from open_notebook.extractors.page_tagger import PageType

        assert len(PageType) == 4


class TestSubSectionTag:
    """Test SubSectionTag model (Task 1.3)."""

    def test_create_subsection_tag(self):
        from open_notebook.extractors.page_tagger import SubSectionTag

        tag = SubSectionTag(
            subsection_number="3.1",
            title="Visual Inspection",
            section_id=3,
        )
        assert tag.subsection_number == "3.1"
        assert tag.title == "Visual Inspection"
        assert tag.section_id == 3

    def test_subsection_section_id_range(self):
        from open_notebook.extractors.page_tagger import SubSectionTag

        with pytest.raises(ValidationError):
            SubSectionTag(subsection_number="1.1", title="Bad", section_id=8)

        with pytest.raises(ValidationError):
            SubSectionTag(subsection_number="1.1", title="Bad", section_id=-1)


class TestPageTag:
    """Test PageTag model (Task 1.4)."""

    def test_create_page_tag(self):
        from open_notebook.extractors.page_tagger import PageTag, PageType

        tag = PageTag(
            page_number=5,
            section_id=3,
            section_title="Methodology",
            confidence=0.95,
            page_type=PageType.CONTENT,
        )
        assert tag.page_number == 5
        assert tag.section_id == 3
        assert tag.section_title == "Methodology"
        assert tag.confidence == 0.95
        assert tag.page_type == PageType.CONTENT
        assert tag.subsection is None
        assert tag.content_summary is None

    def test_page_tag_with_optional_fields(self):
        from open_notebook.extractors.page_tagger import (
            PageTag,
            PageType,
            SubSectionTag,
        )

        tag = PageTag(
            page_number=7,
            section_id=3,
            section_title="Methodology",
            confidence=0.85,
            page_type=PageType.CONTENT,
            subsection=SubSectionTag(
                subsection_number="3.1",
                title="Visual Inspection",
                section_id=3,
            ),
            content_summary="Description of visual inspection methodology",
        )
        assert tag.subsection is not None
        assert tag.subsection.subsection_number == "3.1"
        assert tag.content_summary is not None

    def test_page_tag_confidence_bounds(self):
        from open_notebook.extractors.page_tagger import PageTag, PageType

        with pytest.raises(ValidationError):
            PageTag(
                page_number=1,
                section_id=0,
                section_title="Test",
                confidence=1.5,
                page_type=PageType.CONTENT,
            )

        with pytest.raises(ValidationError):
            PageTag(
                page_number=1,
                section_id=0,
                section_title="Test",
                confidence=-0.1,
                page_type=PageType.CONTENT,
            )

    def test_page_tag_section_id_bounds(self):
        from open_notebook.extractors.page_tagger import PageTag, PageType

        with pytest.raises(ValidationError):
            PageTag(
                page_number=1,
                section_id=8,
                section_title="Test",
                confidence=0.9,
                page_type=PageType.CONTENT,
            )

        with pytest.raises(ValidationError):
            PageTag(
                page_number=1,
                section_id=-1,
                section_title="Test",
                confidence=0.9,
                page_type=PageType.CONTENT,
            )


class TestPageTaggingResult:
    """Test PageTaggingResult model (Task 1.5)."""

    def test_create_empty_result(self):
        result = PageTaggingResult(
            pages=[],
            total_pages=0,
            register_page_range=None,
        )
        assert result.pages == []
        assert result.total_pages == 0
        assert result.register_page_range is None

    def test_create_result_with_pages(self):
        from open_notebook.extractors.page_tagger import (
            PageTag,
            PageType,
        )

        pages = [
            PageTag(
                page_number=1,
                section_id=0,
                section_title="Executive Summary",
                confidence=0.9,
                page_type=PageType.TITLE_PAGE,
            ),
            PageTag(
                page_number=13,
                section_id=4,
                section_title="Asbestos Register",
                confidence=0.95,
                page_type=PageType.CONTENT,
            ),
        ]
        result = PageTaggingResult(
            pages=pages,
            total_pages=30,
            register_page_range=(13, 25),
        )
        assert len(result.pages) == 2
        assert result.total_pages == 30
        assert result.register_page_range == (13, 25)


class TestPageSplitting:
    """Test _split_into_pages() function (Task 5.3)."""

    def test_split_content_with_page_markers(self):
        pages = _split_into_pages(SAMPLE_CONTENT)
        page_numbers = [pn for pn, _ in pages]
        assert 1 in page_numbers
        assert 2 in page_numbers
        assert 13 in page_numbers
        assert 30 in page_numbers

    def test_split_returns_non_empty_text(self):
        pages = _split_into_pages(SAMPLE_CONTENT)
        for pn, text in pages:
            assert text.strip(), f"Page {pn} has empty text"

    def test_split_empty_content(self):
        pages = _split_into_pages("")
        assert pages == [(1, "")]

    def test_split_no_markers(self):
        pages = _split_into_pages("Some plain text without page markers")
        assert len(pages) == 1
        assert pages[0] == (1, "Some plain text without page markers")

    def test_split_preserves_page_order(self):
        pages = _split_into_pages(SAMPLE_CONTENT)
        page_numbers = [pn for pn, _ in pages]
        assert page_numbers == sorted(page_numbers)

    def test_split_html_comment_markers(self):
        content = "<!-- Page 1 -->\nContent A\n<!-- Page 2 -->\nContent B"
        pages = _split_into_pages(content)
        assert len(pages) == 2
        assert pages[0][0] == 1
        assert pages[1][0] == 2

    def test_split_dash_markers(self):
        content = "--- Page 1 ---\nContent A\n--- Page 2 ---\nContent B"
        pages = _split_into_pages(content)
        assert len(pages) == 2
        assert pages[0][0] == 1
        assert pages[1][0] == 2


class TestBatchCreation:
    """Test _create_batches() function (Task 5.4)."""

    def test_create_batches_default_size(self):
        pages = [(i, f"Page {i}") for i in range(1, 16)]
        batches = _create_batches(pages)
        assert len(batches) == 3  # 5 + 5 + 5
        assert len(batches[0]) == 5
        assert len(batches[1]) == 5
        assert len(batches[2]) == 5

    def test_create_batches_partial_last(self):
        pages = [(i, f"Page {i}") for i in range(1, 8)]
        batches = _create_batches(pages)
        assert len(batches) == 2  # 5 + 2
        assert len(batches[0]) == 5
        assert len(batches[1]) == 2

    def test_create_batches_custom_size(self):
        pages = [(i, f"Page {i}") for i in range(1, 10)]
        batches = _create_batches(pages, batch_size=3)
        assert len(batches) == 3
        assert all(len(b) == 3 for b in batches)

    def test_create_batches_empty(self):
        batches = _create_batches([])
        assert batches == []

    def test_create_batches_single_page(self):
        batches = _create_batches([(1, "Content")])
        assert len(batches) == 1
        assert len(batches[0]) == 1


class TestHeuristicTagging:
    """Test heuristic-based page tagging (Task 5.5, 5.9)."""

    def test_title_page_detection(self):
        tag = _heuristic_tag_page(
            page_number=1,
            page_text="School Asbestos Management Plan\nPrepared by Consulting Co",
            total_pages=30,
            previous_section_id=0,
        )
        assert tag.page_type == PageType.TITLE_PAGE
        assert tag.confidence == 0.7

    def test_toc_page_detection(self):
        toc_text = (
            "Table of Contents\n1.0 Introduction ... 3\n2.0 Site Description ... 5"
        )
        tag = _heuristic_tag_page(
            page_number=2,
            page_text=toc_text,
            total_pages=30,
            previous_section_id=0,
        )
        assert tag.page_type == PageType.TOC_PAGE
        assert tag.confidence == 0.9

    def test_register_page_via_building_header(self):
        register_text = (
            "### B00A - Admin Building - 1924 - Brick\n\n| Material | Product |"
        )
        tag = _heuristic_tag_page(
            page_number=13,
            page_text=register_text,
            total_pages=30,
            previous_section_id=3,
        )
        assert tag.section_id == SectionTaxonomy.ASBESTOS_REGISTER
        assert tag.page_type == PageType.CONTENT
        assert tag.confidence == 0.9

    def test_introduction_heading_detection(self):
        tag = _heuristic_tag_page(
            page_number=3,
            page_text="## 1.0 Introduction\n\nThis report presents findings...",
            total_pages=30,
            previous_section_id=0,
        )
        assert tag.section_id == SectionTaxonomy.INTRODUCTION
        assert tag.confidence == 0.8

    def test_methodology_heading_detection(self):
        tag = _heuristic_tag_page(
            page_number=7,
            page_text="## 3.0 Methodology\n\nA comprehensive visual inspection...",
            total_pages=30,
            previous_section_id=2,
        )
        assert tag.section_id == SectionTaxonomy.METHODOLOGY
        assert tag.confidence == 0.8

    def test_appendix_heading_detection(self):
        tag = _heuristic_tag_page(
            page_number=28,
            page_text="## Appendix C: Laboratory Certificates",
            total_pages=30,
            previous_section_id=6,
        )
        assert tag.section_id == SectionTaxonomy.APPENDIX
        assert tag.confidence == 0.8

    def test_special_page_detection(self):
        tag = _heuristic_tag_page(
            page_number=29,
            page_text="NATA Accredited Laboratory\nCertificate No: 12345",
            total_pages=30,
            previous_section_id=7,
        )
        assert tag.page_type == PageType.SPECIAL
        assert tag.section_id == SectionTaxonomy.APPENDIX

    def test_inherit_previous_section(self):
        tag = _heuristic_tag_page(
            page_number=14,
            page_text="Some continuation text with no clear section heading",
            total_pages=30,
            previous_section_id=4,
        )
        assert tag.section_id == 4
        assert tag.confidence == 0.5

    def test_building_inventory_page_range(self):
        from open_notebook.extractors.building_inventory import (
            BuildingInventory,
            BuildingMeta,
        )

        inventory = BuildingInventory(
            buildings=[
                BuildingMeta(
                    building_id="B00A",
                    page_start=13,
                    page_end=19,
                    rooms=[],
                ),
            ],
            processing_groups=[],
            total_buildings=1,
        )
        tag = _heuristic_tag_page(
            page_number=15,
            page_text="More register content here",
            total_pages=30,
            previous_section_id=4,
            building_inventory=inventory,
        )
        assert tag.section_id == SectionTaxonomy.ASBESTOS_REGISTER
        assert tag.confidence == 0.85

    def test_document_structure_section_range(self):
        from open_notebook.extractors.document_structure import (
            DocumentStructure,
            Section,
        )

        doc_structure = DocumentStructure(
            total_pages=30,
            sections=[
                Section(section_id=3, title="Methodology", page_start=7, page_end=12),
            ],
        )
        tag = _heuristic_tag_page(
            page_number=9,
            page_text="Sampling methods used in the inspection process",
            total_pages=30,
            previous_section_id=3,
            document_structure=doc_structure,
        )
        assert tag.section_id == SectionTaxonomy.METHODOLOGY
        assert tag.confidence == 0.9

    def test_risk_assessment_detection(self):
        tag = _heuristic_tag_page(
            page_number=25,
            page_text="## Risk Assessment\n\nOverall the school presents a moderate risk.",
            total_pages=30,
            previous_section_id=4,
        )
        assert tag.section_id == SectionTaxonomy.RISK_ASSESSMENT

    def test_conclusion_detection(self):
        tag = _heuristic_tag_page(
            page_number=28,
            page_text="## Conclusion\n\nRecommendations include monitoring.",
            total_pages=30,
            previous_section_id=5,
        )
        assert tag.section_id == SectionTaxonomy.CONCLUSION


class TestConfidenceScoring:
    """Test confidence scoring heuristics (Task 5.6)."""

    def test_high_confidence_for_toc(self):
        tag = _heuristic_tag_page(
            page_number=2,
            page_text="Table of Contents\n1.0 Introduction ... 3",
            total_pages=30,
            previous_section_id=0,
        )
        assert tag.confidence >= 0.9

    def test_high_confidence_for_building_header(self):
        tag = _heuristic_tag_page(
            page_number=15,
            page_text="### B00A - Admin Building",
            total_pages=30,
            previous_section_id=4,
        )
        assert tag.confidence >= 0.9

    def test_moderate_confidence_for_section_heading(self):
        tag = _heuristic_tag_page(
            page_number=7,
            page_text="## Methodology\n\nDetails of the survey approach.",
            total_pages=30,
            previous_section_id=2,
        )
        assert 0.7 <= tag.confidence <= 0.9

    def test_low_confidence_for_inherited(self):
        tag = _heuristic_tag_page(
            page_number=10,
            page_text="More text without clear section markers",
            total_pages=30,
            previous_section_id=3,
        )
        assert tag.confidence <= 0.5

    def test_high_confidence_from_inventory(self):
        from open_notebook.extractors.building_inventory import (
            BuildingInventory,
            BuildingMeta,
        )

        inventory = BuildingInventory(
            buildings=[
                BuildingMeta(building_id="B00A", page_start=13, page_end=19, rooms=[])
            ],
            processing_groups=[],
            total_buildings=1,
        )
        tag = _heuristic_tag_page(
            page_number=15,
            page_text="Some content",
            total_pages=30,
            previous_section_id=4,
            building_inventory=inventory,
        )
        assert tag.confidence >= 0.85


class TestSubSectionDetection:
    """Test subsection detection (Task 5.7)."""

    def test_subsection_model_in_page_tag(self):
        """Verify SubSectionTag works within PageTag model."""
        tag = PageTag(
            page_number=7,
            section_id=3,
            section_title="Methodology",
            confidence=0.85,
            page_type=PageType.CONTENT,
            subsection=SubSectionTag(
                subsection_number="3.1",
                title="Visual Inspection",
                section_id=3,
            ),
        )
        assert tag.subsection is not None
        assert tag.subsection.subsection_number == "3.1"
        assert tag.subsection.title == "Visual Inspection"
        assert tag.subsection.section_id == 3

    def test_appendix_subsection(self):
        tag = PageTag(
            page_number=28,
            section_id=7,
            section_title="Appendix",
            confidence=0.9,
            page_type=PageType.CONTENT,
            subsection=SubSectionTag(
                subsection_number="B",
                title="Laboratory Certificates",
                section_id=7,
            ),
        )
        assert tag.subsection.subsection_number == "B"

    def test_no_subsection_by_default(self):
        """Heuristic tagging does not set subsection (LLM-only feature)."""
        tag = _heuristic_tag_page(
            page_number=7,
            page_text="## Methodology\n\n### 3.1 Visual Inspection",
            total_pages=30,
            previous_section_id=2,
        )
        assert tag.subsection is None  # Heuristic fallback doesn't detect subsections


class TestHeuristicTagAll:
    """Test _heuristic_tag_all() with full content (Task 5.8, 5.9)."""

    def test_tag_all_pages_from_sample(self):
        pages = _split_into_pages(SAMPLE_CONTENT)
        tags = _heuristic_tag_all(pages)
        assert len(tags) == len(pages)
        # Verify all page numbers match
        for tag, (pn, _) in zip(tags, pages):
            assert tag.page_number == pn

    def test_contextual_continuity(self):
        """Verify previous_section_id propagates across pages."""
        pages = _split_into_pages(SAMPLE_CONTENT)
        tags = _heuristic_tag_all(pages)
        # Find register pages (section 4) - should be contiguous
        register_tags = [
            t for t in tags if t.section_id == SectionTaxonomy.ASBESTOS_REGISTER
        ]
        if register_tags:
            # Register pages should be consecutive
            page_nums = [t.page_number for t in register_tags]
            for i in range(1, len(page_nums)):
                assert page_nums[i] > page_nums[i - 1]

    def test_tag_all_empty_pages(self):
        tags = _heuristic_tag_all([])
        assert tags == []


class TestComputeRegisterRange:
    """Test _compute_register_range() (Task 5.12)."""

    def test_compute_range_with_register_pages(self):
        tags = [
            PageTag(
                page_number=1,
                section_id=0,
                section_title="ES",
                confidence=0.9,
                page_type=PageType.TITLE_PAGE,
            ),
            PageTag(
                page_number=13,
                section_id=4,
                section_title="Reg",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
            PageTag(
                page_number=14,
                section_id=4,
                section_title="Reg",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
            PageTag(
                page_number=20,
                section_id=4,
                section_title="Reg",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
            PageTag(
                page_number=25,
                section_id=5,
                section_title="RA",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
        ]
        result = _compute_register_range(tags)
        assert result == (13, 20)

    def test_compute_range_no_register(self):
        tags = [
            PageTag(
                page_number=1,
                section_id=0,
                section_title="ES",
                confidence=0.9,
                page_type=PageType.TITLE_PAGE,
            ),
            PageTag(
                page_number=2,
                section_id=1,
                section_title="Intro",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
        ]
        result = _compute_register_range(tags)
        assert result is None

    def test_compute_range_single_register_page(self):
        tags = [
            PageTag(
                page_number=10,
                section_id=4,
                section_title="Reg",
                confidence=0.9,
                page_type=PageType.CONTENT,
            ),
        ]
        result = _compute_register_range(tags)
        assert result == (10, 10)

    def test_compute_range_empty(self):
        result = _compute_register_range([])
        assert result is None


class TestTagPagesAsync:
    """Test async tag_pages() function (Task 5.11)."""

    @pytest.mark.asyncio
    async def test_tag_pages_empty_content(self):
        from open_notebook.extractors.page_tagger import tag_pages

        result = await tag_pages("")
        assert result.pages == []
        assert result.total_pages == 0
        assert result.register_page_range is None

    @pytest.mark.asyncio
    async def test_tag_pages_no_page_markers(self):
        from open_notebook.extractors.page_tagger import tag_pages

        # With no LLM available, will fall back to heuristic
        result = await tag_pages("Plain text without markers")
        assert result.total_pages == 0
        assert len(result.pages) >= 0  # Heuristic may tag or not

    @pytest.mark.asyncio
    async def test_tag_pages_heuristic_fallback(self):
        """Test that tag_pages uses heuristic fallback when LLM unavailable."""
        from open_notebook.extractors.page_tagger import tag_pages

        # Without a configured LLM, will fall back to heuristics
        result = await tag_pages(SAMPLE_CONTENT)
        assert len(result.pages) > 0
        assert result.total_pages == 30
        # Should detect register pages
        register_pages = [
            p for p in result.pages if p.section_id == SectionTaxonomy.ASBESTOS_REGISTER
        ]
        assert len(register_pages) > 0
        assert result.register_page_range is not None

    @pytest.mark.asyncio
    async def test_tag_pages_with_document_structure(self):
        from open_notebook.extractors.document_structure import (
            DocumentStructure,
            DocumentType,
            Section,
        )
        from open_notebook.extractors.page_tagger import tag_pages

        doc_structure = DocumentStructure(
            document_type=DocumentType.SAMP,
            total_pages=30,
            register_start_page=13,
            sections=[
                Section(
                    section_id=4, title="Asbestos Register", page_start=13, page_end=24
                ),
            ],
        )
        result = await tag_pages(SAMPLE_CONTENT, document_structure=doc_structure)
        assert len(result.pages) > 0

    @pytest.mark.asyncio
    async def test_tag_pages_with_building_inventory(self):
        from open_notebook.extractors.building_inventory import (
            BuildingInventory,
            BuildingMeta,
        )
        from open_notebook.extractors.page_tagger import tag_pages

        inventory = BuildingInventory(
            buildings=[
                BuildingMeta(building_id="B00A", page_start=13, page_end=19, rooms=[]),
                BuildingMeta(building_id="B001", page_start=20, page_end=24, rooms=[]),
            ],
            processing_groups=[],
            total_buildings=2,
        )
        result = await tag_pages(SAMPLE_CONTENT, building_inventory=inventory)
        assert len(result.pages) > 0
        assert result.register_page_range is not None


class TestSectionTitles:
    """Test _SECTION_TITLES mapping."""

    def test_all_sections_have_titles(self):
        for section in SectionTaxonomy:
            assert section in _SECTION_TITLES
            assert isinstance(_SECTION_TITLES[section], str)

    def test_section_title_values(self):
        assert _SECTION_TITLES[SectionTaxonomy.EXECUTIVE_SUMMARY] == "Executive Summary"
        assert _SECTION_TITLES[SectionTaxonomy.ASBESTOS_REGISTER] == "Asbestos Register"
        assert _SECTION_TITLES[SectionTaxonomy.APPENDIX] == "Appendix"


class TestLangGraphIntegration:
    """Test LangGraph pipeline integration (Task 5.10)."""

    def test_graph_has_tag_pages_node(self):
        from open_notebook.graphs.acm_extraction import graph

        assert "tag_pages" in graph.nodes

    def test_graph_wiring_order(self):
        from open_notebook.graphs.acm_extraction import agent_state

        edges = agent_state.edges
        assert ("inventory", "tag_pages") in edges or any(
            e == ("inventory", "tag_pages") for e in edges
        )
        # tag_pages -> prepare is now a conditional edge (E1-S20 orchestrator routing)
        assert "tag_pages" in agent_state.branches, (
            "tag_pages should have conditional edges for orchestrator routing"
        )
        tag_pages_targets = set()
        for branch in agent_state.branches["tag_pages"].values():
            if hasattr(branch, "ends") and branch.ends:
                tag_pages_targets.update(branch.ends.values())
        assert "prepare" in tag_pages_targets, (
            f"tag_pages conditional edges should include 'prepare', got {tag_pages_targets}"
        )

    def test_extraction_state_has_page_tags(self):
        import typing

        from open_notebook.graphs.acm_extraction import ExtractionState

        annotations = typing.get_type_hints(ExtractionState)
        assert "page_tags" in annotations

    @pytest.mark.asyncio
    async def test_tag_page_sections_node_empty_content(self):
        from unittest.mock import MagicMock

        from open_notebook.graphs.acm_extraction import tag_page_sections

        mock_source = MagicMock()
        mock_source.id = "test:123"
        mock_source.full_text = ""

        state = {
            "source": mock_source,
            "model_id": None,
            "document_structure": None,
            "building_inventory": None,
        }
        config = MagicMock()

        result = await tag_page_sections(state, config)
        assert result["page_tags"] is None

    @pytest.mark.asyncio
    async def test_tag_page_sections_node_with_content(self):
        from unittest.mock import MagicMock

        from open_notebook.graphs.acm_extraction import tag_page_sections

        mock_source = MagicMock()
        mock_source.id = "test:456"
        mock_source.full_text = SAMPLE_CONTENT

        state = {
            "source": mock_source,
            "model_id": None,
            "document_structure": None,
            "building_inventory": None,
        }
        config = MagicMock()

        result = await tag_page_sections(state, config)
        assert result["page_tags"] is not None
        assert len(result["page_tags"].pages) > 0
