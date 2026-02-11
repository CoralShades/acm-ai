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
from pydantic import ValidationError
from typing_extensions import TypedDict

from open_notebook.domain.acm import ACMRecord
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
from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    compile_building_inventory,
)
from open_notebook.extractors.document_structure import (
    DocumentStructure,
    extract_document_structure,
)
from open_notebook.extractors.metadata_extractor import (
    auto_populate_site_config,
    extract_document_metadata,
)
from open_notebook.extractors.normalizers.enums import normalize_enum_value
from open_notebook.extractors.orchestrator import (
    OrchestratorStats,
    orchestrate_extraction,
    should_use_orchestrator,
)
from open_notebook.extractors.page_tagger import (
    PageTaggingResult,
    tag_pages,
)
from open_notebook.extractors.parsers.base import DocumentMeta
from open_notebook.extractors.pipeline_events import StageId
from open_notebook.extractors.pipeline_logger import PipelineLogger
from open_notebook.extractors.validators.acm_validator import (
    CorrectionStats,
    validate_acm_record,
)
from open_notebook.graphs.utils import provision_langchain_model
from open_notebook.utils import token_count

# Constants
CHUNK_THRESHOLD_RATIO = 0.5  # Chunk if content > 50% of context window
DEFAULT_CONTEXT_WINDOW = 128000  # Default context window (GPT-4o-mini)
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds

# Chunking constants (for when no page markers exist)
CHARS_PER_TOKEN_ESTIMATE = 4  # Approximate characters per token for chunking
CHUNK_OVERLAP_CHARS = 500  # Overlap between chunks to preserve context


def _extract_acm_register_section(content: str) -> Tuple[str, bool]:
    """
    Extract just the ACM Register section from a SAMP document.

    SAMP documents have lots of boilerplate text before the actual ACM Register.
    This function finds and extracts just the relevant section.

    Returns:
        Tuple of (extracted_content, was_extracted)
    """
    # Look for common markers that indicate start of ACM Register section
    start_markers = [
        "Appendix B: Asbestos Register",
        "Appendix B - Asbestos Register",
        "Asbestos Register",
        "Interior",  # Often the first area type in the register
    ]

    # Look for building pattern which indicates start of actual data
    building_pattern = r"(B\d{3}\s*-\s*[A-Za-z])"

    start_idx = -1

    # Try to find a good starting point
    for marker in start_markers:
        idx = content.find(marker)
        if idx != -1:
            start_idx = idx
            break

    # If no marker found, try to find the first building ID pattern
    if start_idx == -1:
        match = re.search(building_pattern, content)
        if match:
            # Go back a bit to include potential headers
            start_idx = max(0, match.start() - 200)

    if (
        start_idx != -1 and start_idx > 500
    ):  # Only extract if there's significant boilerplate
        extracted = content[start_idx:]
        acm_debug(
            f"Extracted ACM Register section: {len(content)} -> {len(extracted)} chars (saved {len(content) - len(extracted)} chars)"
        )
        return extracted, True

    return content, False


