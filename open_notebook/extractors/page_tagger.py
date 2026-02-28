"""
Page-Level Section Tagging.

Tags each page with its section classification and confidence score
using the standardized 0-7 taxonomy. Runs as Stage -1.25 (between
Inventory and Prepare) in the LangGraph extraction pipeline.

Story: E1-S18 Page-Level Section Tagging
"""

import re
from enum import Enum, IntEnum
from typing import List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.extractors.building_inventory import BuildingInventory
from open_notebook.extractors.document_structure import (
    _PAGE_PATTERN,
    DocumentStructure,
    _extract_total_pages,
    _page_num_from_match,
)


class SectionTaxonomy(IntEnum):
    """Standardized section taxonomy (0-7) for ACM documents (Task 1.1)."""

    EXECUTIVE_SUMMARY = 0
    INTRODUCTION = 1
    SITE_DESCRIPTION = 2
    METHODOLOGY = 3
    ASBESTOS_REGISTER = 4
    RISK_ASSESSMENT = 5
    CONCLUSION = 6
    APPENDIX = 7


# Human-readable section titles
_SECTION_TITLES = {
    SectionTaxonomy.EXECUTIVE_SUMMARY: "Executive Summary",
    SectionTaxonomy.INTRODUCTION: "Introduction",
    SectionTaxonomy.SITE_DESCRIPTION: "Site Description",
    SectionTaxonomy.METHODOLOGY: "Methodology",
    SectionTaxonomy.ASBESTOS_REGISTER: "Asbestos Register",
    SectionTaxonomy.RISK_ASSESSMENT: "Risk Assessment",
    SectionTaxonomy.CONCLUSION: "Conclusion",
    SectionTaxonomy.APPENDIX: "Appendix",
}


class PageType(str, Enum):
    """Page type classification (Task 1.2)."""

    TITLE_PAGE = "title_page"
    TOC_PAGE = "toc_page"
    CONTENT = "content"
    SPECIAL = "special"


class SubSectionTag(BaseModel):
    """A subsection tag within a page (Task 1.3)."""

    subsection_number: str
    title: str
    section_id: int = Field(description="Section ID (0-7)")


class PageTag(BaseModel):
    """Tag metadata for a single page (Task 1.4)."""

    page_number: int
    section_id: int = Field(description="Section ID (0-7)")
    section_title: str
    confidence: float = Field(description="Confidence score 0.0-1.0")
    page_type: PageType
    subsection: Optional[SubSectionTag] = None
    content_summary: Optional[str] = None


class PageTagBatch(BaseModel):
    """LLM output for a batch of pages."""

    pages: List[PageTag]


class PageTaggingResult(BaseModel):
    """Aggregated page tagging result (Task 1.5)."""

    pages: List[PageTag]
    total_pages: int
    register_page_range: Optional[Tuple[int, int]] = None


# --- Page splitting (Task 3.3) ---


def _split_into_pages(content: str) -> List[Tuple[int, str]]:
    """Split content into (page_number, page_text) tuples.

    Uses _PAGE_PATTERN from document_structure.py to find page boundaries.
    Each page's text runs from its marker to the next marker (or end of content).
    """
    matches = list(_PAGE_PATTERN.finditer(content))
    if not matches:
        return [(1, content)]

    pages = []
    for i, match in enumerate(matches):
        page_num = _page_num_from_match(match)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        page_text = content[start:end].strip()
        if page_text:
            pages.append((page_num, page_text))
    return pages


# --- Batching (Task 3.4) ---

_BATCH_SIZE = 5  # Default batch size (3-5 pages per LLM call)


def _create_batches(
    pages: List[Tuple[int, str]], batch_size: int = _BATCH_SIZE
) -> List[List[Tuple[int, str]]]:
    """Create batches of pages for LLM processing."""
    return [pages[i : i + batch_size] for i in range(0, len(pages), batch_size)]


# --- Heuristic fallback (Task 3.7) ---

# Section heading patterns for heuristic detection
_SECTION_PATTERNS = {
    SectionTaxonomy.INTRODUCTION: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?introduction",
        re.IGNORECASE,
    ),
    SectionTaxonomy.SITE_DESCRIPTION: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?site\s+description",
        re.IGNORECASE,
    ),
    SectionTaxonomy.METHODOLOGY: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?methodology",
        re.IGNORECASE,
    ),
    SectionTaxonomy.RISK_ASSESSMENT: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?risk\s+assessment",
        re.IGNORECASE,
    ),
    SectionTaxonomy.CONCLUSION: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?conclusion",
        re.IGNORECASE,
    ),
    SectionTaxonomy.APPENDIX: re.compile(
        r"(?:^|\n)\s*#+\s*(?:\d+\.?\d*\s+)?appendix",
        re.IGNORECASE,
    ),
}

