"""
ACM Extraction LangGraph Workflow

AI-powered extraction of Asbestos Containing Material (ACM) records from
PDF documents processed by content-core (PyMuPDF).

Story: E1-S7 AI-Powered ACM Extraction
"""

import asyncio
import hashlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from ai_prompter import Prompter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from loguru import logger
from pydantic import ConfigDict, ValidationError
from typing_extensions import TypedDict

from open_notebook.database.repository import save_source_intelligence
from open_notebook.domain.acm import ACMRecord, ACMTableSection, BuildingRecord
from open_notebook.domain.models import Model
from open_notebook.domain.notebook import Source
from open_notebook.extractors.acm_debug import (
    acm_debug,
    debug_config,
    dump_content_to_file,
    dump_prompt_to_file,
    log_extraction_preview,
    log_prompt_preview,
)
from open_notebook.extractors.acm_schemas import (
    ACMExtractionOutput,
    ACMExtractionRecord,
    ACMExtractionResult,
    BuildingRoomContext,
    ExtractionStatus,
)
from open_notebook.extractors.acm_schemas_v3 import (
    ACMItemExtractionResult,
    BuildingExtractionResult,
)
from open_notebook.extractors.agui_event_emitter import AGUIEventEmitter
from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    compile_building_inventory,
)
from open_notebook.extractors.document_structure import (
    DocumentStructure,
    _extract_total_pages,
    extract_document_structure,
)
from open_notebook.extractors.metadata_extractor import (
    auto_populate_site_config,
    extract_document_metadata,
)
from open_notebook.extractors.normalizers.content import normalize_docling_text
from open_notebook.extractors.normalizers.enums import normalize_enum_value
from open_notebook.extractors.orchestrator import (
    BuildingExtractionPlan,
    ExtractionStrategy,
    OrchestratorStats,
    _extract_building_content,
    _get_docling_tables,
    _inject_docling_tables,
    _normalize_v3_records,
    _v3_extract_building_meta,
    _v3_extract_items,
    orchestrate_extraction,
)
from open_notebook.extractors.page_tagger import (
    PageTaggingResult,
    tag_pages,
)
from open_notebook.extractors.parsers.base import DocumentMeta
from open_notebook.extractors.pipeline_event_bus import (
    AIBuildingExtractedData,
    AIBuildingExtractedEvent,
    AIItemsExtractedData,
    AIItemsExtractedEvent,
    AIValidationCompleteData,
    AIValidationCompleteEvent,
    get_event_bus,
)
from open_notebook.extractors.pipeline_events import StageId
from open_notebook.extractors.pipeline_logger import PipelineLogger
from open_notebook.extractors.token_limit_validator import TokenLimitValidator
from open_notebook.extractors.validators.acm_validator import (
    CorrectionStats,
    validate_acm_record,
)
from open_notebook.graphs.utils import (
    _is_qwen_model,
    _verify_provider_routing,
    is_auth_error,
    parse_json_response,
    provision_extraction_fallback_model,
    provision_langchain_model,
)
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)
from open_notebook.utils import token_count

# Constants
CHUNK_THRESHOLD_RATIO = 0.5  # Chunk if content > 50% of context window
DEFAULT_CONTEXT_WINDOW = 128000  # Fallback used when model capabilities aren't available via Model.get_context_window()
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds

# Chunking constants (for when no page markers exist)
CHARS_PER_TOKEN_ESTIMATE = 4  # Approximate characters per token for chunking
CHUNK_OVERLAP_CHARS = 500  # Overlap between chunks to preserve context


def _extract_acm_register_section(content: str) -> Tuple[str, bool]:
    """
    Extract just the ACM Register section from a document.

    SAMP and ARA documents have boilerplate text before the actual ACM Register.
    This function finds and extracts just the relevant section.

    Returns:
        Tuple of (extracted_content, was_extracted)
    """
    # Look for common markers that indicate start of ACM Register section
    # Use case-insensitive search to handle "ASBESTOS REGISTER" (ARA) and
    # "Asbestos Register" (SAMP) formats
    start_marker_patterns = [
        re.compile(r"Appendix\s+B[:\s-]+Asbestos\s+Register", re.IGNORECASE),
        re.compile(r"Asbestos\s+Register", re.IGNORECASE),
    ]

    # Look for building pattern which indicates start of actual data
    # Supports both SAMP (B###) and ARA (named buildings via "Building Name:")
    building_patterns = [
        re.compile(r"B\d{3}\s*-\s*[A-Za-z]"),
        re.compile(r"Building\s+Name:\s*\S", re.IGNORECASE),
    ]

    start_idx = -1

    # Try to find a good starting point using register markers
    for pattern in start_marker_patterns:
        match = pattern.search(content)
        if match:
            start_idx = match.start()
            break

    # If no marker found, try to find the first building pattern
    if start_idx == -1:
        for pattern in building_patterns:
            match = pattern.search(content)
            if match:
                # Go back a bit to include potential headers
                start_idx = max(0, match.start() - 200)
                break

    if (
        start_idx != -1 and start_idx > 500
    ):  # Only extract if there's significant boilerplate
        extracted = content[start_idx:]
        acm_debug(
            f"Extracted ACM Register section: {len(content)} -> {len(extracted)} chars (saved {len(content) - len(extracted)} chars)"
        )
        return extracted, True

    return content, False


def _detect_document_format(content: str) -> str:
    """Detect whether content is SAMP or ARA format.

    Returns:
        "samp" for B###-style IDs, "ara" for named buildings,
        "unknown" otherwise.
    """
    # Check for SAMP format indicators
    samp_building = re.search(r"B\d{3}\s*-\s*R\d{4}", content)
    if samp_building:
        return "samp"

    # Check for ARA format indicators
    ara_indicators = 0
    if re.search(r"Building Name:\s*\S", content):
        ara_indicators += 1
    if re.search(r"(?:Presumed\s+)?(?:Positive|Negative)\b", content, re.IGNORECASE):
        ara_indicators += 1
    if re.search(
        r"\b(?:Dist\.\s*Potential|Risk Rating|Friability)\b", content, re.IGNORECASE
    ):
        ara_indicators += 1
    # ARA section dividers: "BuildingName - Interior/Exterior - Level"
    if re.search(
        r".+\s*-\s*(?:Interior|Exterior)\s*-\s*(?:Ground|First|Second|Basement)\s+Level",
        content,
        re.IGNORECASE,
    ):
        ara_indicators += 1

    if ara_indicators >= 2:
        return "ara"

    return "unknown"


def _preprocess_acm_content(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Pre-process ACM document content to help LLM understand the structure.

    The content from PyMuPDF/content-core often comes in vertical format where
    table columns are stacked vertically. This function:
    1. Extracts the ACM Register section (removes boilerplate)
    2. Detects document format (SAMP vs ARA)
    3. Identifies room/building headers
    4. Groups related content together
    5. Adds structural markers to help LLM parsing

    Returns:
        Tuple of (processed_content, metadata_dict)
    """
    metadata: Dict[str, Any] = {
        "original_length": len(content),
        "rooms_found": 0,
        "acm_indicators_found": 0,
        "no_asbestos_found": 0,
        "section_extracted": False,
        "document_format": "unknown",
    }

    # First, try to extract just the ACM Register section
    content, was_extracted = _extract_acm_register_section(content)
    metadata["section_extracted"] = was_extracted
    metadata["extracted_length"] = len(content)

    # Detect document format
    doc_format = _detect_document_format(content)
    metadata["document_format"] = doc_format

    # Count key patterns for metadata
    metadata["acm_indicators_found"] = content.count("Asbestos-containing")
    metadata["no_asbestos_found"] = content.count("No Asbestos")

    # Add section markers to help LLM understand structure
    processed = content

    if doc_format == "ara":
        # ARA format: Named buildings, sequential items, section dividers
        processed, metadata = _preprocess_ara_format(processed, metadata)
    else:
        # SAMP format or unknown: B###/R#### IDs
        processed, metadata = _preprocess_samp_format(processed, metadata)

    metadata["processed_length"] = len(processed)

    return processed, metadata


def _preprocess_ara_format(
    content: str, metadata: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """Pre-process ARA format content (named buildings, numbered items, section dividers)."""
    processed = content

    # Find building names from header blocks
    building_name_pattern = r"Building Name:\s*(.+?)(?:\n|$)"
    building_names = re.findall(building_name_pattern, content)
    unique_buildings = list(dict.fromkeys(name.strip() for name in building_names))
    metadata["ara_buildings_found"] = len(unique_buildings)

    # Find section dividers: "BuildingName - Interior/Exterior - Level"
    section_pattern = r"^(.+?)\s*-\s*(Interior|Exterior)\s*-\s*(.+?)$"
    section_dividers = re.findall(section_pattern, content, re.MULTILINE)
    metadata["ara_section_dividers"] = len(section_dividers)

    # Add section markers for dividers
    for building, area_type, level in section_dividers:
        original = f"{building.strip()} - {area_type} - {level.strip()}"
        marker = f"\n=== SECTION: {original} ===\n"
        processed = processed.replace(original, marker + original)

    # Count hazard types
    asbestos_count = len(re.findall(r"^Asbestos$", content, re.MULTILINE))
    none_count = len(re.findall(r"^None$", content, re.MULTILINE))
    metadata["acm_indicators_found"] = asbestos_count
    metadata["ara_none_hazard_count"] = none_count

    # Count positive/negative results
    positive_patterns = [
        r"\bPositive\b",
        r"\bPresumed Positive\b",
    ]
    negative_patterns = [
        r"\bNegative\b",
        r"\bPresumed Negative\b",
    ]

    pos_count = sum(len(re.findall(p, content)) for p in positive_patterns)
    neg_count = sum(len(re.findall(p, content)) for p in negative_patterns)
    metadata["ara_positive_count"] = pos_count
    metadata["ara_negative_count"] = neg_count

    if debug_config.DEBUG_ENABLED:
        acm_debug(
            f"Pre-process (ARA): {len(unique_buildings)} buildings, "
            f"{len(section_dividers)} section dividers, "
            f"{asbestos_count} asbestos items, {none_count} none items"
        )

    return processed, metadata


def _preprocess_samp_format(
    content: str, metadata: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """Pre-process SAMP format content (B###/R#### building/room IDs)."""
    # Room header pattern: B009 - R0005 - General Storeroom - 6.61 m2
    room_pattern = r"(B\d{3}\s*-\s*R\d{4,5}\s*-\s*[^-\n]+\s*-\s*[\d.]+\s*m2)"
    rooms = re.findall(room_pattern, content)
    metadata["rooms_found"] = len(rooms)

    # Building header pattern: B009 - Special Purpose - 1950 - Steel
    building_pattern = r"(B\d{3}\s*-\s*[A-Za-z][^-\n]+\s*-\s*\d{4}\s*-\s*[A-Za-z]+)"
    buildings = re.findall(building_pattern, content)

    if debug_config.DEBUG_ENABLED:
        acm_debug(f"Pre-process (SAMP): {len(rooms)} rooms, {len(buildings)} buildings")
        acm_debug(
            f"ACM indicators: {metadata['acm_indicators_found']}, "
            f"No Asbestos: {metadata['no_asbestos_found']}"
        )

    processed = content

    # Normalize abbreviated product names to canonical BAR vocabulary
    # Applied BEFORE marker injection so normalized text feeds into markers
    PRODUCT_NORMALIZATIONS = {
        r"\bFuses\b": "Fuse cartridge",
        r"\bFuse\b(?!\s+cartridge)": "Fuse cartridge",
        r"\bFlange\s+mastic\b": "Flange joints",
    }
    for pattern, replacement in PRODUCT_NORMALIZATIONS.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

    # Mark building headers clearly
    for building in buildings:
        marker = f"\n\n=== BUILDING: {building} ===\n"
        processed = processed.replace(building, marker + building)

    # Mark room headers clearly
    for room in rooms:
        marker = f"\n--- ROOM: {room} ---\n"
        processed = processed.replace(room, marker + room)

    # Mark ACM result patterns (replace newline-split version first)
    acm_marker = ">>> ACM DETECTED: Asbestos-containing material <<<"
    processed = processed.replace("Asbestos-containing\nmaterial", acm_marker)
    processed = processed.replace("Asbestos-containing material", acm_marker)

    # Clean up any accidental double markers
    while ">>> ACM DETECTED: >>> ACM DETECTED:" in processed:
        processed = processed.replace(
            ">>> ACM DETECTED: >>> ACM DETECTED: Asbestos-containing material <<< <<<",
            acm_marker,
        )

    # Mark negative result patterns (visual parity with ACM DETECTED markers)
    no_acm_marker = ">>> NO ASBESTOS: Negative result <<<"

    # Replace newline-split versions first (common in PDF extraction)
    processed = processed.replace("No Asbestos\nDetected", no_acm_marker)
    processed = processed.replace("No asbestos\ndetected", no_acm_marker)
    processed = processed.replace("Not\nDetected", no_acm_marker)

    # Replace single-line versions (longer phrases first to avoid partial matches)
    for neg_phrase in [
        "No Asbestos Detected",
        "No asbestos detected",
        "Not Detected",
        "Not detected",
    ]:
        processed = processed.replace(neg_phrase, no_acm_marker)

    # Standalone "No Asbestos" — safe because "No Asbestos Detected" already replaced
    processed = processed.replace("No Asbestos", no_acm_marker)

    # Clean up any accidental double negative markers
    double_neg = f"{no_acm_marker} {no_acm_marker}"
    while double_neg in processed:
        processed = processed.replace(double_neg, no_acm_marker)

    # Mark "No access" / restricted access patterns as valid entries
    # These phrases come from consultant_wording_rules.json patterns
    # and common SAMP report wording — order: longer phrases first (longest match wins).
    # Single-pass combined regex prevents cascade: after a phrase is replaced with the
    # marker text, the marker itself cannot match again because each position is
    # visited exactly once.
    NO_ACCESS_PHRASES = [
        "No access at the time of the Assessment",
        "No access due to locked door",
        "No access due to",
        "No access at time of",
        "Height restriction",
        "Height or access restriction",
        "Restricted Access",
        "Live Electrical Hazard",
        "Presumed ACM",
        "No access",
    ]
    NO_ACCESS_MARKER = ">>> NO ACCESS ENTRY: Sample Result = Assumed Positive — MUST be extracted as a separate ACM record <<<"
    _no_access_pattern = "|".join(re.escape(p) for p in NO_ACCESS_PHRASES)
    processed = re.sub(
        _no_access_pattern,
        lambda m: NO_ACCESS_MARKER + "\n" + m.group(0),
        processed,
        flags=re.IGNORECASE,
    )

    metadata["processed_length"] = len(processed)

    return processed, metadata


class ExtractionState(TypedDict):
    """State for the ACM extraction graph."""

    # Allow PipelineLogger and AGUIEventEmitter (non-Pydantic classes) in schema generation
    __pydantic_config__ = ConfigDict(arbitrary_types_allowed=True)  # type: ignore[assignment]

    source: Source
    content: str
    chunks: List[Dict[str, Any]]
    current_chunk_index: int
    context: BuildingRoomContext
    records: List[ACMExtractionRecord]
    records_rejected: int  # Count of records rejected during validation
    extraction_result: ACMExtractionResult
    error: Optional[str]
    model_id: Optional[str]
    start_time: float
    retry_count: int
    # Corrective RAG loop fields (E1-S15)
    correction_attempt: int
    correction_stats: Dict[str, int]
    enable_corrective_loop: bool
    max_correction_attempts: int
    # Document structure (E1-S16)
    document_structure: Optional[DocumentStructure]
    # Building inventory (E1-S17)
    building_inventory: Optional[BuildingInventory]
    # Page tags (E1-S18)
    page_tags: Optional[PageTaggingResult]
    # Document metadata (E1-S19)
    document_metadata: Optional[DocumentMeta]
    # Orchestrator stats (E1-S20)
    orchestrator_stats: Optional[OrchestratorStats]
    # Pipeline observability (E1-S21)
    pipeline_logger: Optional[PipelineLogger]
    # AG-UI event emitter (E17-S1)
    agui_emitter: Optional[AGUIEventEmitter]
    # E34-S1: operation_id for PipelineEventBus streaming events
    operation_id: Optional[str]
    # E32-S1: Building__c extraction results (record IDs of persisted BuildingRecords)
    building_records: List[str]
    # E32-S2: True when extract_items_node produced >= 1 record
    items_extracted: bool


def _get_pipeline_logger(state: dict) -> Optional[PipelineLogger]:
    """Safely get PipelineLogger from state (may be None for backward compat)."""
    return state.get("pipeline_logger")


def _get_agui_emitter(state: dict) -> Optional[AGUIEventEmitter]:
    """Safely get AGUIEventEmitter from state (may be None for backward compat)."""
    return state.get("agui_emitter")


def _generate_dedup_key(record: ACMExtractionRecord, school_code: Optional[str]) -> str:
    """Generate a deduplication key for a record.

    Key format: {school_code}_{building_id}_{area_type}_{room_id}_{product}_{sample_no}_{hash(description)}
    - Includes area_type to distinguish Interior vs Exterior locations (E1-S25)
    - Includes product to distinguish different items in same room (E1-S27)
    - Includes sample_no to distinguish records with different sample numbers
      in the same room (e.g., gaskets 034511-039-012 vs 013)
    Uses SHA-256 for cryptographic security (truncated to 8 chars for readability).
    """
    school = school_code or "unknown"
    building = record.building_id or "unknown"
    area = (record.area_type or "Interior").lower()  # Default to Interior
    room = record.room_id or "none"
    product = (record.product or "unknown").lower()
    location = (record.location or "unknown").lower()
    sample = (record.sample_no or "no_sample").lower()

    # Create hash of product description (first 50 chars) using SHA-256
    desc_hash = hashlib.sha256(
        (record.material_description or "")[:50].encode()
    ).hexdigest()[:8]

    return (
        f"{school}_{building}_{area}_{room}_{product}_{location}_{sample}_{desc_hash}"
    )


def _merge_records(
    existing: ACMExtractionRecord, new: ACMExtractionRecord
) -> ACMExtractionRecord:
    """Merge two records, keeping the one with higher confidence and merging data_issues."""
    # Confidence ranking
    confidence_rank = {"high": 3, "medium": 2, "low": 1}
    existing_rank = confidence_rank.get(existing.extraction_confidence, 0)
    new_rank = confidence_rank.get(new.extraction_confidence, 0)

    # Keep record with higher confidence
    if new_rank > existing_rank:
        base = new.model_copy()
    else:
        base = existing.model_copy()

    # Merge data_issues — guard against None on either side (old DB records or
    # rare cases where the coercion validator was not run).
    existing_issues = existing.data_issues or []
    new_issues = new.data_issues or []
    all_issues = list(set(existing_issues + new_issues))
    base.data_issues = all_issues

    return base


def _extract_page_range_text(content: str, page_start: int, page_end: int) -> str:
    """Extract text between page_start and page_end markers from source content.

    Uses the same page marker patterns as _chunk_content to find page boundaries,
    then returns the text spanning the requested page range.
    """
    if not content:
        return ""

    page_pattern = r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$)|PAGE\s+(\d+)\s+OF\s+\d+)"
    matches = list(re.finditer(page_pattern, content, re.IGNORECASE))

    if not matches:
        return ""

    # Build page_num -> (start_pos, end_pos) mapping
    start_pos = None
    end_pos = None
    for i, match in enumerate(matches):
        page_num = int(next(g for g in match.groups() if g is not None))
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        if page_num == page_start and start_pos is None:
            start_pos = match.start()
        if page_num == page_end:
            end_pos = next_start
        # If we've passed end page, stop
        if page_num > page_end and end_pos is not None:
            break

    if start_pos is not None and end_pos is not None:
        return content[start_pos:end_pos].strip()
    if start_pos is not None:
        # page_end marker not found, take from start to end of content
        return content[start_pos:].strip()

    return ""