def _preprocess_acm_content(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Pre-process ACM document content to help LLM understand the structure.

    The content from PyMuPDF/content-core often comes in vertical format where
    table columns are stacked vertically. This function:
    1. Extracts the ACM Register section (removes boilerplate)
    2. Identifies room/building headers
    3. Groups related content together
    4. Adds structural markers to help LLM parsing

    Returns:
        Tuple of (processed_content, metadata_dict)
    """
    metadata = {
        "original_length": len(content),
        "rooms_found": 0,
        "acm_indicators_found": 0,
        "no_asbestos_found": 0,
        "section_extracted": False,
    }

    # First, try to extract just the ACM Register section
    content, was_extracted = _extract_acm_register_section(content)
    metadata["section_extracted"] = was_extracted
    metadata["extracted_length"] = len(content)

    # Count key patterns for metadata
    metadata["acm_indicators_found"] = content.count("Asbestos-containing")
    metadata["no_asbestos_found"] = content.count("No Asbestos")

    # Room header pattern: B009 - R0005 - General Storeroom - 6.61 m2
    room_pattern = r"(B\d{3}\s*-\s*R\d{4,5}\s*-\s*[^-\n]+\s*-\s*[\d.]+\s*m2)"
    rooms = re.findall(room_pattern, content)
    metadata["rooms_found"] = len(rooms)

    # Building header pattern: B009 - Special Purpose - 1950 - Steel
    building_pattern = r"(B\d{3}\s*-\s*[A-Za-z][^-\n]+\s*-\s*\d{4}\s*-\s*[A-Za-z]+)"
    buildings = re.findall(building_pattern, content)

    if debug_config.DEBUG_ENABLED:
        acm_debug(f"Pre-process found: {len(rooms)} rooms, {len(buildings)} buildings")
        acm_debug(
            f"ACM indicators: {metadata['acm_indicators_found']}, No Asbestos: {metadata['no_asbestos_found']}"
        )

    # Add section markers to help LLM understand structure
    processed = content

    # Mark building headers clearly
    for building in buildings:
        marker = f"\n\n=== BUILDING: {building} ===\n"
        processed = processed.replace(building, marker + building)

    # Mark room headers clearly
    for room in rooms:
        marker = f"\n--- ROOM: {room} ---\n"
        processed = processed.replace(room, marker + room)

    # Mark ACM result patterns (replace newline-split version first, then check for already-marked)
    acm_marker = ">>> ACM DETECTED: Asbestos-containing material <<<"

    # Replace newline-split version (most common in PDF extraction)
    processed = processed.replace("Asbestos-containing\nmaterial", acm_marker)

    # Replace single-line version only if not already marked
    # This prevents double-marking
    processed = processed.replace("Asbestos-containing material", acm_marker)

    # Clean up any accidental double markers
    while ">>> ACM DETECTED: >>> ACM DETECTED:" in processed:
        processed = processed.replace(
            ">>> ACM DETECTED: >>> ACM DETECTED: Asbestos-containing material <<< <<<",
            acm_marker,
        )

    metadata["processed_length"] = len(processed)

    return processed, metadata


class ExtractionState(TypedDict):
    """State for the ACM extraction graph."""

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


def _get_pipeline_logger(state: dict) -> Optional[PipelineLogger]:
    """Safely get PipelineLogger from state (may be None for backward compat)."""
    return state.get("pipeline_logger")


def _generate_dedup_key(record: ACMExtractionRecord, school_code: Optional[str]) -> str:
    """Generate a deduplication key for a record.

    Key format: {school_code}_{building_id}_{room_id}_{hash(product_description[:50])}
    Uses SHA-256 for cryptographic security (truncated to 8 chars for readability).
    """
    school = school_code or "unknown"
    building = record.building_id or "unknown"
    room = record.room_id or "none"

    # Create hash of product description (first 50 chars) using SHA-256
    desc_hash = hashlib.sha256(
        (record.material_description or "")[:50].encode()
    ).hexdigest()[:8]

    return f"{school}_{building}_{room}_{desc_hash}"


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

    # Merge data_issues
    all_issues = list(set(existing.data_issues + new.data_issues))
    base.data_issues = all_issues

    return base


def _extract_page_range_text(content: str, page_start: int, page_end: int) -> str:
    """Extract text between page_start and page_end markers from source content.

    Uses the same page marker patterns as _chunk_content to find page boundaries,
    then returns the text spanning the requested page range.
    """
    if not content:
        return ""

    page_pattern = r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$))"
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
    page_pattern = r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$))"

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

    if pl:
        pl.stage_enter(StageId.STRUCTURE, "Extracting document metadata...")

    if not content:
        logger.warning(f"Source {source.id} has no content for metadata extraction")
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
        return {"document_metadata": metadata}
    except Exception as e:
        logger.warning(f"Metadata extraction failed for source {source.id}: {e}")
        return {"document_metadata": None}


async def extract_structure(state: dict, config: RunnableConfig) -> dict:
    """Extract document structure as Stage -1 pre-extraction intelligence.

    Story: E1-S16 Document Structure & TOC Extraction
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    pl = _get_pipeline_logger(state)

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Extracting document structure...")

    if not content:
        logger.warning(f"Source {source.id} has no content for structure extraction")
        return {"document_structure": None}

    try:
        structure = await extract_document_structure(content, model_id=model_id)
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
        return {"document_structure": structure}
    except Exception as e:
        logger.warning(f"Structure extraction failed for source {source.id}: {e}")
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

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Compiling building inventory...")

    if not content:
        logger.warning(f"Source {source.id} has no content for building inventory")
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
        return {"building_inventory": inventory}
    except Exception as e:
        logger.warning(
            f"Building inventory compilation failed for source {source.id}: {e}"
        )
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

    if pl:
        pl.stage_progress(StageId.STRUCTURE, "Tagging page sections...")

    if not content:
        logger.warning(f"Source {source.id} has no content for page tagging")
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
        return {"page_tags": None}


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
                n_plans = len(getattr(orch_stats, "building_plans", []))
                summary = f"{n_plans} building plans"
            pl.stage_complete(StageId.ORCHESTRATOR, summary)
        return result
    except Exception as e:
        if pl:
            pl.stage_fail(StageId.ORCHESTRATOR, str(e))
        raise


async def prepare_context(state: dict, config: RunnableConfig) -> dict:
    """Prepare extraction context and chunk content if needed."""
    source: Source = state["source"]
    content = source.full_text or ""
    pl = _get_pipeline_logger(state)

    # Skip ORCHESTRATOR stage when taking the non-orchestrator path (E1-S21)
    if pl:
        pl.stage_skip(StageId.ORCHESTRATOR, "Below threshold for orchestration")

    if pl:
        pl.stage_enter(StageId.PREFLIGHT, "Preparing content and chunking...")

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
            rf"(?:[-—]+|<!--)\s*Page\s+{doc_structure.register_start_page}\s*(?:[-—]+|-->)",
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

    # Pre-process content to add structural markers
    processed_content, preprocess_meta = _preprocess_acm_content(content)

    if debug_config.DEBUG_ENABLED:
        acm_debug(f"Pre-processing complete: {preprocess_meta}")
        dump_content_to_file(processed_content, source_id, "processed_content")

    # Initialize context from source metadata
    context = BuildingRoomContext()
    if source.title:
        context.school_name = source.title

    # Chunk processed content if needed
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

    return {
        "content": processed_content,
        "chunks": chunks,
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
    retry_count = state.get("retry_count", 0)
    pl = _get_pipeline_logger(state)

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

    # Render the extraction prompt
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
        }
    )

    # Debug: Log and dump the prompt
    source: Source = state["source"]
    source_id = str(source.id) if source.id else "unknown"
    log_prompt_preview(system_prompt, source_id)
    dump_prompt_to_file(system_prompt, source_id, current_index)

    acm_debug(f"Chunk {current_index + 1}/{len(chunks)}: {len(chunk_content)} chars")

    # Get the model
    try:
        model = await provision_langchain_model(
            chunk_content,
            model_id,
            "extraction",  # Uses default_extraction_model or falls back to chat
            temperature=0.1 if retry_count > 0 else 0.3,  # Lower temp on retry
            max_tokens=32768,  # Enough tokens for large ACM tables (64+ records)
        )
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
    except Exception as e:
        logger.error(f"Failed to provision model: {e}")
        return {"error": f"Model provisioning failed: {e}"}

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Extract ACM records from the content provided in the system prompt."
        ),
    ]

    # Use structured output
    try:
        chain = model.with_structured_output(ACMExtractionResult)
        result: ACMExtractionResult = await chain.ainvoke(messages)

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

        return {
            "records": existing_records + new_records,
            "context": context,
            "current_chunk_index": current_index + 1,
            "extraction_result": result,
            "retry_count": 0,  # Reset retry count on success
        }

    except ValidationError as e:
        logger.warning(f"Structured output validation failed: {e}")
        if retry_count < MAX_RETRIES:
            # Apply exponential backoff delay before retry
            delay = (
                RETRY_DELAYS[retry_count]
                if retry_count < len(RETRY_DELAYS)
                else RETRY_DELAYS[-1]
            )
            logger.info(
                f"Retrying in {delay}s (attempt {retry_count + 1}/{MAX_RETRIES})"
            )
            await asyncio.sleep(delay)
            return {
                "retry_count": retry_count + 1,
                "error": None,  # Clear error to allow retry
            }
        return {
            "error": f"Extraction validation failed after {MAX_RETRIES} retries: {e}"
        }

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if retry_count < MAX_RETRIES:
            # Apply exponential backoff delay before retry
            delay = (
                RETRY_DELAYS[retry_count]
                if retry_count < len(RETRY_DELAYS)
                else RETRY_DELAYS[-1]
            )
            logger.info(
                f"Retrying in {delay}s (attempt {retry_count + 1}/{MAX_RETRIES})"
            )
            await asyncio.sleep(delay)
            return {
                "retry_count": retry_count + 1,
                "error": None,
            }
        return {"error": f"Extraction failed after {MAX_RETRIES} retries: {e}"}


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
            if "assumed positive" in result_lower or "presumed positive" in result_lower:
                record.result = "Assumed Positive"
            elif "assumed negative" in result_lower or "presumed negative" in result_lower:
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

    # Log EXTRACT stage complete on first validation pass (marks end of extraction)
    correction_attempt = state.get("correction_attempt", 0)
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

    if pl:
        pl.stage_enter(
            StageId.CORRECT,
            f"Correction attempt {correction_attempt + 1}...",
        )
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

        # Layer 1: Try deterministic normalization first
        still_invalid = []
        for issue in validation.issues:
            if issue.issue_type != "enum_mismatch":
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
    """Use LLM to correct records that failed Layer 1 normalization."""
    import json

    from open_notebook.extractors.validators.acm_validator import validate_acm_record

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

        # Render correction prompt
        prompter = Prompter(prompt_template="acm/correction")
        correction_prompt = prompter.render(
            data={
                "record_json": json.dumps(record_dict, indent=2, default=str),
                "validation_issues": [i.model_dump() for i in validation.issues],
            }
        )

        try:
            model = await provision_langchain_model(
                correction_prompt,
                model_id,
                "extraction",
                temperature=0.1,
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

        except Exception as e:
            logger.warning(f"LLM correction failed for record {idx}: {e}")
            correction_stats["failed"] = correction_stats.get("failed", 0) + 1


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
            # Filter to only correctable issues (enum + business rule)
            correctable = [
                i
                for i in validation.issues
                if i.issue_type in ("enum_mismatch", "business_rule")
            ]
            if correctable:
                return "correct"

    return "deduplicate"


async def deduplicate_records(state: dict, config: RunnableConfig) -> dict:
    """Deduplicate records using composite key."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    pl = _get_pipeline_logger(state)

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

    return {"records": deduplicated}


async def save_records(state: dict, config: RunnableConfig) -> dict:
    """Save validated records to the database."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    source: Source = state["source"]
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    start_time = state.get("start_time", time.time())
    records_rejected = state.get("records_rejected", 0)
    pl = _get_pipeline_logger(state)

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
    from open_notebook.domain.acm import ACMTableSection

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
                room_id=record.room_id,
                room_name=record.room_name,
                room_area=record.room_area,
                area_type=record.area_type or "Interior",
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
    "orchestrate", orchestrate_with_logging
)  # E1-S20: Agentic orchestrator (wrapped with E1-S21 logging)
agent_state.add_node("prepare", prepare_context)
agent_state.add_node("extract", extract_records)
agent_state.add_node("validate", validate_records_strict)
agent_state.add_node("correct", correct_records)
agent_state.add_node("deduplicate", deduplicate_records)
agent_state.add_node("save", save_records)

