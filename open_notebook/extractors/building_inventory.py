"""
Building Inventory Compilation.

Compiles a building-level inventory with page locations, room codes,
complexity classification, and processing groups from document content.
Runs as Stage -1.5 (between Structure and Per-Building Extraction)
in the LangGraph extraction pipeline.

Story: E1-S17 Building Inventory Compilation
"""

import re
from enum import Enum
from typing import List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.extractors.document_structure import (
    _PAGE_PATTERN,
    DocumentStructure,
    _extract_total_pages,
)

# Building header pattern: matches "## B00A - Admin Building - 1924 - Brick"
# but NOT room lines like "#### B00A-R0001 - External Movement"
# Key: requires space-dash after building ID (not hyphen-R for rooms)
_BUILDING_HEADER = re.compile(
    r"^#+\s*(?:Building[:\s]*)?([A-Z]\d+[A-Z]?|D\d{2,3})\s+[-–]\s+([^-–\n]+?)(?:\s*[-–]\s*(\d{4}))?(?:\s*[-–]\s*([^-–\n]+?))?$",
    re.IGNORECASE | re.MULTILINE,
)

# Room header pattern: requires BuildingID-R#### format
_ROOM_HEADER = re.compile(
    r"^#+\s*([A-Z0-9]+-R\d{3,5})\s*[-–]\s*([^-–\n]+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?$",
    re.IGNORECASE | re.MULTILINE,
)


class BuildingComplexity(str, Enum):
    """Building complexity classification (Task 1.1)."""

    SIMPLE = "simple"
    COMPLEX = "complex"


class RoomMeta(BaseModel):
    """Room metadata within a building (Task 1.2)."""

    room_id: str
    name: str
    area_m2: Optional[float] = None
    page: Optional[int] = None


class BuildingMeta(BaseModel):
    """Building metadata with page ranges and complexity (Task 1.3)."""

    building_id: str
    name: Optional[str] = None
    year: Optional[int] = None
    construction: Optional[str] = None
    purpose: Optional[str] = None
    area_m2: Optional[float] = None
    levels: Optional[int] = None
    page_start: int
    page_end: Optional[int] = None
    complexity: BuildingComplexity = BuildingComplexity.COMPLEX
    rooms: List[RoomMeta] = Field(default_factory=list)
    acm_item_count_estimate: Optional[int] = None


class ProcessingGroup(BaseModel):
    """A group of buildings for batched extraction (Task 1.4)."""

    group_id: int
    building_ids: List[str]
    page_start: int
    page_end: int
    estimated_pages: int


class BuildingInventory(BaseModel):
    """Aggregated building inventory for the extraction pipeline (Task 1.5)."""

    buildings: List[BuildingMeta]
    processing_groups: List[ProcessingGroup]
    total_buildings: int
    document_type: Optional[str] = None


# Building-level no-asbestos declarations (NOT individual row results)
_NO_ASBESTOS_MARKERS = [
    "no asbestos containing materials found",
    "no asbestos",
    "no acm",
]


def _find_page_at_position(content: str, position: int) -> int:
    """Find the page number at a given character position in content."""
    page = 1
    for match in _PAGE_PATTERN.finditer(content):
        if match.start() <= position:
            page = int(match.group(1))
        else:
            break
    return page


def _get_building_section(
    content: str, building_start: int, next_building_start: Optional[int]
) -> str:
    """Extract the text section belonging to a building."""
    end = next_building_start if next_building_start is not None else len(content)
    return content[building_start:end]


def _classify_complexity(
    section_text: str, room_count: int
) -> Tuple[BuildingComplexity, int]:
    """Classify building complexity based on content indicators.

    Returns:
        Tuple of (complexity, acm_item_count_estimate).
    """
    lower = section_text.lower()
    for marker in _NO_ASBESTOS_MARKERS:
        if marker in lower:
            return BuildingComplexity.SIMPLE, 0
    # Count ACM product indicators (positive detections only)
    acm_count = lower.count("detected") - lower.count("not detected")
    acm_count = max(acm_count, 0)
    if room_count >= 2:
        return BuildingComplexity.COMPLEX, acm_count
    if acm_count < 3:
        return BuildingComplexity.SIMPLE, acm_count
    return BuildingComplexity.COMPLEX, acm_count


