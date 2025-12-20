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


def _preprocess_acm_content(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Pre-process ACM document content to help LLM understand the structure.

    The content from PyMuPDF/content-core often comes in vertical format where
    table columns are stacked vertically. This function:
    1. Identifies room/building headers
    2. Groups related content together
    3. Adds structural markers to help LLM parsing

    Returns:
        Tuple of (processed_content, metadata_dict)
    """
    metadata = {
        "original_length": len(content),
        "rooms_found": 0,
        "acm_indicators_found": 0,
        "no_asbestos_found": 0,
    }

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
        acm_debug(f"ACM indicators: {metadata['acm_indicators_found']}, No Asbestos: {metadata['no_asbestos_found']}")

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

    # Mark ACM result patterns
    processed = processed.replace(
        "Asbestos-containing\nmaterial",
        ">>> ACM DETECTED: Asbestos-containing material <<<"
    )
    processed = processed.replace(
        "Asbestos-containing material",
        ">>> ACM DETECTED: Asbestos-containing material <<<"
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


def _merge_records(existing: ACMExtractionRecord, new: ACMExtractionRecord) -> ACMExtractionRecord:
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


def _chunk_content(content: str, context_window: int = DEFAULT_CONTEXT_WINDOW) -> List[Dict[str, Any]]:
    """Split content into chunks if it exceeds threshold.

    Chunks are split by page markers or logical sections to preserve context.
    """
    tokens = token_count(content)
    threshold = int(context_window * CHUNK_THRESHOLD_RATIO)

    if tokens <= threshold:
        # No chunking needed
        return [{"content": content, "page_number": 1, "chunk_index": 0}]

    chunks = []

    # Try to split by page markers first
    page_pattern = r"(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+"
    page_matches = list(re.finditer(page_pattern, content, re.IGNORECASE))

    if page_matches:
        # Split by pages
        for i, match in enumerate(page_matches):
            start = match.start()
            end = page_matches[i + 1].start() if i + 1 < len(page_matches) else len(content)

            page_content = content[start:end]
            page_num = int(match.group(1))

            # Check if this chunk is still too large
            if token_count(page_content) > threshold:
                # Split this page further by sections (headings)
                sub_chunks = _split_by_sections(page_content, threshold, page_num)
                for j, sub in enumerate(sub_chunks):
                    chunks.append({
                        "content": sub,
                        "page_number": page_num,
                        "chunk_index": len(chunks)
                    })
            else:
                chunks.append({
                    "content": page_content,
                    "page_number": page_num,
                    "chunk_index": len(chunks)
                })
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

            chunks.append({
                "content": content[start:end],
                "page_number": page_num,
                "chunk_index": len(chunks)
            })

            start = end - overlap if end < len(content) else end
            page_num += 1

    logger.info(f"Content chunked into {len(chunks)} parts")
    return chunks


def _split_by_sections(content: str, max_tokens: int, base_page: int) -> List[str]:
    """Split content by section headers if it's too large."""
    # Split by markdown headers
    sections = re.split(r'(^#{1,3}\s+.+$)', content, flags=re.MULTILINE)

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


async def prepare_context(state: dict, config: RunnableConfig) -> dict:
    """Prepare extraction context and chunk content if needed."""
    source: Source = state["source"]
    content = source.full_text or ""

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
    acm_debug(f"Content stats: {preprocess_meta['acm_indicators_found']} ACM indicators, "
              f"{preprocess_meta['no_asbestos_found']} No Asbestos entries")

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
        )
    except Exception as e:
        logger.error(f"Failed to provision model: {e}")
        return {"error": f"Model provisioning failed: {e}"}

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Extract ACM records from the content provided in the system prompt."),
    ]

    # Use structured output
    try:
        chain = model.with_structured_output(ACMExtractionResult)
        result: ACMExtractionResult = await chain.ainvoke(messages)

        # Debug: Log raw result before processing
        logger.debug(f"Raw extraction result: status={result.status}, records_count={len(result.records)}")
        if result.records:
            logger.debug(f"First record: {result.records[0].model_dump_json()[:500]}")
        else:
            logger.warning(f"No records extracted. Extraction notes: {result.extraction_notes}")

        # Update stats
        result.update_stats()

        # Extract new records and update context
        new_records = result.records

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
            delay = RETRY_DELAYS[retry_count] if retry_count < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
            logger.info(f"Retrying in {delay}s (attempt {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(delay)
            return {
                "retry_count": retry_count + 1,
                "error": None,  # Clear error to allow retry
            }
        return {"error": f"Extraction validation failed after {MAX_RETRIES} retries: {e}"}

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if retry_count < MAX_RETRIES:
            # Apply exponential backoff delay before retry
            delay = RETRY_DELAYS[retry_count] if retry_count < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
            logger.info(f"Retrying in {delay}s (attempt {retry_count + 1}/{MAX_RETRIES})")
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

        # Normalize result field
        if record.result:
            result_lower = record.result.lower()
            if "no asbestos" in result_lower or "nad" in result_lower or "not detected" in result_lower:
                record.result = "Not Detected"
            elif "detected" in result_lower or "positive" in result_lower:
                record.result = "Detected"
            elif "presumed" in result_lower:
                record.result = "Presumed"
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
        if not record.building_id or not record.product or not record.material_description:
            rejected_count += 1
            logger.warning(f"Rejected record due to missing required fields: {issues}")
            continue

        validated_records.append(record)

    if rejected_count > 0:
        logger.info(f"Validated {len(validated_records)} records, rejected {rejected_count}")

    return {"records": validated_records, "records_rejected": rejected_count}


async def deduplicate_records(state: dict, config: RunnableConfig) -> dict:
    """Deduplicate records using composite key."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())

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

    return {"records": deduplicated}


async def save_records(state: dict, config: RunnableConfig) -> dict:
    """Save validated records to the database."""
    records: List[ACMExtractionRecord] = state.get("records", [])
    source: Source = state["source"]
    context: BuildingRoomContext = state.get("context", BuildingRoomContext())
    start_time = state.get("start_time", time.time())
    records_rejected = state.get("records_rejected", 0)

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

    saved_count = 0
    errors = []

    for record in records:
        try:
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

            await acm_record.save()
            saved_count += 1

        except Exception as e:
            logger.error(f"Failed to save record: {e}")
            errors.append(str(e))

    extraction_time = int((time.time() - start_time) * 1000)

    # Build final result
    result = ACMExtractionResult(
        records=records,
        status=ExtractionStatus.VALID if saved_count > 0 else ExtractionStatus.NO_ACM_DATA,
        total_records=saved_count,
        records_rejected=records_rejected,
    )
    result.update_stats()

    logger.info(
        f"Saved {saved_count}/{len(records)} ACM records for source {source.id} "
        f"in {extraction_time}ms"
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
agent_state.add_node("prepare", prepare_context)
agent_state.add_node("extract", extract_records)
agent_state.add_node("validate", validate_records)
agent_state.add_node("deduplicate", deduplicate_records)
agent_state.add_node("save", save_records)

# Add edges
agent_state.add_edge(START, "prepare")
agent_state.add_conditional_edges(
    "prepare",
    lambda s: "error" if s.get("error") else "extract",
    {"extract": "extract", "error": END}
)
agent_state.add_conditional_edges(
    "extract",
    should_continue_extraction,
    {"extract": "extract", "validate": "validate", "error": END}
)
agent_state.add_conditional_edges(
    "validate",
    should_save,
    {"save": "deduplicate", "error": END}
)
agent_state.add_edge("deduplicate", "save")
agent_state.add_edge("save", END)

# Compile the graph
graph = agent_state.compile()


async def extract_acm_from_source(
    source: Source,
    model_id: Optional[str] = None,
    force: bool = False,
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

    if force:
        # Delete existing records
        deleted = await ACMRecord.delete_by_source(str(source.id))
        if deleted > 0:
            logger.info(f"Deleted {deleted} existing ACM records for source {source.id}")

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
    }

    try:
        result = await graph.ainvoke(initial_state)

        extraction_result: ACMExtractionResult = result.get(
            "extraction_result", ACMExtractionResult()
        )
        error = result.get("error")

        extraction_time = int((time.time() - start_time) * 1000)

        if error:
            return ACMExtractionOutput(
                source_id=str(source.id),
                status="failed",
                total_records=0,
                records_failed=extraction_result.records_rejected,
                error=error,
                extraction_time_ms=extraction_time,
            )

        status = "success" if extraction_result.total_records > 0 else "no_data"

        return ACMExtractionOutput(
            source_id=str(source.id),
            status=status,
            total_records=extraction_result.total_records,
            records_failed=extraction_result.records_rejected,
            confidence_distribution=extraction_result.confidence_distribution,
            extraction_time_ms=extraction_time,
        )

    except Exception as e:
        logger.exception(f"ACM extraction failed for source {source.id}")
        extraction_time = int((time.time() - start_time) * 1000)
        return ACMExtractionOutput(
            source_id=str(source.id),
            status="failed",
            total_records=0,
            records_failed=0,
            error=str(e),
            extraction_time_ms=extraction_time,
        )