def _chunk_content(
    content: str, context_window: int = DEFAULT_CONTEXT_WINDOW
) -> List[Dict[str, Any]]:
    """Split content into chunks if it exceeds threshold.

    Chunks are split by page markers or logical sections to preserve context.
    """
    tokens = token_count(content)
    threshold = int(context_window * CHUNK_THRESHOLD_RATIO)

    # Page marker pattern - supports multiple formats:
    # 1. Dashes format: "--- Page 5 ---" or "——— Page 5 ———"
    # 2. HTML comment format: "<!-- Page 5 -->"
    # 3. Simple format: "Page 5" at line start
    # 4. ARA footer format: "PAGE 8 OF 34"
    page_pattern = r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$)|PAGE\s+(\d+)\s+OF\s+\d+)"

    if tokens <= threshold:
        # No chunking needed, but still extract first page number if available
        page_num = 1
        # Collect ALL page markers for per-record page assignment
        page_markers = {}
        for match in re.finditer(page_pattern, content, re.IGNORECASE):
            pg = int(next(g for g in match.groups() if g is not None))
            page_markers[match.start()] = pg
        if page_markers:
            page_num = page_markers[min(page_markers.keys())]
        return [
            {
                "content": content,
                "page_number": page_num,
                "page_markers": page_markers,
                "chunk_index": 0,
            }
        ]

    chunks = []

    # Try to split by page markers first
    page_matches = list(re.finditer(page_pattern, content, re.IGNORECASE))

    if page_matches:
        # Split by pages
        for i, match in enumerate(page_matches):
            start = match.start()
            end = (
                page_matches[i + 1].start()
                if i + 1 < len(page_matches)
                else len(content)
            )

            page_content = content[start:end]
            # Extract page number from whichever capture group matched
            page_num = int(next(g for g in match.groups() if g is not None))

            # Check if this chunk is still too large
            if token_count(page_content) > threshold:
                # Split this page further by sections (headings)
                sub_chunks = _split_by_sections(page_content, threshold, page_num)
                for j, sub in enumerate(sub_chunks):
                    chunks.append(
                        {
                            "content": sub,
                            "page_number": page_num,
                            "page_markers": {0: page_num},
                            "chunk_index": len(chunks),
                        }
                    )
            else:
                chunks.append(
                    {
                        "content": page_content,
                        "page_number": page_num,
                        "page_markers": {0: page_num},
                        "chunk_index": len(chunks),
                    }
                )
    else:
        # No page markers - split by character count with overlap
        chunk_size = threshold * CHARS_PER_TOKEN_ESTIMATE
        overlap = CHUNK_OVERLAP_CHARS

        start = 0
        page_num = 1
        while start < len(content):
            end = min(start + chunk_size, len(content))

            # Try to break at a newline
            if end < len(content):
                newline_pos = content.rfind("\n", start + chunk_size - overlap, end)
                if newline_pos > start:
                    end = newline_pos + 1

            chunks.append(
                {
                    "content": content[start:end],
                    "page_number": page_num,
                    "page_markers": {},
                    "chunk_index": len(chunks),
                }
            )

            start = end - overlap if end < len(content) else end
            page_num += 1

    logger.info(f"Content chunked into {len(chunks)} parts")
    return chunks


def _split_by_sections(content: str, max_tokens: int, base_page: int) -> List[str]:
    """Split content by section headers if it's too large."""
    # Split by markdown headers
    sections = re.split(r"(^#{1,3}\s+.+$)", content, flags=re.MULTILINE)

    chunks = []
    current_chunk = ""

    for section in sections:
        if not section.strip():
            continue

        if token_count(current_chunk + section) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = section
        else:
            current_chunk += section

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [content]


def _assign_record_page(
    product: Optional[str],
    chunk_content: str,
    page_markers: Dict[int, int],
    default_page: int,
    search_after: int = 0,
) -> Tuple[int, int]:
    """Assign a page number to a record based on its position in chunk content.

    Searches for the record's product text in the chunk content, then finds the
    nearest preceding page marker to determine the correct page number.

    Args:
        product: The record's product name to search for in content
        chunk_content: The chunk's text content
        page_markers: Dict mapping character offset -> page number
        default_page: Fallback page if product not found
        search_after: Start searching for product after this character offset.
            Used to handle duplicate product names within the same chunk.

    Returns:
        Tuple of (assigned_page, found_position). Position is -1 if not found.
    """
    if not product or not page_markers:
        return default_page, -1

    # Find where the product appears in the chunk content
    pos = chunk_content.lower().find(product.lower(), search_after)
    if pos < 0:
        return default_page, -1

    # Find the last page marker before this position
    assigned_page = default_page
    for offset in sorted(page_markers.keys()):
        if offset <= pos:
            assigned_page = page_markers[offset]
        else:
            break

    return assigned_page, pos


async def extract_metadata_node(state: dict, config: RunnableConfig) -> dict:
    """Extract document metadata as Stage -2 pre-extraction intelligence.

    Story: E1-S19 Document Metadata Extraction Enhancement
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_enter(StageId.STRUCTURE, "Extracting document metadata...")
    if agui:
        await agui.emit_step_started("extract_metadata")

    if not content:
        logger.warning(f"Source {source.id} has no content for metadata extraction")
        if agui:
            await agui.emit_step_finished("extract_metadata")
        return {"document_metadata": None}

    try:
        metadata = await extract_document_metadata(content, model_id=model_id)
        if metadata:
            fields_count = len(metadata.get_extracted_fields())
            consultant = metadata.consultant_name or "unknown"
            logger.info(
                f"Document metadata extracted for source {source.id}: "
                f"consultant={consultant}, "
                f"fields={fields_count}"
            )
            if pl:
                pl.stage_progress(
                    StageId.STRUCTURE,
                    f"Metadata extracted: consultant={consultant}",
                    consultant=consultant,
                    fields=fields_count,
                )
            if agui:
                await agui.emit_state_delta(
                    [
                        {
                            "op": "replace",
                            "path": "/metadata",
                            "value": {"consultant": consultant, "fields": fields_count},
                        }
                    ]
                )
        if agui:
            await agui.emit_step_finished(
                "extract_metadata", fields=fields_count if metadata else 0
            )
        return {"document_metadata": metadata}
    except Exception as e:
        logger.warning(f"Metadata extraction failed for source {source.id}: {e}")
        if agui:
            await agui.emit_step_finished("extract_metadata")
        return {"document_metadata": None}


async def extract_structure(state: dict, config: RunnableConfig) -> dict:
    """Extract document structure as Stage -1 pre-extraction intelligence.

    Story: E1-S16 Document Structure & TOC Extraction
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Extracting document structure...")
    if agui:
        await agui.emit_step_started("structure")

    if not content:
        logger.warning(f"Source {source.id} has no content for structure extraction")
        if agui:
            await agui.emit_step_finished("structure")
        return {"document_structure": None}

    try:
        structure = await extract_document_structure(content, model_id=model_id)

        # AC1: PyMuPDF page-count fallback when regex finds 0 page markers
        if structure.total_pages == 0:
            pdf_path = (
                getattr(source.asset, "file_path", None) if source.asset else None
            )
            if pdf_path:
                try:
                    import fitz  # PyMuPDF

                    with fitz.open(pdf_path) as pdf_doc:
                        structure.total_pages = len(pdf_doc)
                    logger.info(
                        f"[AC1] PyMuPDF page-count fallback: {structure.total_pages} pages "
                        f"for source {source.id}"
                    )
                except Exception as fitz_err:
                    logger.debug(f"PyMuPDF fallback failed: {fitz_err}")

        logger.info(
            f"Document structure extracted for source {source.id}: "
            f"type={structure.document_type}, register_start={structure.register_start_page}, "
            f"buildings={len(structure.building_ids)}"
        )
        if pl:
            pl.stage_progress(
                StageId.STRUCTURE,
                f"Structure: type={structure.document_type}, register_start={structure.register_start_page}",
                document_type=structure.document_type,
                register_start=structure.register_start_page,
                buildings=len(structure.building_ids),
            )
        if agui:
            await agui.emit_state_delta(
                [
                    {
                        "op": "replace",
                        "path": "/toc",
                        "value": {
                            "type": structure.document_type,
                            "buildings": len(structure.building_ids),
                        },
                    }
                ]
            )
            await agui.emit_step_finished(
                "structure", buildings=len(structure.building_ids)
            )
        return {"document_structure": structure}
    except Exception as e:
        logger.warning(f"Structure extraction failed for source {source.id}: {e}")
        if agui:
            await agui.emit_step_finished("structure")
        return {"document_structure": None}