def _extract_rooms_from_section(
    section_text: str, content_start: int, full_content: str
) -> List[RoomMeta]:
    """Extract room metadata from a building section."""
    rooms: List[RoomMeta] = []
    for match in _ROOM_HEADER.finditer(section_text):
        room_id = match.group(1)
        room_name = match.group(2).strip()
        area_str = match.group(3)
        area_m2 = float(area_str) if area_str else None

        # Calculate page from position in full content
        abs_pos = content_start + match.start()
        page = _find_page_at_position(full_content, abs_pos)

        rooms.append(RoomMeta(
            room_id=room_id,
            name=room_name,
            area_m2=area_m2,
            page=page,
        ))
    return rooms


def _find_page_end(section_text: str, page_start: int, rooms: List[RoomMeta]) -> int:
    """Find the last page containing building content.

    Uses the highest page from room entries, or the last page marker
    that has non-whitespace content before the next page marker or
    section end (indicating actual building data on that page).
    """
    # If rooms have page info, use the max room page
    if rooms:
        room_pages = [r.page for r in rooms if r.page is not None]
        if room_pages:
            return max(room_pages)

    # Fall back to page markers in the section, but exclude trailing markers
    # with no building content after them
    pages_in_section = []
    for match in _PAGE_PATTERN.finditer(section_text):
        pg = int(match.group(1))
        # Check if there's substantial content after this marker before the next marker
        after_marker = section_text[match.end():]
        next_page = _PAGE_PATTERN.search(after_marker)
        content_after = after_marker[:next_page.start()] if next_page else after_marker
        # Only count if there's real content (not just whitespace)
        if content_after.strip():
            pages_in_section.append(pg)

    if pages_in_section:
        return max(pages_in_section)
    return page_start


def _create_processing_groups(buildings: List[BuildingMeta]) -> List[ProcessingGroup]:
    """Create processing groups targeting 3-5 pages per group (Task 3.6).

    Algorithm:
    1. Sort buildings by page_start ascending
    2. Initialize current group with first building
    3. For each subsequent building:
       a. If adding this building keeps group_pages <= 5: add to current group
       b. Else: finalize current group, start new group
    4. Finalize last group
    """
    if not buildings:
        return []

    sorted_buildings = sorted(buildings, key=lambda b: b.page_start)

    groups: List[ProcessingGroup] = []
    current_ids: List[str] = [sorted_buildings[0].building_id]
    current_start = sorted_buildings[0].page_start
    current_end = sorted_buildings[0].page_end or sorted_buildings[0].page_start

    for building in sorted_buildings[1:]:
        b_end = building.page_end or building.page_start
        potential_pages = b_end - current_start + 1

        if potential_pages <= 5:
            current_ids.append(building.building_id)
            current_end = max(current_end, b_end)
        else:
            # Finalize current group
            groups.append(ProcessingGroup(
                group_id=len(groups) + 1,
                building_ids=current_ids,
                page_start=current_start,
                page_end=current_end,
                estimated_pages=current_end - current_start + 1,
            ))
            current_ids = [building.building_id]
            current_start = building.page_start
            current_end = b_end

    # Finalize last group
    groups.append(ProcessingGroup(
        group_id=len(groups) + 1,
        building_ids=current_ids,
        page_start=current_start,
        page_end=current_end,
        estimated_pages=current_end - current_start + 1,
    ))

    return groups