# Add edges: START → extract_metadata → structure → inventory → tag_pages → prepare → ...
agent_state.add_edge(START, "extract_metadata")
agent_state.add_edge("extract_metadata", "structure")
agent_state.add_edge("structure", "inventory")
agent_state.add_edge("inventory", "tag_pages")
# E1-S20: Conditional routing after page tagging
agent_state.add_conditional_edges(
    "tag_pages",
    lambda s: "orchestrate" if should_use_orchestrator(s) else "prepare",
    {"orchestrate": "orchestrate", "prepare": "prepare"},
)
agent_state.add_edge("orchestrate", "validate")  # Orchestrator feeds into validation
agent_state.add_conditional_edges(
    "prepare",
    lambda s: "error" if s.get("error") else "extract",
    {"extract": "extract", "error": END},
)
agent_state.add_conditional_edges(
    "extract",
    should_continue_extraction,
    {"extract": "extract", "validate": "validate", "error": END},
)
# Corrective RAG loop: validate → should_correct → {correct, deduplicate}
agent_state.add_conditional_edges(
    "validate", should_correct, {"correct": "correct", "deduplicate": "deduplicate"}
)
# After correction, re-validate
agent_state.add_edge("correct", "validate")
agent_state.add_edge("deduplicate", "save")
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

    # Initialize pipeline logger (E1-S21)
    total_pages = 0
    if source.full_text:
        # Count page markers to estimate total pages
        page_markers = re.findall(
            r"(?:[-—]+\s*Page\s+\d+|<!--\s*Page\s+\d+\s*-->)",
            source.full_text,
            re.IGNORECASE,
        )
        total_pages = len(page_markers) if page_markers else 0
    pl = PipelineLogger(
        source_id=str(source.id),
        total_pages=total_pages,
        command_id=command_id,
    )

    if force:
        # Delete existing table sections and records (E11-S1)
        from open_notebook.domain.acm import ACMTableSection

        try:
            sections_deleted = await ACMTableSection.delete_by_source(str(source.id))
            if sections_deleted > 0:
                logger.info(
                    f"Deleted {sections_deleted} existing table sections for source {source.id}"
                )
        except Exception as e:
            logger.warning(f"Failed to delete table sections: {e}")

        deleted = await ACMRecord.delete_by_source(str(source.id))
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
    }

    try:
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
            pipeline_run = pl.fail(error)
            return ACMExtractionOutput(
                source_id=str(source.id),
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

        # Pipeline complete — emit summary
        pipeline_run = pl.complete(
            total_records=extraction_result.total_records,
            records_rejected=extraction_result.records_rejected,
            confidence_distribution=conf_dict,
            total_chunks=total_chunks,
            total_buildings=total_buildings,
            strategy_distribution=strategy_dist,
        )

        return ACMExtractionOutput(
            source_id=str(source.id),
            status=status,
            total_records=extraction_result.total_records,
            records_failed=extraction_result.records_rejected,
            confidence_distribution=extraction_result.confidence_distribution,
            extraction_time_ms=extraction_time,
            correction_stats=correction_stats if has_corrections else None,
            orchestrator_stats=orch_stats_dict,
            pipeline_run=pipeline_run.model_dump(mode="json"),
        )

    except Exception as e:
        logger.exception(f"ACM extraction failed for source {source.id}")
        extraction_time = int((time.time() - start_time) * 1000)
        pipeline_run = pl.fail(str(e))
        return ACMExtractionOutput(
            source_id=str(source.id),
            status="failed",
            total_records=0,
            records_failed=0,
            error=str(e),
            extraction_time_ms=extraction_time,
            pipeline_run=pipeline_run.model_dump(mode="json"),
        )