async def compile_inventory(state: dict, config: RunnableConfig) -> dict:
    """Compile building inventory as Stage -1.5 pre-extraction intelligence.

    Story: E1-S17 Building Inventory Compilation
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    doc_structure: Optional[DocumentStructure] = state.get("document_structure")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Compiling building inventory...")
    if agui:
        await agui.emit_step_started("inventory")

    if not content:
        logger.warning(f"Source {source.id} has no content for building inventory")
        if agui:
            await agui.emit_step_finished("inventory")
        return {"building_inventory": None}

    try:
        inventory = await compile_building_inventory(
            content,
            document_structure=doc_structure,
            model_id=model_id,
        )
        logger.info(
            f"Building inventory compiled for source {source.id}: "
            f"{inventory.total_buildings} buildings, "
            f"{len(inventory.processing_groups)} groups"
        )
        if pl:
            # Build page range string
            page_ranges = []
            for b in inventory.buildings:
                page_ranges.append(f"{b.page_start}-{b.page_end or b.page_start}")
            pl.stage_progress(
                StageId.STRUCTURE,
                f"Inventory: {inventory.total_buildings} buildings",
                buildings=inventory.total_buildings,
                pages=", ".join(page_ranges) if page_ranges else "N/A",
            )
        if agui:
            await agui.emit_state_delta(
                [
                    {
                        "op": "replace",
                        "path": "/buildings",
                        "value": inventory.total_buildings,
                    }
                ]
            )
            await agui.emit_step_finished(
                "inventory", buildings=inventory.total_buildings
            )
        return {"building_inventory": inventory}
    except Exception as e:
        logger.warning(
            f"Building inventory compilation failed for source {source.id}: {e}"
        )
        if agui:
            await agui.emit_step_finished("inventory")
        return {"building_inventory": None}


async def tag_page_sections(state: dict, config: RunnableConfig) -> dict:
    """Tag each page with section classification as Stage -1.25.

    Story: E1-S18 Page-Level Section Tagging
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    doc_structure: Optional[DocumentStructure] = state.get("document_structure")
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Tagging page sections...")
    if agui:
        await agui.emit_step_started("tag_pages")

    if not content:
        logger.warning(f"Source {source.id} has no content for page tagging")
        if agui:
            await agui.emit_step_finished("tag_pages")
        return {"page_tags": None}

    try:
        result = await tag_pages(
            content,
            document_structure=doc_structure,
            building_inventory=inventory,
            model_id=model_id,
        )
        logger.info(
            f"Page tagging complete for source {source.id}: "
            f"{len(result.pages)} pages tagged, "
            f"register_range={result.register_page_range}"
        )
        if pl:
            pl.stage_complete(
                StageId.STRUCTURE,
                f"{len(result.pages)} pages tagged, register={result.register_page_range}",
                pages_tagged=len(result.pages),
                register_range=str(result.register_page_range),
            )
        if agui:
            await agui.emit_state_delta(
                [{"op": "replace", "path": "/page_tags", "value": len(result.pages)}]
            )
            await agui.emit_step_finished("tag_pages", pages_tagged=len(result.pages))
        return {"page_tags": result}
    except Exception as e:
        logger.warning(f"Page tagging failed for source {source.id}: {e}")
        if pl:
            pl.stage_complete(
                StageId.STRUCTURE,
                "Completed with warnings: page tagging failed (non-fatal)",
                pages_tagged=0,
                warnings=1,
            )
        if agui:
            await agui.emit_step_finished("tag_pages")
        return {"page_tags": None}


async def save_intelligence_node(state: dict, config: RunnableConfig) -> dict:
    """Persist pre-extraction intelligence to source_intelligence table (E30-S9).

    Runs between tag_pages and orchestrate. Non-blocking: catches all exceptions
    so the pipeline continues even if persistence fails.
    """
    source: Source = state["source"]
    agui = _get_agui_emitter(state)

    if agui:
        await agui.emit_step_started("save_intelligence")

    try:
        doc_meta: Optional[DocumentMeta] = state.get("document_metadata")
        doc_structure: Optional[DocumentStructure] = state.get("document_structure")
        inventory: Optional[BuildingInventory] = state.get("building_inventory")
        page_tags: Optional[PageTaggingResult] = state.get("page_tags")

        data: Dict[str, Any] = {
            "document_meta": doc_meta.model_dump(mode="json") if doc_meta else None,
            "document_structure": (
                doc_structure.model_dump(mode="json") if doc_structure else None
            ),
            "building_inventory": (
                inventory.model_dump(mode="json") if inventory else None
            ),
            "page_tags": page_tags.model_dump(mode="json") if page_tags else None,
            "total_pages": (doc_structure.total_pages if doc_structure else None),
            "total_buildings": inventory.total_buildings if inventory else None,
            "document_type": (
                doc_structure.document_type.value if doc_structure else None
            ),
            "register_page_range": (
                {
                    "start": page_tags.register_page_range[0],
                    "end": page_tags.register_page_range[1],
                }
                if page_tags and page_tags.register_page_range
                else None
            ),
            "field_confidence": doc_meta.field_confidence if doc_meta else None,
        }

        source_id_str = str(source.id)
        await save_source_intelligence(source_id_str, data)
        logger.info(f"[PIPELINE] Saved pre-extraction intelligence for {source_id_str}")

    except Exception as e:
        logger.warning(
            f"[PIPELINE] Failed to save intelligence for {source.id}: {e} "
            "(non-fatal, continuing pipeline)"
        )

    if agui:
        await agui.emit_step_finished("save_intelligence")

    return {}


async def extract_building_node(state: dict, config: RunnableConfig) -> dict:
    """Phase 1 Building__c extraction: one AI call per building section.

    Iterates over state["building_inventory"].buildings and calls
    _v3_extract_building_meta() for each building, mapping results to
    BuildingRecord domain objects and persisting them to the DB.

    Story: E32-S1 Building__c AI Extraction Node
    """
    source: Source = state["source"]
    content: str = source.full_text or ""
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    schema_bundle = state.get(
        "schema_bundle"
    )  # may be None — _v3_extract_building_meta handles None
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)
    operation_id: Optional[str] = state.get("operation_id")
    model_id: Optional[str] = state.get("model_id")

    if agui:
        await agui.emit_step_started("extract_building")

    if not inventory or not inventory.buildings:
        logger.info(
            f"[E32-S1] No building inventory for source {source.id} — skipping building extraction"
        )
        if agui:
            await agui.emit_step_finished("extract_building", buildings=0)
        return {"building_records": []}

    if pl:
        pl.stage_progress(
            StageId.ORCHESTRATOR,
            f"Building extraction: {inventory.total_buildings} buildings",
        )

    saved_ids: List[str] = []
    source_id_str = str(source.id)

    for building_meta in inventory.buildings:
        _bldg_start = time.time()
        try:
            # Slice document content to this building's page range
            page_start = building_meta.page_start
            page_end = building_meta.page_end or page_start
            building_content = _extract_building_content(content, page_start, page_end)

            if not building_content.strip():
                logger.warning(
                    f"[E32-S1] Empty content for building {building_meta.building_id} "
                    f"(pages {page_start}-{page_end}) — skipping"
                )
                continue

            # Construct a minimal BuildingExtractionPlan so _v3_extract_building_meta
            # can access building_id and page_range for logging/prompt context
            plan = BuildingExtractionPlan(
                building_id=building_meta.building_id,
                building_name=building_meta.name,
                page_range=(page_start, page_end),
                strategy=ExtractionStrategy.FULL_LLM,
            )

            # Phase 1 LLM call — returns BuildingExtractionResult or None on failure
            result = await _v3_extract_building_meta(
                building_content=building_content,
                plan=plan,
                state=state,
                schema_bundle=schema_bundle,
            )

            if result is None:
                logger.warning(
                    f"[E32-S1] Phase 1 returned None for building {building_meta.building_id} — skipping"
                )
                continue

            # Generate server-side internal ID: BLD#{source_short}_{seq:03d}
            internal_id = await BuildingRecord.generate_internal_id(source_id_str)

            # Map BuildingExtractionResult fields to BuildingRecord domain model
            record = BuildingRecord(
                internal_id=internal_id,
                source_id=source_id_str,
                building_code=building_meta.building_id,
                building_name=result.building_name,
                building_type=result.building_type,
                building_category=result.building_category,
                building_address=result.building_address,
                suburb=result.suburb,
                postcode=result.postcode,
                building_year=result.estimated_year_built,
                building_construction=result.construction_type,
                date_of_audit_report=result.date_of_audit,
                frequency_of_use=result.frequency_of_use,
            )

            saved_record = await record.save()
            if not saved_record or not saved_record.id:
                logger.warning(
                    f"[E32-S1] BuildingRecord.save() returned no ID for building "
                    f"{building_meta.building_id} — record may not have persisted"
                )
                continue
            record_id = str(saved_record.id)
            saved_ids.append(record_id)

            logger.info(
                f"[E32-S1] Saved BuildingRecord {internal_id} for building "
                f"{building_meta.building_id} (confidence={result.extraction_confidence})"
            )

            # E34-S1: Publish ai.building_extracted event for real-time streaming
            if operation_id:
                try:
                    _bldg_duration_ms = int((time.time() - _bldg_start) * 1000)
                    await get_event_bus().publish(
                        AIBuildingExtractedEvent(
                            operation_id=operation_id,
                            data=AIBuildingExtractedData(
                                building_id=internal_id,
                                building_name=result.building_name or building_meta.building_id,
                                records_extracted=1,
                                model_used=model_id or "unknown",
                                duration_ms=_bldg_duration_ms,
                            ),
                        )
                    )
                except Exception as _pub_err:
                    logger.debug(
                        f"[E34-S1] Failed to publish ai.building_extracted for "
                        f"{building_meta.building_id}: {_pub_err}"
                    )

        except Exception as e:
            logger.warning(
                f"[E32-S1] Failed to extract/save building {building_meta.building_id}: {e} "
                "(skipping — partial results preserved)"
            )
            continue

    logger.info(
        f"[E32-S1] Building extraction complete for source {source_id_str}: "
        f"{len(saved_ids)}/{len(inventory.buildings)} buildings saved"
    )

    if pl:
        pl.stage_progress(
            StageId.ORCHESTRATOR,
            f"Building extraction: {len(saved_ids)}/{len(inventory.buildings)} saved",
            buildings_saved=len(saved_ids),
        )

    if agui:
        await agui.emit_step_finished(
            "extract_building",
            buildings=len(saved_ids),
            total=len(inventory.buildings),
        )

    return {"building_records": saved_ids}


# ---------------------------------------------------------------------------
# E32-S2: Item__c AI Extraction Node
# ---------------------------------------------------------------------------

_ITEM_EXTRACTION_CHUNK_CHARS = 48_000


async def _chunk_and_extract_items(
    building_content: str,
    plan: BuildingExtractionPlan,
    building_meta: Optional[BuildingExtractionResult],
    state: dict,
    schema_bundle: Optional[Any],
) -> ACMItemExtractionResult:
    """Split oversized building content and merge item results.

    If building_content exceeds _ITEM_EXTRACTION_CHUNK_CHARS, splits into
    equal-sized char chunks, calls _v3_extract_items() for each, and merges
    records into a single ACMItemExtractionResult.

    Story: E32-S2 Item__c AI Extraction Node
    """
    if len(building_content) <= _ITEM_EXTRACTION_CHUNK_CHARS:
        return await _v3_extract_items(
            building_content, plan, building_meta, state, schema_bundle
        )

    # Split into N equal-sized char chunks
    chunks = [
        building_content[i : i + _ITEM_EXTRACTION_CHUNK_CHARS]
        for i in range(0, len(building_content), _ITEM_EXTRACTION_CHUNK_CHARS)
    ]
    merged_records = []
    final_status = "valid"
    for chunk in chunks:
        result = await _v3_extract_items(
            chunk, plan, building_meta, state, schema_bundle
        )
        merged_records.extend(result.records)
        if result.status == "invalid":
            final_status = "invalid"

    return ACMItemExtractionResult(records=merged_records, status=final_status)


async def extract_items_node(state: dict, config: RunnableConfig) -> dict:
    """Phase 2 Item__c extraction: one AI call per building section.

    For each building in building_inventory, calls _v3_extract_items()
    and normalises results to ACMExtractionRecord via _normalize_v3_records().
    Appends all records to state["records"] for consumption by validate/save nodes.

    Returns items_extracted=True when at least one record was produced.

    Story: E32-S2 Item__c AI Extraction Node
    """
    source: Source = state["source"]
    content: str = source.full_text or ""
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    schema_bundle = state.get("schema_bundle")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)
    source_id_str = str(source.id)
    operation_id: Optional[str] = state.get("operation_id")

    if not inventory or not inventory.buildings:
        logger.info(
            f"[E32-S2] No building inventory for source {source_id_str} — skipping item extraction"
        )
        return {"records": [], "items_extracted": False}

    if agui:
        await agui.emit_step_started("extract_items")

    # Build building_code -> record_id lookup from persisted BuildingRecords
    try:
        saved_buildings = await BuildingRecord.get_by_source(source_id_str)
        code_to_id_map: dict = {
            br.building_code: str(br.id)
            for br in (saved_buildings or [])
            if br.building_code
        }
        # Build building_code -> internal_id lookup for event publishing
        code_to_internal_id_map: dict = {
            br.building_code: br.internal_id or br.building_code
            for br in (saved_buildings or [])
            if br.building_code
        }
    except Exception as e:
        logger.warning(
            f"[E32-S2] Could not load BuildingRecords for source {source_id_str}: {e} "
            "(building_record_id will not be populated)"
        )
        code_to_id_map = {}
        code_to_internal_id_map = {}

    all_records: List[ACMExtractionRecord] = []
    n_buildings = len(inventory.buildings)

    for building_meta in inventory.buildings:
        try:
            page_start = building_meta.page_start
            page_end = building_meta.page_end or page_start

            building_content = _extract_building_content(content, page_start, page_end)

            if not building_content.strip():
                logger.warning(
                    f"[E32-S2] Empty content for building {building_meta.building_id} "
                    f"(pages {page_start}-{page_end}) — skipping"
                )
                continue

            plan = BuildingExtractionPlan(
                building_id=building_meta.building_id,
                building_name=building_meta.name,
                page_range=(page_start, page_end),
                strategy=ExtractionStrategy.FULL_LLM,
            )

            # Re-run Phase 1 to get building_meta_result for picklist subsetting.
            # Phase 1 is cheap (small prompt). This avoids state complexity of
            # caching Phase 1 results across nodes.
            # If None, _normalize_v3_records falls back to plan.building_name.
            building_meta_result = await _v3_extract_building_meta(
                building_content=building_content,
                plan=plan,
                state=state,
                schema_bundle=schema_bundle,
            )

            # Phase 2: extract items (with chunking if content is large)
            item_result = await _chunk_and_extract_items(
                building_content, plan, building_meta_result, state, schema_bundle
            )

            # Normalise V3 SF fields -> ACMExtractionRecord
            records = _normalize_v3_records(building_meta_result, item_result, plan)

            # Populate building_record_id FK from lookup map
            building_record_id = code_to_id_map.get(building_meta.building_id)
            if building_record_id:
                for rec in records:
                    rec.building_record_id = building_record_id

            all_records.extend(records)
            logger.info(
                f"[E32-S2] Building {building_meta.building_id}: {len(records)} items"
            )

            # E34-S1: Publish ai.items_extracted event for real-time streaming
            if operation_id:
                try:
                    _internal_id = code_to_internal_id_map.get(
                        building_meta.building_id, building_meta.building_id
                    )
                    items_rejected = (
                        len(item_result.records) - len(records)
                        if hasattr(item_result, "records")
                        else 0
                    )
                    await get_event_bus().publish(
                        AIItemsExtractedEvent(
                            operation_id=operation_id,
                            data=AIItemsExtractedData(
                                building_id=_internal_id,
                                items_count=len(records),
                                items_rejected=max(0, items_rejected),
                            ),
                        )
                    )
                except Exception as _pub_err:
                    logger.debug(
                        f"[E34-S1] Failed to publish ai.items_extracted for "
                        f"{building_meta.building_id}: {_pub_err}"
                    )

        except Exception as e:
            logger.warning(
                f"[E32-S2] Failed to extract items for building "
                f"{building_meta.building_id}: {e} "
                "(skipping — partial results preserved)"
            )
            continue

    logger.info(
        f"[E32-S2] Item extraction complete: {len(all_records)} records from "
        f"{n_buildings} buildings"
    )

    if pl:
        pl.stage_progress(
            StageId.ORCHESTRATOR,
            f"Item extraction: {len(all_records)} records from {n_buildings} buildings",
        )

    if agui:
        await agui.emit_step_finished(
            "extract_items",
            records=len(all_records),
            buildings=n_buildings,
        )

    return {"records": all_records, "items_extracted": len(all_records) > 0}