def _heuristic_fallback(
    content: str,
    document_structure: Optional[DocumentStructure] = None,
) -> BuildingInventory:
    """Heuristic-based building inventory extraction (Task 3.5).

    Uses custom regex patterns (_BUILDING_HEADER, _ROOM_HEADER) to detect
    buildings, rooms, page ranges, and complexity without LLM.
    """
    if not content:
        return BuildingInventory(
            buildings=[], processing_groups=[], total_buildings=0,
        )

    # Find all building headers (B-series and D-series)
    building_matches: List[Tuple[int, re.Match]] = []
    seen_ids: set = set()
    for match in _BUILDING_HEADER.finditer(content):
        bid = match.group(1)
        if bid not in seen_ids:
            building_matches.append((match.start(), match))
            seen_ids.add(bid)

    buildings: List[BuildingMeta] = []
    for i, (pos, match) in enumerate(building_matches):
        building_id = match.group(1)
        name = match.group(2).strip() if match.group(2) else None
        year_str = match.group(3)
        year = int(year_str) if year_str else None
        construction = match.group(4).strip() if match.group(4) else None

        page_start = _find_page_at_position(content, pos)

        # Get section text (up to next building)
        next_pos = building_matches[i + 1][0] if i + 1 < len(building_matches) else None
        section_text = _get_building_section(content, pos, next_pos)

        # Extract rooms
        rooms = _extract_rooms_from_section(section_text, pos, content)

        # Find page end (using room pages for accuracy)
        page_end = _find_page_end(section_text, page_start, rooms)

        # Classify complexity and estimate ACM item count
        complexity, acm_estimate = _classify_complexity(section_text, len(rooms))

        buildings.append(BuildingMeta(
            building_id=building_id,
            name=name,
            year=year,
            construction=construction,
            page_start=page_start,
            page_end=page_end,
            complexity=complexity,
            rooms=rooms,
            acm_item_count_estimate=acm_estimate if acm_estimate > 0 else None,
        ))

    # Create processing groups
    processing_groups = _create_processing_groups(buildings)

    # Determine document type from DocumentStructure if available
    doc_type = None
    if document_structure and document_structure.document_type:
        doc_type = document_structure.document_type.value

    return BuildingInventory(
        buildings=buildings,
        processing_groups=processing_groups,
        total_buildings=len(buildings),
        document_type=doc_type,
    )


async def _llm_compile_inventory(
    content: str,
    model_id: Optional[str] = None,
) -> BuildingInventory:
    """Use LLM with structured output for building inventory compilation (Task 3.3).

    Args:
        content: Document content (trimmed to register section).
        model_id: Optional model ID override.

    Returns:
        BuildingInventory from LLM analysis.
    """
    from ai_prompter import Prompter
    from langchain_core.messages import HumanMessage, SystemMessage

    from open_notebook.graphs.utils import provision_langchain_model

    prompter = Prompter(prompt_template="acm/building_inventory")
    system_prompt = prompter.render(data={"content": content})

    model = await provision_langchain_model(
        content,
        model_id,
        "extraction",
        temperature=0.1,
        max_tokens=4096,
    )

    chain = model.with_structured_output(BuildingInventory)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Compile a building inventory with page ranges, room codes, and complexity classifications."
        ),
    ]
    result: BuildingInventory = await chain.ainvoke(messages)
    return result


def _trim_to_register(
    content: str,
    document_structure: Optional[DocumentStructure],
) -> str:
    """Trim content to register section using DocumentStructure intelligence (Task 3.4)."""
    if not document_structure or not document_structure.register_start_page:
        return content

    page_pattern = re.compile(
        rf"(?:[-—]+|<!--)\s*Page\s+{document_structure.register_start_page}\s*(?:[-—]+|-->)",
        re.IGNORECASE,
    )
    match = page_pattern.search(content)
    if match and match.start() > 500:
        return content[match.start():]
    return content


async def compile_building_inventory(
    content: Optional[str],
    document_structure: Optional[DocumentStructure] = None,
    model_id: Optional[str] = None,
) -> BuildingInventory:
    """Compile a building inventory from document content (Task 3).

    Single-pass extraction: one LLM call per document.
    Falls back to heuristic detection if LLM fails or is unavailable.

    Args:
        content: Full document markdown content.
        document_structure: Optional DocumentStructure from E1-S16.
        model_id: Optional model ID override for LLM.

    Returns:
        BuildingInventory with buildings, rooms, page ranges, and processing groups.
    """
    if not content:
        logger.warning("Empty content provided for building inventory compilation")
        return BuildingInventory(
            buildings=[], processing_groups=[], total_buildings=0,
        )

    # Trim to register section if DocumentStructure available
    register_content = _trim_to_register(content, document_structure)

    try:
        inventory = await _llm_compile_inventory(register_content, model_id)
        # Ensure processing groups are generated
        if not inventory.processing_groups and inventory.buildings:
            inventory.processing_groups = _create_processing_groups(inventory.buildings)
        logger.info(
            f"Building inventory compiled: {inventory.total_buildings} buildings, "
            f"{len(inventory.processing_groups)} processing groups"
        )
        return inventory

    except Exception as e:
        logger.warning(f"LLM building inventory compilation failed: {e}. Using heuristic fallback.")
        fallback = _heuristic_fallback(register_content, document_structure)
        return fallback