_TOC_PATTERN = re.compile(
    r"(?:table\s+of\s+contents|contents)\s*\n",
    re.IGNORECASE,
)

_BUILDING_HEADER_PATTERN = re.compile(
    r"\b[BD]\d{2,3}[A-Z]?\s*[-–]",
)

_SPECIAL_PATTERNS = re.compile(
    r"(?:laboratory|certificate|NATA|site\s+plan|photograph)",
    re.IGNORECASE,
)


def _heuristic_tag_page(
    page_number: int,
    page_text: str,
    total_pages: int,
    previous_section_id: int,
    document_structure: Optional[DocumentStructure] = None,
    building_inventory: Optional[BuildingInventory] = None,
) -> PageTag:
    """Tag a single page using heuristic regex patterns (Task 3.7).

    Used as fallback when LLM is unavailable.
    """
    text_lower = page_text.lower()

    # Check if page falls within known building inventory page ranges
    if building_inventory:
        for b in building_inventory.buildings:
            if b.page_start <= page_number <= (b.page_end or b.page_start):
                return PageTag(
                    page_number=page_number,
                    section_id=SectionTaxonomy.ASBESTOS_REGISTER,
                    section_title=_SECTION_TITLES[SectionTaxonomy.ASBESTOS_REGISTER],
                    confidence=0.85,
                    page_type=PageType.CONTENT,
                )

    # Check if page falls within known section ranges from DocumentStructure
    if document_structure and document_structure.sections:
        for section in document_structure.sections:
            if (
                section.page_start
                <= page_number
                <= (section.page_end or section.page_start)
            ):
                return PageTag(
                    page_number=page_number,
                    section_id=section.section_id,
                    section_title=_SECTION_TITLES.get(
                        SectionTaxonomy(section.section_id),
                        section.title,
                    ),
                    confidence=0.9,
                    page_type=PageType.CONTENT,
                )

    # TOC page (check before title page since TOC can be on page 2)
    if _TOC_PATTERN.search(page_text):
        return PageTag(
            page_number=page_number,
            section_id=SectionTaxonomy.EXECUTIVE_SUMMARY,
            section_title=_SECTION_TITLES[SectionTaxonomy.EXECUTIVE_SUMMARY],
            confidence=0.9,
            page_type=PageType.TOC_PAGE,
        )

    # Title page: first 1-2 pages with no strong section markers
    if page_number <= 2:
        has_section_heading = any(
            p.search(page_text) for p in _SECTION_PATTERNS.values()
        )
        if not has_section_heading:
            return PageTag(
                page_number=page_number,
                section_id=SectionTaxonomy.EXECUTIVE_SUMMARY,
                section_title=_SECTION_TITLES[SectionTaxonomy.EXECUTIVE_SUMMARY],
                confidence=0.7,
                page_type=PageType.TITLE_PAGE,
            )

    # Check for section heading patterns (before special/building checks)
    for section_id, pattern in _SECTION_PATTERNS.items():
        if pattern.search(page_text):
            return PageTag(
                page_number=page_number,
                section_id=section_id,
                section_title=_SECTION_TITLES[section_id],
                confidence=0.8,
                page_type=PageType.CONTENT,
            )

    # Building headers indicate register section
    if _BUILDING_HEADER_PATTERN.search(page_text):
        return PageTag(
            page_number=page_number,
            section_id=SectionTaxonomy.ASBESTOS_REGISTER,
            section_title=_SECTION_TITLES[SectionTaxonomy.ASBESTOS_REGISTER],
            confidence=0.9,
            page_type=PageType.CONTENT,
        )

    # Special pages (lab certificates, site plans - no section heading detected)
    if _SPECIAL_PATTERNS.search(page_text):
        return PageTag(
            page_number=page_number,
            section_id=SectionTaxonomy.APPENDIX,
            section_title=_SECTION_TITLES[SectionTaxonomy.APPENDIX],
            confidence=0.7,
            page_type=PageType.SPECIAL,
        )

    # Default: inherit previous section
    sid = (
        SectionTaxonomy(previous_section_id)
        if 0 <= previous_section_id <= 7
        else SectionTaxonomy.EXECUTIVE_SUMMARY
    )
    return PageTag(
        page_number=page_number,
        section_id=sid,
        section_title=_SECTION_TITLES[sid],
        confidence=0.5,
        page_type=PageType.CONTENT,
    )