def should_run_orchestrate(state: dict) -> str:
    """Route to orchestrate (fallback) or validate directly.

    Orchestrate runs when:
    - building_inventory is None/empty (legacy document, no structure detection)
    - items_extracted is False (E32-S2 produced zero records — possible extraction failure)

    Otherwise skip directly to validate.

    Story: E32-S2 Item__c AI Extraction Node
    """
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    items_extracted: bool = state.get("items_extracted", False)

    if not inventory or not inventory.buildings:
        return "orchestrate"
    if not items_extracted:
        return "orchestrate"
    return "validate"


async def orchestrate_with_logging(state: dict, config: RunnableConfig) -> dict:
    """Wrapper around orchestrate_extraction that adds pipeline logging.

    Story: E1-S21 — instruments the ORCHESTRATOR stage.
    """
    pl = _get_pipeline_logger(state)
    if pl:
        pl.stage_enter(StageId.ORCHESTRATOR, "Planning extraction strategy...")
    try:
        result = await orchestrate_extraction(state, config)
        if pl:
            orch_stats = result.get("orchestrator_stats")
            summary = ""
            if orch_stats:
                n_plans = len(orch_stats.plan.plans) if orch_stats.plan else 0
                n_records = orch_stats.total_records
                n_extracted = orch_stats.buildings_extracted
                parts = [f"{n_plans} building plans"]
                if n_extracted > 0:
                    parts.append(f"{n_extracted} extracted")
                if n_records > 0:
                    parts.append(f"{n_records} records")
                if orch_stats.buildings_skipped > 0:
                    parts.append(f"{orch_stats.buildings_skipped} skipped")
                # Surface strategy distribution for debugging
                if orch_stats.strategy_distribution:
                    strats = ", ".join(
                        f"{k}={v}" for k, v in orch_stats.strategy_distribution.items()
                    )
                    parts.append(f"strategies: {strats}")
                summary = " | ".join(parts)

                # Surface per-building errors/warnings to pipeline log
                if orch_stats.plan and orch_stats.plan.plans:
                    for bp in orch_stats.plan.plans:
                        pl._log(
                            f"  Building plan: {bp.building_name} | "
                            f"strategy={bp.strategy.value} | "
                            f"pages={bp.page_range}"
                        )
                # Check building stats from result for errors
                raw_records = result.get("records", [])
                if n_plans > 0 and n_records == 0:
                    pl._log(
                        f"  WARNING: {n_plans} plans but 0 records — "
                        f"check LLM response or auth errors",
                        level="warning",
                    )
            pl.stage_complete(StageId.ORCHESTRATOR, summary)
        return result
    except Exception as e:
        if pl:
            pl.stage_fail(StageId.ORCHESTRATOR, str(e))
        raise


async def prepare_context(state: dict, config: RunnableConfig) -> dict:
    """Prepare extraction context and chunk content if needed."""
    source: Source = state["source"]
    content = normalize_docling_text(source.full_text or "")
    input_format = "markdown"

    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    # Skip ORCHESTRATOR stage when taking the non-orchestrator path (E1-S21)
    if pl:
        pl.stage_skip(StageId.ORCHESTRATOR, "Below threshold for orchestration")

    if pl:
        pl.stage_enter(StageId.PREFLIGHT, "Preparing content and chunking...")
    if agui:
        await agui.emit_step_started("prepare")

    if not content:
        logger.warning(f"Source {source.id} has no content")
        return {
            "error": "Source has no content to extract",
            "chunks": [],
            "context": BuildingRoomContext(),
        }

    # Debug: Log content preview and dump to file
    source_id = str(source.id) if source.id else "unknown"
    log_extraction_preview(content, source_id)
    dump_content_to_file(content, source_id, "raw_content")

    # Use register_start_page from document structure to trim content (E1-S16)
    doc_structure: Optional[DocumentStructure] = state.get("document_structure")
    if doc_structure and doc_structure.register_start_page:
        # Find the page marker for register_start_page and trim content
        page_pattern = re.compile(
            rf"(?:[-—]+|<!--)\s*Page\s+{doc_structure.register_start_page}\s*(?:[-—]+|-->)|PAGE\s+{doc_structure.register_start_page}\s+OF\s+\d+",
            re.IGNORECASE,
        )
        match = page_pattern.search(content)
        if match and match.start() > 500:
            trimmed = content[match.start() :]
            acm_debug(
                f"Trimmed content using register_start_page={doc_structure.register_start_page}: "
                f"{len(content)} -> {len(trimmed)} chars"
            )
            content = trimmed

    if input_format == "html":
        processed_content = content
        preprocess_meta = {
            "acm_indicators_found": 0,
            "no_asbestos_found": 0,
        }
    else:
        # Pre-process content to add structural markers
        processed_content, preprocess_meta = _preprocess_acm_content(content)

        if debug_config.DEBUG_ENABLED:
            acm_debug(f"Pre-processing complete: {preprocess_meta}")
            dump_content_to_file(processed_content, source_id, "processed_content")

    # E26-S4: Inject Docling structured tables into non-orchestrator path
    # The orchestrator path handles this in _extract_single_building(),
    # but single-building documents (building_inventory=0) skip the orchestrator.
    source_id_str = str(source.id) if source.id else None
    if source_id_str:
        try:
            # Use full document page range (1 to total_pages)
            total_pages = state.get("pipeline_logger")
            max_page = (
                total_pages.total_pages
                if total_pages and hasattr(total_pages, "total_pages")
                else 999
            )
            docling_tables = await _get_docling_tables(source_id_str, 1, max_page)
            if docling_tables:
                processed_content = _inject_docling_tables(
                    processed_content, docling_tables
                )
                logger.info(
                    f"Non-orchestrator path: injected {len(docling_tables)} "
                    f"Docling tables into LLM context for {source_id_str}"
                )
        except Exception as e:
            logger.warning(f"Docling table injection failed in prepare_context: {e}")

    # Initialize context from source metadata
    context = BuildingRoomContext()
    if source.title:
        context.school_name = source.title

    # Chunk processed content if needed
    if input_format == "html":
        chunks = [{"content": processed_content, "page_number": 1}]
    else:
        chunks = _chunk_content(processed_content)

    logger.info(f"Prepared {len(chunks)} chunks for extraction from source {source.id}")
    acm_debug(
        f"Content stats: {preprocess_meta['acm_indicators_found']} ACM indicators, "
        f"{preprocess_meta['no_asbestos_found']} No Asbestos entries"
    )

    if pl:
        pl.stage_complete(
            StageId.PREFLIGHT,
            f"{len(chunks)} chunks prepared",
            chunks=len(chunks),
            content_chars=len(processed_content),
            acm_indicators=preprocess_meta.get("acm_indicators_found", 0),
        )
    if agui:
        await agui.emit_state_delta(
            [{"op": "replace", "path": "/chunks", "value": len(chunks)}]
        )
        await agui.emit_step_finished("prepare", chunks=len(chunks))

    return {
        "content": processed_content,
        "chunks": chunks,
        "input_format": input_format,
        "context": context,
        "current_chunk_index": 0,
        "records": [],
        "start_time": time.time(),
    }


async def extract_records(state: dict, config: RunnableConfig) -> dict:
    """Extract ACM records from the current chunk using LLM."""
    chunks = state.get("chunks", [])
    current_index = state.get("current_chunk_index", 0)
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    existing_records: List[ACMExtractionRecord] = state.get("records", [])
    model_id = state.get("model_id")
    input_format = state.get("input_format", "markdown")
    retry_count = state.get("retry_count", 0)
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    # AG-UI tool call ID for this chunk
    tool_call_id = f"extract_chunk_{current_index}"

    # Log stage entry on first chunk only
    if pl and current_index == 0 and retry_count == 0:
        pl.stage_enter(
            StageId.EXTRACT,
            f"Processing {len(chunks)} chunks" if chunks else "No chunks",
        )

    if not chunks or current_index >= len(chunks):
        return {"error": "No chunks to process"}

    chunk = chunks[current_index]
    chunk_content = chunk["content"]
    page_number = chunk.get("page_number", 1)

    # Update context with chunk info
    context.current_page = page_number

    acm_debug(f"Chunk {current_index + 1}/{len(chunks)}: {len(chunk_content)} chars")

    # Provision model BEFORE prompt rendering so we can detect model family.
    # model_family initialized here so prompt rendering outside try block never hits NameError.
    model_family = "default"
    try:
        # Dynamic max_tokens: look up model capabilities; fall back to 16384 if unavailable
        _max_tokens = (
            16384  # safe fallback (8192 too small for registers with 30+ records)
        )
        _early_qwen = False
        if model_id:
            try:
                _domain_model = await Model.get(model_id)
                _max_tokens = _domain_model.get_max_output_tokens(fallback=16384)
                _early_qwen = "qwen2.5" in (_domain_model.name or "").lower()
            except asyncio.CancelledError:
                raise  # never suppress cooperative cancellation
            except Exception:
                logger.warning(
                    f"Could not fetch Model capabilities for {model_id}; "
                    "falling back to max_tokens=16384, Qwen2.5 path disabled"
                )
        # Qwen2.5: use temperature=0.0 for deterministic extraction
        _temperature = 0.0 if _early_qwen else (0.1 if retry_count > 0 else 0.3)
        model = await provision_langchain_model(
            chunk_content,
            model_id,
            "extraction",  # Uses default_extraction_model or falls back to chat
            temperature=_temperature,
            max_tokens=_max_tokens,
        )

        is_qwen = _is_qwen_model(model)
        model_family = "qwen" if is_qwen else "default"
        # Track model ID and prompt template for observability (E1-S21, AC #4)
        if pl:
            actual_model = (
                getattr(model, "model_name", None)
                or getattr(model, "model", None)
                or model_id
                or "default_extraction_model"
            )
            pl.log_model(str(actual_model), "extraction")
            logger.info("[PIPELINE] Prompt template: acm/extraction")
        if is_qwen:
            logger.info(
                f"Qwen2.5 model detected — using direct JSON mode (temp={_temperature})"
            )
    except Exception as e:
        logger.error(f"Failed to provision model: {e}")
        return {"error": f"Model provisioning failed: {e}"}

    # Render the extraction prompt (after provisioning so model_family is known)
    prompter = Prompter(prompt_template="acm/extraction")
    system_prompt = prompter.render(
        data={
            "school_name": context.school_name,
            "page_number": page_number,
            "building_context": context,
            "chunk_info": {
                "chunk_index": current_index,
                "total_chunks": len(chunks),
            },
            "content": chunk_content,
            "input_format": input_format,
            "model_family": model_family,
        }
    )

    # Debug: Log and dump the prompt
    source: Source = state["source"]
    source_id = str(source.id) if source.id else "unknown"
    log_prompt_preview(system_prompt, source_id)
    dump_prompt_to_file(system_prompt, source_id, current_index)

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Extract ACM records from the content provided in the system prompt."
        ),
    ]

    # Emit AG-UI tool call start
    if agui:
        import json as _json

        await agui.emit_tool_call_start(tool_call_id, "extract_records")
        await agui.emit_tool_call_args(
            tool_call_id,
            _json.dumps(
                {
                    "chunk_index": current_index,
                    "total_chunks": len(chunks),
                    "page": page_number,
                    "content_length": len(chunk_content),
                }
            ),
        )

    # Direct ainvoke + JSON parse for all models (E27-S1: eliminates dead
    # with_structured_output() that always fails on OpenRouter/Anthropic grammar limits)
    try:
        raw_response = await model.ainvoke(messages)

        # E27-S3: Verify provider routing (non-blocking)
        try:
            await _verify_provider_routing(raw_response, "extract_records")
        except Exception:
            pass

        response_text = (
            raw_response.content
            if hasattr(raw_response, "content")
            else str(raw_response)
        )
        parsed = parse_json_response(response_text)
        # E27-S4: completionState wrapper eliminated by Anthropic-direct routing (E27-S3)
        result: ACMExtractionResult = ACMExtractionResult.model_validate(parsed)
        logger.info(f"Direct JSON extraction: {len(result.records)} records")

        # Debug: Log raw result before processing
        logger.debug(
            f"Raw extraction result: status={result.status}, records_count={len(result.records)}"
        )
        if result.records:
            logger.debug(f"First record: {result.records[0].model_dump_json()[:500]}")
        else:
            logger.warning(
                f"No records extracted. Extraction notes: {result.extraction_notes}"
            )

        # Update stats
        result.update_stats()

        # Extract new records and update context
        new_records = result.records

        # Ensure page_number is set on all records from this chunk
        # Use page_markers for position-based assignment instead of blanket chunk page
        # Track search positions per product to handle duplicate product names
        page_markers = chunk.get("page_markers", {})
        search_positions: Dict[str, int] = {}
        for record in new_records:
            if record.page_number is None:
                product_key = (record.product or "").lower()
                search_start = search_positions.get(product_key, 0)
                page, pos = _assign_record_page(
                    record.product,
                    chunk_content,
                    page_markers,
                    page_number,
                    search_start,
                )
                record.page_number = page
                if record.product and pos >= 0:
                    search_positions[product_key] = pos + len(record.product)

        if new_records:
            # Update context from the last record for continuity
            last_record = new_records[-1]
            if last_record.building_id:
                context.building_id = last_record.building_id
                context.building_name = last_record.building_name
            if last_record.room_id:
                context.room_id = last_record.room_id
                context.room_name = last_record.room_name

        logger.info(
            f"Extracted {len(new_records)} records from chunk {current_index + 1}/{len(chunks)}"
        )

        # Per-chunk progress logging
        if pl:
            total_so_far = len(existing_records) + len(new_records)
            progress = (current_index + 1) / len(chunks) if chunks else 1.0
            pl.stage_progress(
                StageId.EXTRACT,
                f"Chunk {current_index + 1}/{len(chunks)} | pages {page_number}+ | "
                f"{len(new_records)} records | {total_so_far} total",
                progress=progress,
                records_so_far=total_so_far,
                chunk=f"{current_index + 1}/{len(chunks)}",
            )

        # AG-UI: emit tool call end and state delta for new records
        if agui and new_records:
            # Emit StateDelta for each new record (incremental streaming)
            for rec in new_records:
                await agui.emit_state_delta(
                    [
                        {
                            "op": "add",
                            "path": "/records/-",
                            "value": {
                                "building_id": rec.building_id,
                                "room_name": rec.room_name,
                                "product": rec.product,
                                "result": rec.result,
                                "page_number": rec.page_number,
                            },
                        }
                    ]
                )
            await agui.emit_tool_call_end(
                tool_call_id,
                f"{len(new_records)} records from chunk {current_index + 1}",
            )
        elif agui:
            await agui.emit_tool_call_end(tool_call_id, "0 records")

        return {
            "records": existing_records + new_records,
            "context": context,
            "current_chunk_index": current_index + 1,
            "extraction_result": result,
            "retry_count": 0,  # Reset retry count on success
        }

    except ValidationError as e:
        logger.warning(f"Structured output validation failed (schema mismatch): {e}")
        _exc_info = ("validation", e)
    except Exception as e:
        logger.warning(f"Structured output extraction failed: {e}")
        _exc_info = ("extraction", e)

    # Fallback logic shared between both except clauses.
    # The success path above always returns, so _exc_info is always set here.
    _error_type, _exc = _exc_info  # type: ignore[possibly-undefined]

    if is_auth_error(_exc):
        failed_model_name = (
            getattr(model, "model_name", None)
            or getattr(model, "model", None)
            or str(model_id or "unknown")
        )
        fallback_model = await provision_extraction_fallback_model(
            str(failed_model_name),
            temperature=0.0 if is_qwen else 0.1,
            max_tokens=_max_tokens,
        )
        if fallback_model is not None:
            model = fallback_model
            is_qwen = _is_qwen_model(model)
            logger.warning(
                "Authentication failure detected for extraction model "
                f"'{failed_model_name}', switched to fallback model "
                f"'{getattr(model, 'model_name', getattr(model, 'model', 'unknown'))}'"
            )

    # Fallback: try direct model invocation with manual JSON extraction
    # (handles OpenRouter/provider incompatibility with function calling)
    if retry_count == 0:
        logger.info(
            "Attempting fallback: direct model invocation with manual JSON parsing"
        )
        response_text = ""
        try:
            raw_response = await model.ainvoke(messages)
            response_text = (
                raw_response.content
                if hasattr(raw_response, "content")
                else str(raw_response)
            )

            parsed = parse_json_response(response_text)
            result = ACMExtractionResult.model_validate(parsed)
            logger.info(
                f"Fallback JSON parsing succeeded: {len(result.records)} records"
            )
            # Continue with normal processing (jump to success path below)
            # We need to duplicate the post-processing here
            result.update_stats()
            new_records = result.records
            page_markers = chunk.get("page_markers", {})
            search_positions_fb: Dict[str, int] = {}
            for record in new_records:
                if record.page_number is None:
                    product_key = (record.product or "").lower()
                    search_start = search_positions_fb.get(product_key, 0)
                    page, pos = _assign_record_page(
                        record.product,
                        chunk_content,
                        page_markers,
                        page_number,
                        search_start,
                    )
                    record.page_number = page
                    if record.product and pos >= 0:
                        search_positions_fb[product_key] = pos + len(record.product)
            if new_records:
                last_record = new_records[-1]
                if last_record.building_id:
                    context.building_id = last_record.building_id
                    context.building_name = last_record.building_name
                if last_record.room_id:
                    context.room_id = last_record.room_id
                    context.room_name = last_record.room_name
            logger.info(
                f"Extracted {len(new_records)} records from chunk "
                f"{current_index + 1}/{len(chunks)} (fallback parser)"
            )
            if pl:
                total_so_far = len(existing_records) + len(new_records)
                progress = (current_index + 1) / len(chunks) if chunks else 1.0
                pl.stage_progress(
                    StageId.EXTRACT,
                    f"Chunk {current_index + 1}/{len(chunks)} | pages {page_number}+ | "
                    f"{len(new_records)} records | {total_so_far} total (fallback)",
                    progress=progress,
                    records_so_far=total_so_far,
                    chunk=f"{current_index + 1}/{len(chunks)}",
                )
            return {
                "records": existing_records + new_records,
                "context": context,
                "current_chunk_index": current_index + 1,
                "extraction_result": result,
                "retry_count": 0,
            }
        except (ValueError, ValidationError) as fallback_err:
            logger.warning(
                f"Fallback JSON parsing failed for source={source_id} "
                f"chunk={current_index + 1}/{len(chunks)}: {fallback_err}. "
                f"Response preview: {response_text[:300]!r}"
            )

    if retry_count < MAX_RETRIES:
        # Apply exponential backoff delay before retry
        delay = (
            RETRY_DELAYS[retry_count]
            if retry_count < len(RETRY_DELAYS)
            else RETRY_DELAYS[-1]
        )
        logger.info(f"Retrying in {delay}s (attempt {retry_count + 1}/{MAX_RETRIES})")
        await asyncio.sleep(delay)
        return {
            "retry_count": retry_count + 1,
            "error": None,  # Clear error to allow retry
        }
    return {
        "error": f"Extraction {_error_type} failed after {MAX_RETRIES} retries: {_exc}"
    }


