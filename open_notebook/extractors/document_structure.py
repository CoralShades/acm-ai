"""
Document Structure & TOC Extraction.

Extracts document structure, table of contents, and hierarchical page mapping
from SAMP/BAR PDF documents. Runs as Stage -1 (pre-extraction intelligence)
in the LangGraph extraction pipeline.

Story: E1-S16 Document Structure & TOC Extraction
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document type classification (Task 1.1)."""

    SAMP = "SAMP"
    ARA = "ARA"
    DIVISION_5 = "Division_5"
    UNKNOWN = "Unknown"


class SubSection(BaseModel):
    """A subsection within a document section (Task 1.3)."""

    subsection_number: str
    title: str
    page_start: int
    page_end: Optional[int] = None


class Section(BaseModel):
    """A document section following the standardized 0-7 taxonomy (Task 1.2).

    Section IDs:
        0: Executive Summary
        1: Introduction
        2: Site Description
        3: Methodology
        4: Asbestos Register (TARGET SECTION)
        5: Risk Assessment
        6: Conclusion
        7: Appendix
    """

    section_id: int = Field(ge=0, le=7)
    title: str
    page_start: int
    page_end: Optional[int] = None
    subsections: List[SubSection] = Field(default_factory=list)


class DocumentStructure(BaseModel):
    """Aggregated document structure model (Task 1.4).

    Transient Pydantic model that flows through ExtractionState,
    NOT persisted to database.
    """

    document_type: DocumentType = DocumentType.UNKNOWN
    toc_present: bool = False
    total_pages: int = 0
    register_start_page: Optional[int] = None
    building_ids: List[str] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentStructureLLM(BaseModel):
    """LLM-friendly version of DocumentStructure without Dict fields.

    Azure OpenAI strict mode rejects Dict[str, Any] fields. This slim model
    excludes `metadata` for LLM structured output.
    """

    document_type: DocumentType = DocumentType.UNKNOWN
    toc_present: bool = False
    total_pages: int = 0
    register_start_page: Optional[int] = None
    building_ids: List[str] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)


# Page marker pattern — matches multiple PDF-to-text formats:
# 1. Dash format: "--- Page 5 ---" or "——— Page 5 ———"
# 2. HTML comment format: "<!-- Page 5 -->"
# 3. ARA footer format: "PAGE 8 OF 34" (Greencap, Prensa, etc.)
_PAGE_PATTERN = re.compile(
    r"(?:[-—]+|<!--)\s*Page\s+(\d+)\s*(?:[-—]+|-->)|PAGE\s+(\d+)\s+OF\s+\d+",
    re.IGNORECASE,
)


def _page_num_from_match(match: re.Match) -> int:
    """Extract the page number from a _PAGE_PATTERN match (handles multiple groups)."""
    return int(next(g for g in match.groups() if g is not None))


def _extract_total_pages(content: str) -> int:
    """Extract total page count from page markers in content."""
    max_page = 0
    for match in _PAGE_PATTERN.finditer(content):
        page_num = _page_num_from_match(match)
        if page_num > max_page:
            max_page = page_num
    return max_page


async def _llm_extract_structure(
    content: str,
    model_id: Optional[str] = None,
) -> DocumentStructure:
    """Use LLM with structured output for TOC/structure analysis (Task 3.2).

    Args:
        content: Full document markdown content.
        model_id: Optional model ID override.

    Returns:
        DocumentStructure from LLM analysis.
    """
    from ai_prompter import Prompter
    from langchain_core.messages import HumanMessage, SystemMessage

    from open_notebook.graphs.utils import provision_langchain_model

    prompter = Prompter(prompt_template="acm/structure_extraction")
    system_prompt = prompter.render(data={"content": content})

    # TODO: Use model.get_max_output_tokens() when Model domain object is available here
    model = await provision_langchain_model(
        content,
        model_id,
        "extraction",
        temperature=0.1,
        max_tokens=4096,
    )

    chain = model.with_structured_output(DocumentStructureLLM)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Extract the document structure, table of contents, and section hierarchy."
        ),
    ]
    llm_result: DocumentStructureLLM = await chain.ainvoke(messages)
    return DocumentStructure(**llm_result.model_dump())


def _heuristic_fallback(content: str) -> DocumentStructure:
    """Heuristic-based structure detection for documents without TOC (Task 3.4).

    Falls back to regex-based detection when LLM is unavailable or fails.
    """
    total_pages = _extract_total_pages(content)

    # Detect register start page
    register_start = None
    register_markers = [
        "Appendix B: Asbestos Register",
        "Appendix B - Asbestos Register",
        "Asbestos Register",
    ]
    for marker in register_markers:
        idx = content.find(marker)
        if idx != -1:
            # Find nearest preceding page marker
            preceding = content[:idx]
            page_matches = list(_PAGE_PATTERN.finditer(preceding))
            if page_matches:
                register_start = _page_num_from_match(page_matches[-1])
            break

    # Detect building IDs (use set for O(1) dedup, preserve insertion order)
    seen_ids: set[str] = set()
    building_ids: list[str] = []
    building_pattern = re.compile(r"\b(B\d{2,3}[A-Z]?)\b")
    demountable_pattern = re.compile(r"\b(D\d{2,3})\b")
    for match in building_pattern.finditer(content):
        bid = match.group(1)
        if bid not in seen_ids:
            seen_ids.add(bid)
            building_ids.append(bid)
    for match in demountable_pattern.finditer(content):
        bid = match.group(1)
        if bid not in seen_ids:
            seen_ids.add(bid)
            building_ids.append(bid)

    return DocumentStructure(
        document_type=DocumentType.UNKNOWN,
        toc_present=False,
        total_pages=total_pages,
        register_start_page=register_start,
        building_ids=building_ids,
    )


async def extract_document_structure(
    content: Optional[str],
    model_id: Optional[str] = None,
) -> DocumentStructure:
    """Extract document structure from markdown content (Task 3).

    Single-pass extraction: one LLM call per document.
    Falls back to heuristic detection if LLM fails.

    Args:
        content: Full document markdown content.
        model_id: Optional model ID override for LLM.

    Returns:
        DocumentStructure with section hierarchy, building IDs, and metadata.
    """
    if not content:
        logger.warning("Empty content provided for structure extraction")
        return DocumentStructure(
            document_type=DocumentType.UNKNOWN,
            total_pages=0,
        )

    total_pages = _extract_total_pages(content)

    try:
        structure = await _llm_extract_structure(content, model_id)
        # Ensure total_pages is set from page markers (more reliable than LLM estimate)
        if total_pages > 0:
            structure.total_pages = total_pages
        logger.info(
            f"Document structure extracted: type={structure.document_type}, "
            f"pages={structure.total_pages}, sections={len(structure.sections)}, "
            f"buildings={len(structure.building_ids)}, "
            f"register_start={structure.register_start_page}"
        )
        return structure

    except Exception as e:
        logger.warning(
            f"LLM structure extraction failed: {e}. Using heuristic fallback."
        )
        fallback = _heuristic_fallback(content)
        return fallback