def _heuristic_tag_all(
    pages: List[Tuple[int, str]],
    document_structure: Optional[DocumentStructure] = None,
    building_inventory: Optional[BuildingInventory] = None,
) -> List[PageTag]:
    """Tag all pages using heuristics (fallback path)."""
    total_pages = max(pn for pn, _ in pages) if pages else 0
    tagged: List[PageTag] = []
    previous_section_id = 0

    for page_num, page_text in pages:
        tag = _heuristic_tag_page(
            page_num,
            page_text,
            total_pages,
            previous_section_id,
            document_structure,
            building_inventory,
        )
        tagged.append(tag)
        previous_section_id = tag.section_id

    return tagged


# --- LLM-based tagging (Task 3.5, 3.6, 3.8) ---


async def _llm_tag_batch(
    batch: List[Tuple[int, str]],
    previous_section_id: int,
    document_type: Optional[str] = None,
    model_id: Optional[str] = None,
) -> List[PageTag]:
    """Tag a batch of pages using LLM with structured output (Task 3.5)."""
    from ai_prompter import Prompter
    from langchain_core.messages import HumanMessage, SystemMessage

    from open_notebook.graphs.utils import provision_langchain_model

    # Prepare batch data for the template
    batch_pages = [{"page_number": pn, "text": text} for pn, text in batch]

    prompter = Prompter(prompt_template="acm/page_tagging")
    system_prompt = prompter.render(
        data={
            "batch_pages": batch_pages,
            "previous_section_id": previous_section_id,
            "document_type": document_type,
        }
    )

    # Concatenate batch text for model provisioning (token estimation)
    batch_text = "\n".join(text for _, text in batch)

    # TODO: Use model.get_max_output_tokens() when Model domain object is available here
    model = await provision_langchain_model(
        batch_text,
        model_id,
        "extraction",
        temperature=0.1,
        max_tokens=2048,
    )

    from open_notebook.graphs.utils import _unwrap_completion_state, parse_json_response

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Classify each page into its document section."),
    ]

    raw_response = await model.ainvoke(messages)
    response_text = (
        raw_response.content
        if hasattr(raw_response, "content")
        else str(raw_response)
    )
    parsed = parse_json_response(response_text)
    parsed = _unwrap_completion_state(parsed)
    result = PageTagBatch.model_validate(parsed)
    return result.pages


# --- Compute register page range (Task 3.9) ---


def _compute_register_range(tags: List[PageTag]) -> Optional[Tuple[int, int]]:
    """Compute the register page range from tagged pages (Task 3.9)."""
    register_pages = [
        t.page_number for t in tags if t.section_id == SectionTaxonomy.ASBESTOS_REGISTER
    ]
    if not register_pages:
        return None
    return (min(register_pages), max(register_pages))


# --- Main entry point (Task 3) ---


async def tag_pages(
    content: str,
    document_structure: Optional[DocumentStructure] = None,
    building_inventory: Optional[BuildingInventory] = None,
    model_id: Optional[str] = None,
) -> PageTaggingResult:
    """Tag each page with section classification and confidence score.

    Args:
        content: Full document markdown content with page markers.
        document_structure: Optional DocumentStructure from E1-S16.
        building_inventory: Optional BuildingInventory from E1-S17.
        model_id: Optional model ID override for LLM.

    Returns:
        PageTaggingResult with per-page tags, total pages, and register range.
    """
    if not content:
        logger.warning("Empty content provided for page tagging")
        return PageTaggingResult(pages=[], total_pages=0)

    # Split content into pages
    pages = _split_into_pages(content)
    total_pages = _extract_total_pages(content)

    if not pages:
        logger.warning("No pages found in content")
        return PageTaggingResult(pages=[], total_pages=total_pages)

    # Determine document type from DocumentStructure
    document_type = None
    if document_structure and document_structure.document_type:
        document_type = document_structure.document_type.value

    # Try LLM-based tagging with batch processing
    try:
        batches = _create_batches(pages)
        all_tags: List[PageTag] = []
        previous_section_id = 0

        for batch in batches:
            batch_tags = await _llm_tag_batch(
                batch,
                previous_section_id,
                document_type,
                model_id,
            )
            all_tags.extend(batch_tags)
            # Track previous section for contextual continuity
            if batch_tags:
                previous_section_id = batch_tags[-1].section_id

        register_range = _compute_register_range(all_tags)
        logger.info(
            f"Page tagging complete: {len(all_tags)} pages tagged, "
            f"register_range={register_range}"
        )
        return PageTaggingResult(
            pages=all_tags,
            total_pages=total_pages,
            register_page_range=register_range,
        )

    except Exception as e:
        logger.warning(f"LLM page tagging failed: {e}. Using heuristic fallback.")
        fallback_tags = _heuristic_tag_all(
            pages,
            document_structure,
            building_inventory,
        )
        register_range = _compute_register_range(fallback_tags)
        return PageTaggingResult(
            pages=fallback_tags,
            total_pages=total_pages,
            register_page_range=register_range,
        )