async def validate_records(state: dict, config: RunnableConfig) -> dict:
    """Validate extracted records and apply guardrails."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())

    if not records:
        logger.info("No records to validate")
        return {"records": [], "records_rejected": 0}

    validated_records = []
    rejected_count = 0

    for record in records:
        issues = list(record.data_issues) if record.data_issues else []

        # Check required fields
        if not record.building_id:
            issues.append("Missing required field: building_id")
        if not record.product:
            issues.append("Missing required field: product")
        if not record.material_description:
            issues.append("Missing required field: material_description")

        # If missing building_id, try to use context
        if not record.building_id and context.building_id:
            record.building_id = context.building_id
            issues.append("Building ID inferred from context")

        # Normalize result field to BAR vocabulary
        # Order matters: check negative compound terms before simple "detected"
        if record.result:
            result_lower = record.result.lower()
            if (
                "assumed positive" in result_lower
                or "presumed positive" in result_lower
            ):
                record.result = "Assumed Positive"
            elif (
                "assumed negative" in result_lower
                or "presumed negative" in result_lower
            ):
                record.result = "Assumed Negative"
            elif any(
                x in result_lower
                for x in ["no asbestos", "nad", "not detected", "negative"]
            ):
                record.result = "Negative"
            elif any(
                x in result_lower
                for x in ["positive", "detected", "asbestos-containing"]
            ):
                record.result = "Positive"
            elif "presumed" in result_lower:
                # Use sample_result to disambiguate bare "presumed" results
                sr = (record.sample_result or "").lower()
                if "negative" in sr:
                    record.result = "Assumed Negative"
                else:
                    record.result = "Assumed Positive"
            else:
                record.result = "Unknown"
        else:
            record.result = "Unknown"
            issues.append("Result field was empty, set to Unknown")

        # Validate confidence value
        if record.extraction_confidence not in {"high", "medium", "low"}:
            record.extraction_confidence = "medium"
            issues.append("Invalid confidence value normalized to medium")

        # Update issues
        record.data_issues = issues

        # Reject records missing critical fields
        if (
            not record.building_id
            or not record.product
            or not record.material_description
        ):
            rejected_count += 1
            logger.warning(f"Rejected record due to missing required fields: {issues}")
            continue

        validated_records.append(record)

    if rejected_count > 0:
        logger.info(
            f"Validated {len(validated_records)} records, rejected {rejected_count}"
        )

    return {"records": validated_records, "records_rejected": rejected_count}


async def validate_records_strict(state: dict, config: RunnableConfig) -> dict:
    """Validate extracted records against BAR enum values and business rules.

    Uses acm_validator for strict validation. Records with issues are flagged
    for correction by the corrective loop.

    Story: E1-S15 Corrective RAG Validation Loop
    """
    records: List[ACMExtractionRecord] = state.get("records", [])
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)
    operation_id: Optional[str] = state.get("operation_id")
    _validate_start = time.time()

    # Log EXTRACT stage complete on first validation pass (marks end of extraction)
    correction_attempt = state.get("correction_attempt", 0)
    if agui and correction_attempt == 0:
        await agui.emit_step_started("validate")
    if pl and correction_attempt == 0:
        pl.stage_complete(
            StageId.EXTRACT,
            f"{len(records)} raw records extracted",
            record_count=len(records),
        )
        pl.stage_enter(StageId.VALIDATE, f"Validating {len(records)} records...")

    correction_stats = state.get(
        "correction_stats",
        {
            "auto_corrected": 0,
            "llm_corrected": 0,
            "failed": 0,
            "total_validated": 0,
        },
    )

    # Extraction completeness check: count room headers vs extracted records
    content = state.get("content", "")
    if content and correction_attempt == 0:
        room_pattern = re.compile(r"B\d{3}\s*-\s*R\d{4,5}")
        expected_rooms = len(set(room_pattern.findall(content)))
        extracted_count = len(records)
        if expected_rooms > 0:
            completeness_pct = (extracted_count / expected_rooms) * 100
            if extracted_count < expected_rooms:
                logger.warning(
                    f"COMPLETENESS GAP: Extracted {extracted_count}/{expected_rooms} "
                    f"room records ({completeness_pct:.0f}%) — "
                    f"{expected_rooms - extracted_count} records may be missing"
                )
            else:
                logger.info(
                    f"Completeness check: {extracted_count}/{expected_rooms} "
                    f"room records ({completeness_pct:.0f}%)"
                )
            if pl:
                pl.stage_progress(
                    StageId.VALIDATE,
                    f"Completeness: {extracted_count}/{expected_rooms} ({completeness_pct:.0f}%)",
                    expected_rooms=expected_rooms,
                    extracted_count=extracted_count,
                    completeness_pct=round(completeness_pct, 1),
                )

    if not records:
        logger.info("No records to validate")
        return {"records": [], "records_rejected": 0}

    validated_records = []
    rejected_count = 0
    records_with_issues: List[Dict[str, Any]] = []

    for record in records:
        issues = list(record.data_issues) if record.data_issues else []

        # Check required fields
        if not record.building_id:
            if context.building_id:
                record.building_id = context.building_id
                issues.append("Building ID inferred from context")
            else:
                issues.append("Missing required field: building_id")

        if not record.product:
            issues.append("Missing required field: product")
        if not record.material_description:
            issues.append("Missing required field: material_description")

        # Validate confidence value
        if record.extraction_confidence not in {"high", "medium", "low"}:
            record.extraction_confidence = "medium"
            issues.append("Invalid confidence value normalized to medium")

        record.data_issues = issues

        # Reject records missing critical fields
        if (
            not record.building_id
            or not record.product
            or not record.material_description
        ):
            rejected_count += 1
            logger.warning(f"Rejected record due to missing required fields: {issues}")
            continue

        # Run strict enum + business rule validation
        record_dict = {
            "sample_result": record.sample_result or record.result,
            "material_condition": record.material_condition,
            "friable": record.friable,
            "disturbance_potential": record.disturbance_potential,
            "building_id": record.building_id,
            "product": record.product,
            "material_description": record.material_description,
        }
        validation = validate_acm_record(record_dict)
        correction_stats["total_validated"] = (
            correction_stats.get("total_validated", 0) + 1
        )

        # AC6: Write validation fields to record
        if validation.is_valid:
            record.validation_status = "valid"
            record.validation_errors = []
        else:
            record.validation_status = "invalid"
            record.validation_errors = [
                f"{vi.field_name}: {vi.issue_type} (current={vi.current_value!r})"
                for vi in validation.issues
            ]

        if not validation.is_valid:
            # Track issues on the record for potential correction
            for vi in validation.issues:
                if vi.issue_type in ("enum_mismatch", "business_rule"):
                    record.data_issues.append(
                        f"Validation: {vi.field_name}='{vi.current_value}' "
                        f"({vi.issue_type})"
                    )
            records_with_issues.append(
                {
                    "record_index": len(validated_records),
                    "issues": [i.model_dump() for i in validation.issues],
                }
            )

        validated_records.append(record)

    if rejected_count > 0:
        logger.info(
            f"Validated {len(validated_records)} records, rejected {rejected_count}"
        )

    if records_with_issues:
        logger.info(f"Found {len(records_with_issues)} records with validation issues")

    if pl:
        # Build rejection reason summary
        rejection_reasons = []
        if rejected_count > 0:
            rejection_reasons.append(f"missing_fields={rejected_count}")
        if records_with_issues:
            rejection_reasons.append(f"issues={len(records_with_issues)}")

        pl.stage_complete(
            StageId.VALIDATE,
            f"{len(validated_records)} accepted, {rejected_count} rejected",
            accepted=len(validated_records),
            rejected=rejected_count,
            with_issues=len(records_with_issues),
        )

    if agui:
        await agui.emit_state_delta(
            [
                {
                    "op": "replace",
                    "path": "/validation_result",
                    "value": {
                        "accepted": len(validated_records),
                        "rejected": rejected_count,
                    },
                }
            ]
        )
        await agui.emit_step_finished(
            "validate", accepted=len(validated_records), rejected=rejected_count
        )

    # E34-S1: Publish ai.validation_complete event on the final validation pass only.
    # validate_records_strict is called once per correction loop iteration; only
    # publish the terminal event when no more corrections will run.
    _is_final_validation = rejected_count == 0 or (
        state.get("correction_attempt", 0) >= state.get("max_correction_attempts", 2)
    )
    if operation_id and _is_final_validation:
        try:
            _validation_duration_ms = int((time.time() - _validate_start) * 1000)
            _records_corrected = (
                correction_stats.get("auto_corrected", 0)
                + correction_stats.get("llm_corrected", 0)
            )
            await get_event_bus().publish(
                AIValidationCompleteEvent(
                    operation_id=operation_id,
                    data=AIValidationCompleteData(
                        records_valid=len(validated_records),
                        records_corrected=_records_corrected,
                        records_rejected=rejected_count,
                        validation_duration_ms=_validation_duration_ms,
                    ),
                )
            )
        except Exception as _pub_err:
            logger.debug(
                f"[E34-S1] Failed to publish ai.validation_complete: {_pub_err}"
            )

    return {
        "records": validated_records,
        "records_rejected": rejected_count,
        "correction_stats": correction_stats,
    }


async def correct_records(state: dict, config: RunnableConfig) -> dict:
    """Apply corrections to records with validation issues.

    Two-layer correction strategy:
    1. Layer 1 (fast, deterministic): Apply normalize_enum_value() for known synonyms
    2. Layer 2 (slow, LLM-based): Call LLM with correction prompt for remaining issues

    Story: E1-S15 Corrective RAG Validation Loop
    """
    records: List[ACMExtractionRecord] = state.get("records", [])
    correction_attempt = state.get("correction_attempt", 0)
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_enter(
            StageId.CORRECT,
            f"Correction attempt {correction_attempt + 1}...",
        )
    if agui:
        await agui.emit_step_started("correct")
    correction_stats = state.get(
        "correction_stats",
        {
            "auto_corrected": 0,
            "llm_corrected": 0,
            "failed": 0,
            "total_validated": 0,
        },
    )
    model_id = state.get("model_id")

    if not records:
        return {"records": [], "correction_attempt": correction_attempt + 1}

    # Field name mapping for normalize_enum_value
    enum_fields = {
        "sample_result": "sample_result",
        "material_condition": "condition",
        "friable": "friability",
        "disturbance_potential": "disturbance_potential",
    }

    records_needing_llm: List[int] = []

    for i, record in enumerate(records):
        record_dict = {
            "sample_result": record.sample_result or record.result,
            "material_condition": record.material_condition,
            "friable": record.friable,
            "disturbance_potential": record.disturbance_potential,
            "building_id": record.building_id,
            "product": record.product,
            "material_description": record.material_description,
        }
        validation = validate_acm_record(record_dict)

        if validation.is_valid:
            continue

        # Compute SF-valid fields to freeze (AC2 — E35-S7)
        from open_notebook.extractors.validators.acm_validator import sf_valid_fields

        frozen_fields = sf_valid_fields(record_dict)

        # Layer 1: Try deterministic normalization first
        still_invalid = []
        for issue in validation.issues:
            # Skip frozen fields — SF-valid values must not be overwritten
            if issue.field_name in frozen_fields:
                logger.info(
                    f"Skipping correction of {issue.field_name}="
                    f"'{issue.current_value}' — field is SF-valid (frozen)"
                )
                continue

            if issue.issue_type not in ("enum_mismatch", "invalid_sf_enum"):
                still_invalid.append(issue)
                continue

            field = issue.field_name
            normalizer_field = enum_fields.get(field, field)
            current_val = issue.current_value

            normalized = normalize_enum_value(current_val, normalizer_field)
            if normalized != current_val and normalized in (issue.valid_values or []):
                # Layer 1 success — apply correction
                logger.info(
                    f"Corrected {field}: '{current_val}' -> '{normalized}' "
                    f"via normalizer (attempt {correction_attempt + 1})"
                )
                _apply_field_correction(record, field, normalized)
                correction_stats["auto_corrected"] = (
                    correction_stats.get("auto_corrected", 0) + 1
                )
            else:
                still_invalid.append(issue)

        if still_invalid:
            records_needing_llm.append(i)

    # Layer 2: LLM correction for remaining issues
    if records_needing_llm:
        try:
            if pl:
                logger.info("[PIPELINE] Prompt template: acm/correction")
            await _llm_correct_records(
                records,
                records_needing_llm,
                correction_stats,
                model_id,
                correction_attempt,
                pl=pl,
            )
        except Exception as e:
            logger.warning(f"LLM correction failed: {e}")
            for idx in records_needing_llm:
                correction_stats["failed"] = correction_stats.get("failed", 0) + 1

    if pl:
        auto = correction_stats.get("auto_corrected", 0)
        llm = correction_stats.get("llm_corrected", 0)
        failed = correction_stats.get("failed", 0)
        pl.stage_complete(
            StageId.CORRECT,
            f"auto={auto}, llm={llm}, failed={failed}",
            auto_corrected=auto,
            llm_corrected=llm,
            failed=failed,
        )
    if agui:
        await agui.emit_step_finished(
            "correct",
            auto_corrected=correction_stats.get("auto_corrected", 0),
            llm_corrected=correction_stats.get("llm_corrected", 0),
        )

    return {
        "records": records,
        "correction_attempt": correction_attempt + 1,
        "correction_stats": correction_stats,
    }


def _apply_field_correction(
    record: ACMExtractionRecord, field_name: str, value: str
) -> None:
    """Apply a corrected value to an extraction record field."""
    if field_name == "sample_result":
        record.sample_result = value
    elif field_name == "material_condition":
        record.material_condition = value
    elif field_name == "friable":
        record.friable = value
    elif field_name == "disturbance_potential":
        record.disturbance_potential = value


async def _llm_correct_records(
    records: List[ACMExtractionRecord],
    record_indices: List[int],
    correction_stats: Dict[str, int],
    model_id: Optional[str],
    correction_attempt: int,
    pl: Optional[PipelineLogger] = None,
) -> None:
    """Use LLM to correct records that failed Layer 1 normalization.

    SF-valid fields are frozen and excluded from the correction prompt.
    Any LLM response that attempts to modify a frozen field is rejected.

    Story: E35-S7 — SF-First Validation Pipeline (field freezing).
    """
    import json

    from open_notebook.extractors.validators.acm_validator import (
        sf_valid_fields,
        validate_acm_record,
    )

    enum_fields = {
        "sample_result": "sample_result",
        "material_condition": "condition",
        "friable": "friability",
        "disturbance_potential": "disturbance_potential",
    }

    for idx in record_indices:
        record = records[idx]
        record_dict = {
            "sample_result": record.sample_result or record.result,
            "material_condition": record.material_condition,
            "friable": record.friable,
            "disturbance_potential": record.disturbance_potential,
            "building_id": record.building_id,
            "product": record.product,
            "material_description": record.material_description,
        }
        validation = validate_acm_record(record_dict)

        if validation.is_valid:
            continue

        # Compute SF-valid fields to freeze (AC2 — E35-S7)
        frozen_fields = sf_valid_fields(record_dict)

        # Filter issues to exclude frozen fields from the correction prompt
        unfrozen_issues = [
            i for i in validation.issues if i.field_name not in frozen_fields
        ]

        if not unfrozen_issues:
            # All issues are on frozen fields — skip LLM correction
            continue

        # Build frozen_fields display dict for the template
        frozen_fields_display = {
            f: record_dict.get(f, "") for f in frozen_fields if record_dict.get(f)
        }

        # Render correction prompt
        prompter = Prompter(prompt_template="acm/correction")
        correction_prompt = prompter.render(
            data={
                "record_json": json.dumps(record_dict, indent=2, default=str),
                "validation_issues": [i.model_dump() for i in unfrozen_issues],
                "frozen_fields": frozen_fields_display,
            }
        )

        # Detect Qwen2.5 before provisioning so temperature is set at construction time.
        # Pydantic v2 frozen models silently ignore post-construction attribute assignment.
        _correction_qwen = False
        if model_id:
            try:
                _correction_domain_model = await Model.get(model_id)
                _correction_qwen = (
                    "qwen2.5" in (_correction_domain_model.name or "").lower()
                )
            except Exception:
                pass  # fallback: temperature=0.1 is safe default

        try:
            model = await provision_langchain_model(
                correction_prompt,
                model_id,
                "extraction",
                temperature=0.0 if _correction_qwen else 0.1,
                max_tokens=1024,
            )
            # Track resolved model for observability (E1-S21, AC #4)
            if pl:
                actual_model = (
                    getattr(model, "model_name", None)
                    or getattr(model, "model", None)
                    or model_id
                    or "default_extraction_model"
                )
                pl.log_model(str(actual_model), "correction")

            messages = [
                SystemMessage(content=correction_prompt),
                HumanMessage(content="Correct the invalid field values as instructed."),
            ]

            response = await model.ainvoke(messages)

            # E27-S3: Verify provider routing (non-blocking)
            try:
                await _verify_provider_routing(response, "correction")
            except Exception:
                pass

            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Strip markdown code block wrappers if present
            text = response_text.strip()
            if text.startswith("```"):
                # Remove opening ```json or ``` line
                first_newline = text.index("\n") if "\n" in text else len(text)
                text = text[first_newline + 1 :]
                # Remove closing ```
                if text.rstrip().endswith("```"):
                    text = text.rstrip()[:-3].rstrip()

            # Parse JSON response
            corrected = json.loads(text)
            if isinstance(corrected, dict):
                for field, value in corrected.items():
                    # Reject corrections to frozen fields (AC2 — E35-S7)
                    if field in frozen_fields:
                        logger.warning(
                            f"LLM attempted to modify frozen field {field} "
                            f"(SF-valid), ignoring correction"
                        )
                        continue
                    if field in enum_fields and value:
                        old_val = getattr(record, field, None) or record_dict.get(field)
                        _apply_field_correction(record, field, value)
                        logger.info(
                            f"Corrected {field}: '{old_val}' -> '{value}' "
                            f"via LLM (attempt {correction_attempt + 1})"
                        )
                        correction_stats["llm_corrected"] = (
                            correction_stats.get("llm_corrected", 0) + 1
                        )
            # AC6: Track correction attempts on record
            record.correction_attempts = record.correction_attempts + 1
            record.validation_status = "corrected"

        except Exception as e:
            logger.warning(f"LLM correction failed for record {idx}: {e}")
            correction_stats["failed"] = correction_stats.get("failed", 0) + 1
            record.correction_attempts = record.correction_attempts + 1  # AC6
            record.validation_status = "failed_correction"


def should_correct(state: dict) -> str:
    """Route to correction or continue to deduplication.

    Story: E1-S15 Corrective RAG Validation Loop
    """
    if not state.get("enable_corrective_loop", True):
        return "deduplicate"

    records: List[ACMExtractionRecord] = state.get("records", [])
    attempt = state.get("correction_attempt", 0)
    max_attempts = state.get("max_correction_attempts", 2)

    if attempt >= max_attempts:
        return "deduplicate"

    # Check if any records have validation issues
    enum_fields = [
        "sample_result",
        "material_condition",
        "friable",
        "disturbance_potential",
    ]
    for record in records:
        record_dict = {
            "sample_result": record.sample_result or record.result,
            "material_condition": record.material_condition,
            "friable": record.friable,
            "disturbance_potential": record.disturbance_potential,
            "building_id": record.building_id,
            "product": record.product,
            "material_description": record.material_description,
        }
        validation = validate_acm_record(record_dict)
        if not validation.is_valid:
            # Filter to only correctable issues
            # (enum + business rule + SF enum + SF chain)
            correctable = [
                i
                for i in validation.issues
                if i.issue_type
                in (
                    "enum_mismatch",
                    "business_rule",
                    "invalid_sf_enum",
                    "sf_chain",
                    "invalid_chain_value",
                )
            ]
            if correctable:
                return "correct"

    return "deduplicate"


async def deduplicate_records(state: dict, config: RunnableConfig) -> dict:
    """Deduplicate records using composite key."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if agui:
        await agui.emit_step_started("deduplicate")

    # Enter STORE stage here (dedup + save are both part of Enrich & Store)
    if pl:
        pl.stage_enter(
            StageId.STORE, f"Deduplicating and saving {len(records)} records..."
        )

    if not records:
        return {"records": []}

    seen: Dict[str, ACMExtractionRecord] = {}
    duplicates_merged = 0

    for record in records:
        key = _generate_dedup_key(record, context.school_code)

        if key in seen:
            # Merge with existing record
            seen[key] = _merge_records(seen[key], record)
            duplicates_merged += 1
        else:
            seen[key] = record

    deduplicated = list(seen.values())

    if duplicates_merged > 0:
        logger.info(f"Merged {duplicates_merged} duplicate records")

    if pl and duplicates_merged > 0:
        pl.stage_progress(
            StageId.STORE,
            f"Deduplicated: {duplicates_merged} merged, {len(deduplicated)} unique",
            duplicates_merged=duplicates_merged,
        )

    if agui:
        await agui.emit_state_delta(
            [{"op": "replace", "path": "/final_count", "value": len(deduplicated)}]
        )
        await agui.emit_step_finished(
            "deduplicate", unique=len(deduplicated), merged=duplicates_merged
        )

    return {"records": deduplicated}


def _recover_no_access_records(
    full_text: str,
    extracted_records: List[ACMExtractionRecord],
    building_id: str,
    building_name: str,
) -> List[ACMExtractionRecord]:
    """Post-LLM fallback: scan full_text for 'No Access' entries not captured.

    Targets the known pattern where register continuation rows on overflow
    pages (e.g., page 8 of Broadmeadows) are below Docling's table detection
    threshold and the LLM consistently skips them.

    The vertical PDF text format for these entries is:
        {Level}\\n{Room}\\n{Location}\\n{Product}\\n{dashes}\\nNo access...

    The function finds level indicators (e.g., "Ground\\nfloor") and scans
    forward to find "No access" phrases, extracting room/location/product
    from the lines between.

    Returns additional ACMExtractionRecord objects to append.
    """
    recovered: List[ACMExtractionRecord] = []

    no_access_re = re.compile(
        r"No\s+access|Height\s+restriction|Restricted\s+Access",
        re.IGNORECASE,
    )

    # Level indicators: lines that mark the start of a register row block
    level_re = re.compile(
        r"^(Ground|First|Second|Third|Level|Roof|Basement)\s*$", re.IGNORECASE
    )
    # Second line of level indicator
    level_suffix_re = re.compile(r"^(floor|level|\d)\s*$", re.IGNORECASE)

    # Build lookup of existing room+location combos (lowered)
    existing_combos = set()
    for r in extracted_records:
        room_norm = (r.room_name or "").lower().strip()
        loc_norm = (r.location or "").lower().strip()
        existing_combos.add((room_norm, loc_norm))

    lines = full_text.split("\n")

    # Scan for level-indicator lines, then check if their block has "no access"
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Check if this line is a level indicator
        if not level_re.match(stripped):
            i += 1
            continue

        level_name = stripped.title()

        # Check if next line is the level suffix (e.g., "floor")
        if i + 1 < len(lines) and level_suffix_re.match(lines[i + 1].strip()):
            level_name = f"{level_name} {lines[i + 1].strip().lower()}"
            block_start = i + 2
        else:
            block_start = i + 1

        # Collect content lines until we hit the next level indicator,
        # a page marker, or exceed a reasonable window
        content_lines: List[str] = []
        no_access_line: Optional[str] = None
        j = block_start
        while j < len(lines) and j < block_start + 30:
            line_s = lines[j].strip()

            # Stop at next level indicator or page boundary
            if level_re.match(line_s):
                break
            if line_s.startswith("--- Page"):
                break

            # Check for "No access" phrase
            if no_access_re.search(line_s):
                no_access_line = line_s
                break

            # Collect non-empty, non-dash lines as content
            if line_s and line_s not in ("-", "–", " -"):
                content_lines.append(line_s)

            j += 1

        # If no "no access" found in this block, skip
        if no_access_line is None:
            i = block_start
            continue

        # Advance past this block
        i = j + 1

        # Parse content_lines: [room, location_parts..., product]
        # In the vertical register format, the product (ACM item) is the last
        # meaningful line before the dashes. But multi-word locations can span
        # several lines, so we check if the last line is a known ACM product.
        KNOWN_PRODUCT_KEYWORDS = {
            "lining",
            "cladding",
            "insulation",
            "lagging",
            "sheeting",
            "covering",
            "coverings",
            "tiles",
            "cartridge",
            "gasket",
            "eaves",
            "soffit",
            "mastic",
            "joint",
            "joints",
            "door",
            "panel",
            "board",
            "coating",
            "millboard",
            "packing",
            "gutter",
            "downpipe",
            "cistern",
            "pipe",
            "duct",
        }

        if len(content_lines) < 1:
            continue

        room_name = content_lines[0]

        if len(content_lines) >= 3:
            candidate_product = content_lines[-1]
            # Check if last line looks like a known ACM product
            words = candidate_product.lower().split()
            if any(w in KNOWN_PRODUCT_KEYWORDS for w in words):
                product_val = candidate_product
                location_val = " ".join(content_lines[1:-1])
            else:
                # Last line is part of multi-word location, product unknown
                product_val = "Unknown"
                location_val = " ".join(content_lines[1:])
        elif len(content_lines) == 2:
            candidate = content_lines[1]
            words = candidate.lower().split()
            if any(w in KNOWN_PRODUCT_KEYWORDS for w in words):
                product_val = candidate
                location_val = "Unknown"
            else:
                location_val = candidate
                product_val = "Unknown"
        else:
            location_val = "Unknown"
            product_val = "Unknown"

        # If product is a dash or empty, set Unknown
        if product_val.strip() in ("-", "–", ""):
            product_val = "Unknown"

        # Check if this room+location already exists in extracted records
        room_norm = room_name.lower().strip()
        loc_norm = location_val.lower().strip()
        if (room_norm, loc_norm) in existing_combos:
            continue

        # Also check against already-recovered records
        if (room_norm, loc_norm) in {
            ((r.room_name or "").lower().strip(), (r.location or "").lower().strip())
            for r in recovered
        }:
            continue

        no_access_comment = no_access_line.strip().rstrip(".")

        recovered.append(
            ACMExtractionRecord(
                building_id=building_id,
                building_name=building_name,
                room_name=room_name.title(),
                location=location_val,
                product=product_val,
                material_description=product_val or "Unknown",
                result="Assumed Positive",
                sample_result="Assumed Positive",
                sample_no="Not Sampled",
                no_access=True,
                extraction_confidence="low",
                data_issues=[
                    f"No access — recovered by post-LLM fallback ({no_access_comment})"
                ],
                area_type="Interior",
                floor_level=level_name,
            )
        )
        logger.info(
            f"Recovered no-access record: {room_name} / {location_val} / {product_val}"
        )

    # ── ARA Format Scan (E28-S2) ──────────────────────────────────────────
    # ARA (Asbestos Risk Assessment) format uses a different text layout:
    #   {item_no}\n{room}\n{desc}\nAsbestos\nNot Sampled\n{restriction}\nPresumed Positive
    # The SAMP-specific level_re above won't match ARA section headers like
    # "Mortuary Buildings - Interior - Ground Level". This scan finds
    # "Not Sampled" lines and works backward/forward to extract the record.
    ara_recovered = _recover_not_sampled_records_ara(
        full_text, extracted_records + recovered, building_id, building_name
    )
    recovered.extend(ara_recovered)

    return recovered


def _recover_not_sampled_records_ara(
    full_text: str,
    existing_records: List[ACMExtractionRecord],
    default_building_id: str,
    default_building_name: str,
) -> List[ACMExtractionRecord]:
    """ARA-format recovery for unsampled items missed by LLM.

    Runs on orchestrator path (multi-building documents like Alexander).
    Complements the SAMP-path scan in ``_recover_no_access_records()``.

    ARA "Not Sampled" entries follow a consistent vertical text pattern::

        {item_number}
        {room_name}
        {item_description} - {material}
        Asbestos
        Not Sampled
        {access_restriction}   (Restricted Access / Height Restricted / Live Electrical Hazard)
        Presumed Positive

    The function locates every "Not Sampled" line, verifies "Asbestos" appears
    just above it and "Presumed Positive" just below, then extracts room/product
    from the lines between the item number and "Asbestos".
    """
    recovered: List[ACMExtractionRecord] = []

    # Build dedup lookup: (room_norm, product_norm) to avoid duplicating
    # records the LLM already captured. Use room+product instead of
    # room+location because ARA's "location" field is less standardized.
    existing_combos: set[tuple[str, str]] = set()
    for r in existing_records:
        room_norm = (r.room_name or "").lower().strip()
        product_norm = (r.product or "").lower().strip()
        existing_combos.add((room_norm, product_norm))
        # Also add location-based combo for broader dedup
        loc_norm = (r.location or "").lower().strip()
        existing_combos.add((room_norm, loc_norm))

    # ARA section header pattern: "Building Name - Interior/Exterior - Level"
    section_header_re = re.compile(
        r"^(.+?)\s*-\s*(Interior|Exterior)\s*-\s*(.+)$", re.IGNORECASE
    )

    lines = full_text.split("\n")
    current_building = default_building_name
    current_area_type = "Interior"

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Track ARA section headers for building context
        header_match = section_header_re.match(stripped)
        if header_match:
            current_building = header_match.group(1).strip()
            current_area_type = header_match.group(2).strip()
            i += 1
            continue

        # Look for "Not Sampled" lines
        if stripped != "Not Sampled":
            i += 1
            continue

        not_sampled_line = i

        # Verify "Asbestos" appears within 5 lines above
        asbestos_line = None
        for back in range(1, 6):
            if not_sampled_line - back < 0:
                break
            if lines[not_sampled_line - back].strip().lower() == "asbestos":
                asbestos_line = not_sampled_line - back
                break

        if asbestos_line is None:
            i += 1
            continue

        # Verify restriction + "Presumed Positive" appear within 3 lines below
        restriction = None
        presumed_positive = False
        for fwd in range(1, 4):
            if not_sampled_line + fwd >= len(lines):
                break
            fwd_stripped = lines[not_sampled_line + fwd].strip()
            if re.match(
                r"Restricted\s+Access|Height\s+Restricted|Live\s+Electrical",
                fwd_stripped,
                re.IGNORECASE,
            ):
                restriction = fwd_stripped
            if fwd_stripped.lower() == "presumed positive":
                presumed_positive = True

        if not presumed_positive:
            i += 1
            continue

        # Extract room/product from lines between item_number and "Asbestos"
        # Scan backward from asbestos_line to find the item number
        item_number = None
        content_lines: List[str] = []
        for back_idx in range(asbestos_line - 1, max(asbestos_line - 10, -1), -1):
            if back_idx < 0:
                break
            back_line = lines[back_idx].strip()
            if not back_line or back_line in ("-", "\u2013", " -"):
                continue
            # Item number: bare integer on its own line
            if re.match(r"^\d+$", back_line):
                item_number = back_line
                break
            content_lines.insert(0, back_line)

        if not content_lines:
            i += 1
            continue

        # ARA item description patterns — detect where room ends and item
        # description starts. Item descriptions in ARA format have a
        # "{Product} - {Material}" pattern with the product being a specific
        # ACM item, not a room name.
        _ARA_ITEM_DESC_RE = re.compile(
            r"^(?:Fire\s+Door|Ceiling|Shower\s+Cubicle|Eaves|Ductwork|"
            r"Electrical\s+Distribution|Safe|Infill|Wall(?:\s|$)|"
            r"Pipe|Insulation|Window|Gable|Porch|Expansion|"
            r"Stored\s+Item|Heater|Shelving|Debris|Floor)\b",
            re.IGNORECASE,
        )

        # Split content_lines into room lines vs description lines.
        # Walk forward: lines are room continuation until we hit one that
        # matches an ARA item description pattern.
        room_lines: List[str] = []
        desc_lines: List[str] = []
        found_desc = False
        for cl in content_lines:
            if found_desc:
                desc_lines.append(cl)
                continue
            # Check if this line starts an item description
            is_desc = bool(_ARA_ITEM_DESC_RE.match(cl.strip()))
            if is_desc:
                found_desc = True
                desc_lines.append(cl)
            else:
                room_lines.append(cl)

        # If no description found, first line is room, rest is desc
        if not desc_lines and len(content_lines) >= 2:
            room_lines = [content_lines[0]]
            desc_lines = content_lines[1:]
        elif not desc_lines:
            room_lines = content_lines
            desc_lines = []

        room_name = " ".join(room_lines).strip()
        item_desc = " ".join(desc_lines).strip()

        if not item_desc:
            item_desc = room_name
            room_name = "Unknown"

        # Parse item description: "{product} - {material}" or just product
        product_val = item_desc
        material_val = None
        if " - " in item_desc:
            parts = item_desc.split(" - ", 1)
            product_val = parts[0].strip()
            material_val = parts[1].strip()

        # Parse ARA room: "External - Throughout" → room="Exterior", location_hint="Throughout"
        # "External - On Roof" → room="Roof"
        location_val = product_val
        room_clean = room_name
        if " - " in room_name:
            room_parts = room_name.split(" - ", 1)
            room_prefix = room_parts[0].strip()
            room_suffix = room_parts[1].strip()
            # "External - Throughout" → room=room_prefix, ignore "Throughout"
            # "External - On Roof" → room="Roof" (suffix is location hint)
            if room_prefix.lower() in ("external", "exterior"):
                # For exterior items, use product as the room context
                if room_suffix.lower().startswith("on "):
                    room_clean = room_suffix[3:].strip()  # "On Roof" → "Roof"
                elif room_suffix.lower() == "throughout":
                    room_clean = "Exterior"
                else:
                    room_clean = room_suffix
                location_val = product_val
            else:
                # Multi-part room name — keep the full name
                room_clean = room_name

        # Dedup check: room + product (and room + location)
        room_norm = room_clean.lower().strip()
        product_norm = product_val.lower().strip()
        loc_norm = location_val.lower().strip()
        if (room_norm, product_norm) in existing_combos:
            i += 1
            continue
        if (room_norm, loc_norm) in existing_combos:
            i += 1
            continue

        # Also check against already-recovered records
        already_recovered = {
            (
                (r.room_name or "").lower().strip(),
                (r.product or "").lower().strip(),
            )
            for r in recovered
        }
        if (room_norm, product_norm) in already_recovered:
            i += 1
            continue

        existing_combos.add((room_norm, product_norm))
        existing_combos.add((room_norm, loc_norm))

        restriction_comment = restriction or "Not Sampled"

        recovered.append(
            ACMExtractionRecord(
                building_id=default_building_id,
                building_name=current_building or default_building_name,
                room_name=room_clean,
                location=location_val,
                product=product_val,
                material_description=material_val or product_val,
                result="Assumed Positive",
                sample_result="Assumed Positive",
                sample_no="Not Sampled",
                no_access=True,
                extraction_confidence="low",
                data_issues=[
                    f"Not Sampled — recovered by ARA post-LLM fallback ({restriction_comment})"
                ],
                area_type=current_area_type,
            )
        )
        logger.info(
            f"ARA recovered not-sampled record: {room_clean} / {location_val} / {product_val} "
            f"(item {item_number}, {restriction_comment})"
        )

        i = not_sampled_line + 3  # Skip past Presumed Positive

    return recovered


async def recover_no_access_node(state: dict, config: RunnableConfig) -> dict:
    """Graph node: recover no-access records missed by LLM extraction."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    source: Source = state["source"]
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if agui:
        await agui.emit_step_started("recover_no_access")
    if pl:
        pl.stage_enter(
            StageId.NO_ACCESS_RECOVERY,
            f"Scanning for missed No Access records ({len(records)} existing)",
        )

    full_text = getattr(source, "full_text", "") or ""
    if not full_text:
        if pl:
            pl.stage_skip(StageId.NO_ACCESS_RECOVERY, "No full_text available")
        if agui:
            await agui.emit_step_finished("recover_no_access", recovered=0)
        return {"records": records}

    building_id = context.building_id or "unknown"
    building_name = context.building_name or ""

    recovered = _recover_no_access_records(
        full_text, records, building_id, building_name
    )

    if recovered:
        records = list(records) + recovered
        logger.info(f"Recovered {len(recovered)} no-access records via fallback")

    if pl:
        pl.stage_complete(
            StageId.NO_ACCESS_RECOVERY,
            summary=f"Recovery complete: {len(recovered)} records found",
            records_recovered=len(recovered),
        )
    if agui:
        await agui.emit_step_finished("recover_no_access", recovered=len(recovered))

    return {"records": records}


async def save_records(state: dict, config: RunnableConfig) -> dict:
    """Save validated records to the database."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    source: Source = state["source"]
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    start_time = state.get("start_time", time.time())
    records_rejected = state.get("records_rejected", 0)
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if agui:
        await agui.emit_step_started("save")
    if pl:
        pl.stage_progress(StageId.STORE, f"Saving {len(records)} records...")

    if not records:
        logger.info(f"No records to save for source {source.id}")
        extraction_time = int((time.time() - start_time) * 1000)
        return {
            "extraction_result": ACMExtractionResult(
                records=[],
                status=ExtractionStatus.NO_ACM_DATA,
                total_records=0,
                records_rejected=records_rejected,
            ),
            "error": None,
        }

    # Create parent table sections from building inventory (E11-S1)

    section_map: Dict[str, str] = {}  # building_id -> section_id
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    full_text = source.full_text or ""
    if inventory and inventory.buildings:
        for building in inventory.buildings:
            try:
                # Extract raw text for the page range from source content
                raw_text = _extract_page_range_text(
                    full_text,
                    building.page_start,
                    building.page_end or building.page_start,
                )
                section = ACMTableSection(
                    source_id=str(source.id),
                    page_start=building.page_start,
                    page_end=building.page_end or building.page_start,
                    building_name=f"{building.building_id} {building.name}"
                    if building.name
                    else building.building_id,
                    table_type="register",
                    raw_text=raw_text if raw_text else None,
                )
                await section.save()
                if section.id:
                    section_map[building.building_id] = str(section.id)
            except Exception as e:
                logger.warning(
                    f"Failed to create table section for building {building.building_id}: {e}"
                )

        if section_map:
            logger.info(
                f"Created {len(section_map)} parent table sections for source {source.id}"
            )

    saved_count = 0
    errors = []

    for record in records:
        try:
            # Resolve parent section (E11-S1)
            parent_id = section_map.get(record.building_id)

            # Convert extraction record to ACMRecord
            acm_record = ACMRecord(
                source_id=str(source.id),
                school_name=context.school_name or "Unknown School",
                school_code=context.school_code,
                building_id=record.building_id,
                building_name=record.building_name,
                building_year=record.building_year,
                building_construction=record.building_construction,
                building_record_id=record.building_record_id,  # E32-S2
                room_id=record.room_id,
                room_name=record.room_name,
                room_area=record.room_area,
                area_type=record.area_type or "Interior",
                floor_level=record.floor_level,
                date_of_inspection=record.date_of_inspection,
                product=record.product,
                material_description=record.material_description,
                extent=record.extent,
                location=record.location,
                friable=record.friable,
                material_condition=record.material_condition,
                risk_status=record.risk_status,
                result=record.result,
                page_number=record.page_number,
                parent_table_id=parent_id,
                # New AI extraction fields
                disturbance_potential=record.disturbance_potential,
                sample_no=record.sample_no,
                sample_result=record.sample_result,
                identifying_company=record.identifying_company,
                quantity=record.quantity,
                acm_labelled=record.acm_labelled,
                acm_label_details=record.acm_label_details,
                hygienist_recommendations=record.hygienist_recommendations,
                psb_supplied_acm_id=record.psb_supplied_acm_id,
                removal_status=record.removal_status,
                date_of_removal=record.date_of_removal,
                quantity_removed=record.quantity_removed,
                removal_notification_no=record.removal_notification_no,
                epa_certificate_no=record.epa_certificate_no,
                additional_comments=record.additional_comments,
                extraction_confidence=record.extraction_confidence,
                data_issues=record.data_issues if record.data_issues else None,
            )

            # Generate enriched text for contextual embedding (E1-S14)
            acm_record.enriched_text = acm_record.get_enriched_embedding_text()

            await acm_record.save()
            saved_count += 1

        except Exception as e:
            logger.error(f"Failed to save record: {e}")
            errors.append(str(e))

    extraction_time = int((time.time() - start_time) * 1000)

    # Build final result
    result = ACMExtractionResult(
        records=records,
        status=ExtractionStatus.VALID
        if saved_count > 0
        else ExtractionStatus.NO_ACM_DATA,
        total_records=saved_count,
        records_rejected=records_rejected,
    )
    result.update_stats()

    # Auto-fill SiteConfig from document metadata (E1-S19)
    document_metadata: Optional[DocumentMeta] = state.get("document_metadata")
    if document_metadata and saved_count > 0:
        try:
            await auto_populate_site_config(document_metadata, str(source.id))
        except Exception as e:
            logger.warning(f"SiteConfig auto-fill failed: {e}")

    # Log correction stats (E1-S15)
    correction_stats = state.get("correction_stats", {})
    if any(
        correction_stats.get(k, 0) > 0
        for k in ("auto_corrected", "llm_corrected", "failed")
    ):
        logger.info(
            f"Correction stats: auto={correction_stats.get('auto_corrected', 0)}, "
            f"llm={correction_stats.get('llm_corrected', 0)}, "
            f"failed={correction_stats.get('failed', 0)}, "
            f"total_validated={correction_stats.get('total_validated', 0)}"
        )

    logger.info(
        f"Saved {saved_count}/{len(records)} ACM records for source {source.id} "
        f"in {extraction_time}ms"
    )

    if pl:
        pl.stage_complete(
            StageId.STORE,
            f"{saved_count} saved, {len(section_map)} parent sections",
            record_count=saved_count,
            parent_sections=len(section_map),
            errors=len(errors),
        )

    if errors:
        return {
            "extraction_result": result,
            "error": f"Saved {saved_count} records, {len(errors)} failed: {errors[0]}",
        }

    return {
        "extraction_result": result,
        "error": None,
    }


def should_continue_extraction(state: dict) -> str:
    """Determine if we should continue extracting more chunks."""
    error = state.get("error")
    if error:
        return "error"

    chunks = state.get("chunks", [])
    current_index = state.get("current_chunk_index", 0)
    retry_count = state.get("retry_count", 0)

    # Check if we need to retry current chunk
    if retry_count > 0 and retry_count <= MAX_RETRIES:
        return "extract"

    # Check if there are more chunks
    if current_index < len(chunks):
        return "extract"

    return "validate"


def should_save(state: dict) -> str:
    """Determine if we should proceed to save."""
    error = state.get("error")
    if error:
        return "error"
    return "save"


# Build the graph
agent_state = StateGraph(ExtractionState)

# Add nodes
agent_state.add_node("extract_metadata", extract_metadata_node)  # E1-S19: Stage -2
agent_state.add_node("structure", extract_structure)  # E1-S16: Stage -1
agent_state.add_node("inventory", compile_inventory)  # E1-S17: Stage -1.5
agent_state.add_node("tag_pages", tag_page_sections)  # E1-S18: Stage -1.25
agent_state.add_node(
    "save_intelligence", save_intelligence_node
)  # E30-S9: Persist pre-extraction intelligence
agent_state.add_node(
    "extract_building", extract_building_node
)  # E32-S1: Building__c Phase 1 extraction
agent_state.add_node(
    "extract_items", extract_items_node
)  # E32-S2: Item__c Phase 2 extraction
agent_state.add_node(
    "orchestrate", orchestrate_with_logging
)  # E1-S20: Agentic orchestrator (wrapped with E1-S21 logging)
agent_state.add_node("prepare", prepare_context)
agent_state.add_node("extract", extract_records)
agent_state.add_node("validate", validate_records_strict)
agent_state.add_node("correct", correct_records)
agent_state.add_node("deduplicate", deduplicate_records)
agent_state.add_node("recover_no_access", recover_no_access_node)
agent_state.add_node("save", save_records)

# Add edges: START → extract_metadata → structure → inventory → tag_pages → prepare → ...
agent_state.add_edge(START, "extract_metadata")
agent_state.add_edge("extract_metadata", "structure")
agent_state.add_edge("structure", "inventory")
agent_state.add_edge("inventory", "tag_pages")
# E30-S9: Persist pre-extraction intelligence before orchestrator
agent_state.add_edge("tag_pages", "save_intelligence")
# E32-S1: Building__c extraction runs between save_intelligence and extract_items
agent_state.add_edge("save_intelligence", "extract_building")
# E32-S2: Item__c extraction runs after building extraction, with conditional fallback
agent_state.add_edge("extract_building", "extract_items")
agent_state.add_conditional_edges(
    "extract_items",
    should_run_orchestrate,
    {"orchestrate": "orchestrate", "validate": "validate"},
)
agent_state.add_edge("orchestrate", "validate")
# Legacy edges removed — prepare/extract nodes kept but unreachable (AC-5)
# Corrective RAG loop: validate → should_correct → {correct, deduplicate}
agent_state.add_conditional_edges(
    "validate", should_correct, {"correct": "correct", "deduplicate": "deduplicate"}
)
# After correction, re-validate
agent_state.add_edge("correct", "validate")
agent_state.add_edge("deduplicate", "recover_no_access")
agent_state.add_edge("recover_no_access", "save")
agent_state.add_edge("save", END)

# Compile the graph
graph = agent_state.compile()


async def extract_acm_from_source(
    source: Source,
    model_id: Optional[str] = None,
    force: bool = False,
    command_id: Optional[str] = None,
) -> ACMExtractionOutput:
    """
    Main entry point for ACM extraction.

    Args:
        source: Source document to extract from
        model_id: Optional specific model to use
        force: If True, delete existing records before extraction

    Returns:
        ACMExtractionOutput with results
    """
    start_time = time.time()
    source_id_str = str(source.id)

    langfuse_handler = get_langfuse_handler()
    langfuse_callbacks = append_langfuse_callback([], langfuse_handler)
    langfuse_metadata = build_langfuse_metadata(
        source_id=source_id_str,
        extraction_model=model_id,
        command_id=command_id,
    )

    # Initialize pipeline logger (E1-S21)
    # Use the shared _extract_total_pages utility (same pattern as the rest of the pipeline)
    # which handles: "--- Page N ---", "<!-- Page N -->", and "PAGE N OF M" formats.
    # Returns the highest page number seen (accurate for display) rather than a marker count.
    total_pages = _extract_total_pages(source.full_text) if source.full_text else 0
    if source.full_text and total_pages == 0:
        logger.warning(
            f"[PIPELINE] No page markers found in source {source.id} "
            f"({len(source.full_text)} chars). Page count will show 0 in logs. "
            "Chunking will fall back to character-based splitting."
        )
    pl = PipelineLogger(
        source_id=source_id_str,
        total_pages=total_pages,
        command_id=command_id,
        emit_custom_events=bool(langfuse_handler),
    )

    # Initialize AG-UI event emitter (E17-S1)
    agui: Optional[AGUIEventEmitter] = None
    if command_id:
        agui = AGUIEventEmitter(command_id=command_id, source_id=source_id_str)
        await agui.emit_run_started()

    if force:
        # Delete existing table sections and records (E11-S1)
        from open_notebook.domain.acm import ACMTableSection

        try:
            sections_deleted = await ACMTableSection.delete_by_source(source_id_str)
            if sections_deleted > 0:
                logger.info(
                    f"Deleted {sections_deleted} existing table sections for source {source.id}"
                )
        except Exception as e:
            logger.warning(f"Failed to delete table sections: {e}")

        deleted = await ACMRecord.delete_by_source(source_id_str)
        if deleted > 0:
            logger.info(
                f"Deleted {deleted} existing ACM records for source {source.id}"
            )

    # Run the extraction graph
    initial_state: ExtractionState = {
        "source": source,
        "content": "",
        "chunks": [],
        "current_chunk_index": 0,
        "context": BuildingRoomContext(),
        "records": [],
        "records_rejected": 0,
        "extraction_result": ACMExtractionResult(),
        "error": None,
        "model_id": model_id,
        "start_time": start_time,
        "retry_count": 0,
        # Corrective RAG loop (E1-S15)
        "correction_attempt": 0,
        "correction_stats": {
            "auto_corrected": 0,
            "llm_corrected": 0,
            "failed": 0,
            "total_validated": 0,
        },
        "enable_corrective_loop": True,
        "max_correction_attempts": 2,
        # Document structure (E1-S16)
        "document_structure": None,
        # Building inventory (E1-S17)
        "building_inventory": None,
        # Page tags (E1-S18)
        "page_tags": None,
        # Document metadata (E1-S19)
        "document_metadata": None,
        # Orchestrator stats (E1-S20)
        "orchestrator_stats": None,
        # Pipeline observability (E1-S21)
        "pipeline_logger": pl,
        # AG-UI event emitter (E17-S1)
        "agui_emitter": agui,
        # E34-S1: operation_id for PipelineEventBus streaming events
        "operation_id": command_id,
    }

    try:
        if langfuse_callbacks:
            result = await graph.ainvoke(
                initial_state,
                config={
                    "callbacks": langfuse_callbacks,
                    "metadata": langfuse_metadata,
                },
            )
        else:
            result = await graph.ainvoke(initial_state)

        extraction_result: ACMExtractionResult = result.get(
            "extraction_result", ACMExtractionResult()
        )
        error = result.get("error")

        extraction_time = int((time.time() - start_time) * 1000)

        # Extract correction stats for API consumers (AC #8)
        correction_stats = result.get("correction_stats")
        has_corrections = correction_stats and any(
            correction_stats.get(k, 0) > 0
            for k in ("auto_corrected", "llm_corrected", "failed")
        )

        # Extract orchestrator stats (E1-S20)
        orch_stats = result.get("orchestrator_stats")
        orch_stats_dict = orch_stats.model_dump() if orch_stats else None

        if error:
            # Pipeline failed — emit summary
            if agui:
                await agui.emit_run_error(error)
            pipeline_run = pl.fail(error)
            return ACMExtractionOutput(
                source_id=source_id_str,
                status="failed",
                total_records=0,
                records_failed=extraction_result.records_rejected,
                error=error,
                extraction_time_ms=extraction_time,
                correction_stats=correction_stats if has_corrections else None,
                orchestrator_stats=orch_stats_dict,
                pipeline_run=pipeline_run.model_dump(mode="json"),
            )

        status = "success" if extraction_result.total_records > 0 else "no_data"

        # Gather building and strategy info for summary
        inventory = result.get("building_inventory")
        total_buildings = inventory.total_buildings if inventory else 0
        total_chunks = len(result.get("chunks", []))
        conf_dist = extraction_result.confidence_distribution
        conf_dict = {
            "high": conf_dist.high,
            "medium": conf_dist.medium,
            "low": conf_dist.low,
        }
        strategy_dist = None
        if orch_stats:
            strategy_dist = getattr(orch_stats, "strategy_distribution", None)

        # AG-UI: emit RunFinished
        if agui:
            await agui.emit_run_finished(total_records=extraction_result.total_records)

        # Pipeline complete — emit summary
        pipeline_run = pl.complete(
            total_records=extraction_result.total_records,
            records_rejected=extraction_result.records_rejected,
            confidence_distribution=conf_dict,
            total_chunks=total_chunks,
            total_buildings=total_buildings,
            strategy_distribution=strategy_dist,
        )

        # Token limit assessment (E1-S23)
        token_limit_exceeded = False
        chunk_count = max(total_chunks, 1)
        content = result.get("content", "")
        if content:
            validator = TokenLimitValidator(
                model_id=model_id or "unknown",
                context_window=DEFAULT_CONTEXT_WINDOW,
            )
            assessment = validator.assess_extraction(
                content=content,
                chunks_used=chunk_count,
                records_extracted=extraction_result.total_records,
            )
            token_limit_exceeded = assessment["token_limit_exceeded"]

        return ACMExtractionOutput(
            source_id=source_id_str,
            status=status,
            total_records=extraction_result.total_records,
            records_failed=extraction_result.records_rejected,
            confidence_distribution=extraction_result.confidence_distribution,
            extraction_time_ms=extraction_time,
            correction_stats=correction_stats if has_corrections else None,
            orchestrator_stats=orch_stats_dict,
            pipeline_run=pipeline_run.model_dump(mode="json"),
            token_limit_exceeded=token_limit_exceeded,
            chunk_count=chunk_count,
        )

    except Exception as e:
        logger.exception(f"ACM extraction failed for source {source.id}")
        extraction_time = int((time.time() - start_time) * 1000)
        if agui:
            await agui.emit_run_error(str(e))
        pipeline_run = pl.fail(str(e))
        return ACMExtractionOutput(
            source_id=source_id_str,
            status="failed",
            total_records=0,
            records_failed=0,
            error=str(e),
            extraction_time_ms=extraction_time,
            pipeline_run=pipeline_run.model_dump(mode="json"),
        )
    finally:
        flush_langfuse_handler(langfuse_handler)
