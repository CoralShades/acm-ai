"""
ACM Extraction LangGraph Workflow

AI-powered extraction of Asbestos Containing Material (ACM) records from
PDF documents processed by content-core (PyMuPDF).

Story: E1-S7 AI-Powered ACM Extraction
"""

import asyncio
import hashlib
import os
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
from open_notebook.extractors.metadata_and_structure import (
    extract_metadata_and_structure,
    synthesize_page_tags,
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
    _apply_ollama_extraction_settings,
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
    # AG-UI event emitter (E17-S1)
    agui_emitter: Optional[AGUIEventEmitter]
    # E34-S1: operation_id for PipelineEventBus streaming events
    operation_id: Optional[str]
    # E32-S1: Building__c extraction results (record IDs of persisted BuildingRecords)
    building_records: List[str]
    # E32-S2: True when extract_items_node produced >= 1 record
    items_extracted: bool
    # Phase 1 building meta cache: building_code -> BuildingExtractionResult
    # Populated by extract_building_node, consumed by extract_items_node to
    # avoid duplicate Phase 1 LLM calls.
    building_meta_cache: Dict[str, Any]


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


async def metadata_and_structure_node(state: dict, config: RunnableConfig) -> dict:
    """Combined metadata + structure extraction (S4: merged pre-extraction).

    Replaces separate extract_metadata and structure nodes with a single LLM call.
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if pl:
        pl.stage_enter(StageId.STRUCTURE, "Extracting metadata and structure...")
    if agui:
        await agui.emit_step_started("metadata_and_structure")

    if not content:
        logger.warning(
            f"Source {source.id} has no content for metadata+structure extraction"
        )
        if agui:
            await agui.emit_step_finished("metadata_and_structure")
        return {"document_metadata": None, "document_structure": None}

    try:
        metadata, structure = await extract_metadata_and_structure(
            content, model_id=model_id
        )

        # PyMuPDF page-count fallback (from existing extract_structure node)
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
                        f"[S4] PyMuPDF page-count fallback: {structure.total_pages} pages "
                        f"for source {source.id}"
                    )
                except Exception as fitz_err:
                    logger.debug(f"PyMuPDF fallback failed: {fitz_err}")

        if metadata:
            fields_count = len(metadata.get_extracted_fields())
            consultant = metadata.consultant_name or "unknown"
            logger.info(
                f"[S4] Combined extraction for source {source.id}: "
                f"consultant={consultant}, type={structure.document_type}, "
                f"register_start={structure.register_start_page}, "
                f"buildings={len(structure.building_ids)}"
            )
            if pl:
                pl.stage_progress(
                    StageId.STRUCTURE,
                    f"Metadata+Structure: consultant={consultant}, type={structure.document_type}",
                    consultant=consultant,
                    document_type=structure.document_type,
                    register_start=structure.register_start_page,
                    buildings=len(structure.building_ids),
                )
            if agui:
                await agui.emit_state_delta(
                    [
                        {
                            "op": "replace",
                            "path": "/metadata",
                            "value": {"consultant": consultant, "fields": fields_count},
                        },
                        {
                            "op": "replace",
                            "path": "/toc",
                            "value": {
                                "type": structure.document_type,
                                "buildings": len(structure.building_ids),
                            },
                        },
                    ]
                )

        if agui:
            await agui.emit_step_finished("metadata_and_structure")
        return {"document_metadata": metadata, "document_structure": structure}
    except Exception as e:
        logger.warning(
            f"Combined metadata+structure extraction failed for source {source.id}: {e}"
        )
        if agui:
            await agui.emit_step_finished("metadata_and_structure")
        return {"document_metadata": None, "document_structure": None}


async def compile_inventory(state: dict, config: RunnableConfig) -> dict:
    """Compile building inventory as Stage -1.5 pre-extraction intelligence.

    Story: E1-S17 Building Inventory Compilation
    """
    source: Source = state["source"]
    content = source.full_text or ""
    model_id = state.get("model_id")
    doc_structure: Optional[DocumentStructure] = state.get("document_structure")
    doc_meta = state.get("document_metadata")
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    # Build metadata context for prompt injection
    meta_context: Optional[dict] = None
    if doc_meta:
        meta_context = {
            "site_name": getattr(doc_meta, "site_name", None) or "",
            "consultant_name": getattr(doc_meta, "consultant_name", None) or "",
            "document_type": (
                doc_structure.document_type.value
                if doc_structure and doc_structure.document_type
                else ""
            ),
        }

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
            document_metadata=meta_context,
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

        # S4: Synthesize page_tags from inventory + structure (replaces tag_pages LLM call)
        page_tags = None
        if inventory and doc_structure:
            page_tags = synthesize_page_tags(inventory, doc_structure)
            logger.info(
                f"[S4] Synthesized page tags: {len(page_tags.pages)} pages, "
                f"register_range={page_tags.register_page_range}"
            )
            if pl:
                pl.stage_complete(
                    StageId.STRUCTURE,
                    f"Inventory + page tags synthesized: {inventory.total_buildings} buildings",
                    pages_tagged=len(page_tags.pages),
                    register_range=str(page_tags.register_page_range),
                )

        return {"building_inventory": inventory, "page_tags": page_tags}
    except Exception as e:
        logger.warning(
            f"Building inventory compilation failed for source {source.id}: {e}"
        )
        if agui:
            await agui.emit_step_finished("inventory")
        return {"building_inventory": None, "page_tags": None}


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


_MAX_CONCURRENT_BUILDINGS = int(os.getenv("ACM_MAX_CONCURRENT_BUILDINGS", "3"))


async def extract_building_node(state: dict, config: RunnableConfig) -> dict:
    """Phase 1 Building__c extraction: concurrent AI calls per building section.

    Iterates over state["building_inventory"].buildings and calls
    _v3_extract_building_meta() for each building concurrently (bounded by
    ACM_MAX_CONCURRENT_BUILDINGS env var, default 3), mapping results to
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
        return {"building_records": [], "building_meta_cache": {}}

    if pl:
        pl.stage_progress(
            StageId.ORCHESTRATOR,
            f"Building extraction: {inventory.total_buildings} buildings",
        )

    saved_ids: List[str] = []
    meta_cache: Dict[str, Any] = {}  # building_code -> BuildingExtractionResult
    source_id_str = str(source.id)
    sem = asyncio.Semaphore(_MAX_CONCURRENT_BUILDINGS)

    async def _extract_one_building(building_meta_entry):
        """Extract a single building's metadata (semaphore-bounded)."""
        async with sem:
            _bldg_start = time.time()
            page_start = building_meta_entry.page_start
            page_end = building_meta_entry.page_end or page_start
            building_content = _extract_building_content(content, page_start, page_end)

            if not building_content.strip():
                logger.warning(
                    f"[E32-S1] Empty content for building {building_meta_entry.building_id} "
                    f"(pages {page_start}-{page_end}) — skipping"
                )
                return None

            plan = BuildingExtractionPlan(
                building_id=building_meta_entry.building_id,
                building_name=building_meta_entry.name,
                page_range=(page_start, page_end),
                strategy=ExtractionStrategy.FULL_LLM,
            )

            # Phase 1 LLM call
            result = await _v3_extract_building_meta(
                building_content=building_content,
                plan=plan,
                state=state,
                schema_bundle=schema_bundle,
            )

            if result is None:
                logger.warning(
                    f"[E32-S1] Phase 1 returned None for building "
                    f"{building_meta_entry.building_id} — creating minimal record"
                )
                # Bug Fix 11 Phase 3: Create minimal BuildingRecord so FK linkage
                # and frontend display work even when LLM extraction fails.
                internal_id = await BuildingRecord.generate_internal_id(source_id_str)
                minimal_record = BuildingRecord(
                    internal_id=internal_id,
                    source_id=source_id_str,
                    building_code=building_meta_entry.building_id,
                    building_name=building_meta_entry.name,
                )
                await minimal_record.save()
                if not minimal_record.id:
                    logger.warning(
                        f"[E32-S1] Minimal BuildingRecord.save() failed for building "
                        f"{building_meta_entry.building_id} — skipping"
                    )
                    return None
                minimal_record_id = str(minimal_record.id)
                logger.info(
                    f"[E32-S1] Saved minimal BuildingRecord {internal_id} for building "
                    f"{building_meta_entry.building_id} (LLM Phase 1 failed)"
                )
                return {
                    "record_id": minimal_record_id,
                    "building_id": building_meta_entry.building_id,
                    "result": None,
                }

            # Generate server-side internal ID (sequential — safe under asyncio)
            internal_id = await BuildingRecord.generate_internal_id(source_id_str)

            record = BuildingRecord(
                internal_id=internal_id,
                source_id=source_id_str,
                building_code=building_meta_entry.building_id,
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
                state=result.state,
                number_of_levels=result.number_of_levels,
                owned_or_leased=result.owned_or_leased,
                building_sub_category=result.building_sub_category,
                building_risk_rating=result.building_risk_rating,
            )

            await record.save()
            if not record.id:
                logger.warning(
                    f"[E32-S1] BuildingRecord.save() returned no ID for building "
                    f"{building_meta_entry.building_id} — record may not have persisted"
                )
                return None
            record_id = str(record.id)

            logger.info(
                f"[E32-S1] Saved BuildingRecord {internal_id} for building "
                f"{building_meta_entry.building_id} (confidence={result.extraction_confidence})"
            )

            # E34-S1: Publish ai.building_extracted event
            if operation_id:
                try:
                    _bldg_duration_ms = int((time.time() - _bldg_start) * 1000)
                    await get_event_bus().publish(
                        AIBuildingExtractedEvent(
                            operation_id=operation_id,
                            data=AIBuildingExtractedData(
                                building_id=internal_id,
                                building_name=result.building_name
                                or building_meta_entry.building_id,
                                records_extracted=1,
                                model_used=model_id or "unknown",
                                duration_ms=_bldg_duration_ms,
                            ),
                        )
                    )
                except Exception as _pub_err:
                    logger.debug(
                        f"[E34-S1] Failed to publish ai.building_extracted for "
                        f"{building_meta_entry.building_id}: {_pub_err}"
                    )

            return {
                "record_id": record_id,
                "building_id": building_meta_entry.building_id,
                "result": result,
            }

    # Run all building extractions concurrently (bounded by semaphore)
    outcomes = await asyncio.gather(
        *[_extract_one_building(b) for b in inventory.buildings],
        return_exceptions=True,
    )

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.warning(
                f"[E32-S1] Building extraction task failed: {outcome} "
                "(skipping — partial results preserved)"
            )
            continue
        if outcome is None:
            continue
        saved_ids.append(outcome["record_id"])
        meta_cache[outcome["building_id"]] = outcome["result"]

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

    return {"building_records": saved_ids, "building_meta_cache": meta_cache}


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
    docling_tables: Optional[List[Dict[str, Any]]] = None,
) -> ACMItemExtractionResult:
    """Split oversized building content and merge item results.

    If building_content exceeds _ITEM_EXTRACTION_CHUNK_CHARS, splits into
    equal-sized char chunks, calls _v3_extract_items() for each, and merges
    records into a single ACMItemExtractionResult.

    Story: E32-S2 Item__c AI Extraction Node
    """
    if len(building_content) <= _ITEM_EXTRACTION_CHUNK_CHARS:
        result = await _v3_extract_items(
            building_content,
            plan,
            building_meta,
            state,
            schema_bundle,
            docling_tables=docling_tables,
        )
        if result.status == "truncated":
            logger.warning(
                f"[E32-S2] Truncation detected for building {plan.building_id} "
                "— retrying with cloud provider (model_id=None)"
            )
            cloud_state = {**state, "model_id": None}
            result = await _v3_extract_items(
                building_content,
                plan,
                building_meta,
                cloud_state,
                schema_bundle,
                docling_tables=docling_tables,
            )
        return result

    # Split into N equal-sized char chunks
    chunks = [
        building_content[i : i + _ITEM_EXTRACTION_CHUNK_CHARS]
        for i in range(0, len(building_content), _ITEM_EXTRACTION_CHUNK_CHARS)
    ]
    merged_records = []
    final_status = "valid"
    for chunk in chunks:
        result = await _v3_extract_items(
            chunk,
            plan,
            building_meta,
            state,
            schema_bundle,
            docling_tables=docling_tables,
        )
        if result.status == "truncated":
            logger.warning(
                f"[E32-S2] Truncation detected in chunk for building {plan.building_id} "
                "— retrying chunk with cloud provider (model_id=None)"
            )
            cloud_state = {**state, "model_id": None}
            result = await _v3_extract_items(
                chunk,
                plan,
                building_meta,
                cloud_state,
                schema_bundle,
                docling_tables=docling_tables,
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
    meta_cache_state: Dict[str, Any] = state.get("building_meta_cache") or {}
    sem = asyncio.Semaphore(_MAX_CONCURRENT_BUILDINGS)

    # Per-row vs bulk extraction mode (Phase 3 integration)
    extraction_mode = os.getenv("ACM_ITEM_EXTRACTION_MODE", "per_row")

    async def _extract_items_for_building(building_meta_entry):
        """Extract items for a single building (semaphore-bounded)."""
        async with sem:
            page_start = building_meta_entry.page_start
            page_end = building_meta_entry.page_end or page_start

            building_content = _extract_building_content(content, page_start, page_end)

            # S6: Fetch Docling tables for this building's page range
            docling_tables = await _get_docling_tables(
                source_id_str, page_start, page_end
            )

            if not building_content.strip():
                logger.warning(
                    f"[E32-S2] Empty content for building {building_meta_entry.building_id} "
                    f"(pages {page_start}-{page_end}) — skipping"
                )
                return None

            plan = BuildingExtractionPlan(
                building_id=building_meta_entry.building_id,
                building_name=building_meta_entry.name,
                page_range=(page_start, page_end),
                strategy=ExtractionStrategy.FULL_LLM,
            )

            # Look up cached Phase 1 result from extract_building_node
            building_meta_result = meta_cache_state.get(building_meta_entry.building_id)

            # ---------------------------------------------------------------
            # Per-row extraction path (Phase 3)
            # ---------------------------------------------------------------
            if extraction_mode == "per_row":
                from open_notebook.extractors.row_extractor import extract_all_rows
                from open_notebook.extractors.row_segmenter import (
                    scan_text_for_synthetics,
                    segment_multiple_tables,
                )

                # Get DoclingDocument JSON from stored tables + inject page_number
                docling_json_tables = []
                for t in (docling_tables or []):
                    dj = t.get("docling_document_json")
                    if dj:
                        # Inject page_number from outer acm_table_section row
                        dj["page_number"] = t.get("page_start", 0)
                        docling_json_tables.append(dj)

                if docling_json_tables:
                    # Segment tables into individual rows
                    rows = segment_multiple_tables(
                        docling_json_tables,
                        building_id=building_meta_entry.building_id,
                        source_id=source_id_str,
                        building_page_range=(page_start, page_end),
                    )

                    # Scan markdown for synthetic rows (Type D/F)
                    synthetic_rows = scan_text_for_synthetics(
                        building_content,
                        building_meta_entry.building_id,
                        source_id_str,
                    )
                    rows.extend(synthetic_rows)

                    if rows:
                        # Provision model for per-row extraction (small context)
                        row_model = await provision_langchain_model(
                            "",
                            state.get("model_id"),
                            "extraction",
                            temperature=0,
                            num_ctx=int(
                                os.getenv("ACM_ROW_EXTRACTION_NUM_CTX", "2048")
                            ),
                        )

                        # Get Langfuse handler for tracing (if available)
                        langfuse_handler = get_langfuse_handler()

                        # Build human-readable building context string
                        building_context = (
                            building_meta_entry.name
                            or building_meta_entry.building_id
                        )

                        # Extract all rows -> list[ACMExtractionRecord]
                        records = await extract_all_rows(
                            rows=rows,
                            building_context=building_context,
                            model=row_model,
                            source_id=source_id_str,
                            building_id=building_meta_entry.building_id,
                            langfuse_handler=langfuse_handler,
                        )

                        # Populate building_record_id FK
                        building_record_id = code_to_id_map.get(
                            building_meta_entry.building_id
                        )
                        if building_record_id:
                            for rec in records:
                                rec.building_record_id = building_record_id

                        logger.info(
                            f"[per-row] Building {building_meta_entry.building_id}: "
                            f"{len(records)} items from {len(rows)} rows"
                        )

                        # Publish ai.items_extracted event (same as bulk path)
                        if operation_id:
                            try:
                                _internal_id = code_to_internal_id_map.get(
                                    building_meta_entry.building_id,
                                    building_meta_entry.building_id,
                                )
                                await get_event_bus().publish(
                                    AIItemsExtractedEvent(
                                        operation_id=operation_id,
                                        data=AIItemsExtractedData(
                                            building_id=_internal_id,
                                            items_count=len(records),
                                            items_rejected=0,
                                        ),
                                    )
                                )
                            except Exception as _pub_err:
                                logger.debug(
                                    f"[E34-S1] Failed to publish ai.items_extracted for "
                                    f"{building_meta_entry.building_id}: {_pub_err}"
                                )

                        return records
                    else:
                        logger.warning(
                            f"No rows segmented for {building_meta_entry.building_id} "
                            "— falling back to bulk"
                        )
                else:
                    logger.warning(
                        f"No DoclingDocument JSON for {building_meta_entry.building_id} "
                        "— falling back to bulk"
                    )

            # ---------------------------------------------------------------
            # Bulk extraction path (existing, unchanged)
            # ---------------------------------------------------------------

            # Phase 2: extract items (with chunking if content is large)
            item_result = await _chunk_and_extract_items(
                building_content,
                plan,
                building_meta_result,
                state,
                schema_bundle,
                docling_tables=docling_tables,
            )

            # Normalise V3 SF fields -> ACMExtractionRecord
            records = _normalize_v3_records(building_meta_result, item_result, plan)

            # Populate building_record_id FK from lookup map
            building_record_id = code_to_id_map.get(building_meta_entry.building_id)
            if building_record_id:
                for rec in records:
                    rec.building_record_id = building_record_id

            logger.info(
                f"[E32-S2] Building {building_meta_entry.building_id}: {len(records)} items"
            )

            # E34-S1: Publish ai.items_extracted event
            if operation_id:
                try:
                    _internal_id = code_to_internal_id_map.get(
                        building_meta_entry.building_id, building_meta_entry.building_id
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
                        f"{building_meta_entry.building_id}: {_pub_err}"
                    )

            return records

    # Run all item extractions concurrently (bounded by semaphore)
    outcomes = await asyncio.gather(
        *[_extract_items_for_building(b) for b in inventory.buildings],
        return_exceptions=True,
    )

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.warning(
                f"[E32-S2] Item extraction task failed: {outcome} "
                "(skipping — partial results preserved)"
            )
            continue
        if outcome is None:
            continue
        all_records.extend(outcome)

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


async def normalize_to_sf_node(state: dict, config: RunnableConfig) -> dict:
    """Normalize SF picklist fields before validation.

    Runs deterministic SF normalization (case, synonyms, business rules)
    to eliminate unnecessary LLM correction calls.
    """
    records = state.get("records", [])
    if not records:
        return {"records": []}
    try:
        from open_notebook.extractors.normalizers.sf_normalizer import (
            normalize_extraction_records,
        )

        stats = normalize_extraction_records(records)
        logger.info(
            f"[NORMALIZE] {stats['records_modified']}/{stats['total_records']} "
            f"records, {stats['fields_modified']} fields"
        )
    except Exception as e:
        logger.warning(f"SF normalization failed (non-fatal): {e}")
    return {"records": records}


async def validate_records_strict(state: dict, config: RunnableConfig) -> dict:
    """Validate extracted records against SF/BAR enum values and business rules.

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
            _records_corrected = correction_stats.get(
                "auto_corrected", 0
            ) + correction_stats.get("llm_corrected", 0)
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
            # Bug Fix 11 Phase 4: Apply format="json" for Ollama correction models
            model = _apply_ollama_extraction_settings(model)
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
    # In per-row mode the segmenter already handles synthetic rows (Type D/F)
    # so post-LLM recovery is unnecessary.
    if os.getenv("ACM_ITEM_EXTRACTION_MODE", "per_row") == "per_row":
        logger.info(
            "Skipping no-access recovery in per-row mode (handled by segmenter)"
        )
        return state

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


# Build the graph
agent_state = StateGraph(ExtractionState)

# Add nodes
agent_state.add_node(
    "metadata_and_structure", metadata_and_structure_node
)  # S4: combined
agent_state.add_node(
    "inventory", compile_inventory
)  # E1-S17: Stage -1.5 (also synthesizes page_tags)
agent_state.add_node(
    "save_intelligence", save_intelligence_node
)  # E30-S9: Persist pre-extraction intelligence
agent_state.add_node(
    "extract_building", extract_building_node
)  # E32-S1: Building__c Phase 1 extraction
agent_state.add_node(
    "extract_items", extract_items_node
)  # E32-S2: Item__c Phase 2 extraction
agent_state.add_node("normalize_to_sf", normalize_to_sf_node)
agent_state.add_node("validate", validate_records_strict)
agent_state.add_node("correct", correct_records)
agent_state.add_node("deduplicate", deduplicate_records)
agent_state.add_node("recover_no_access", recover_no_access_node)
agent_state.add_node("save", save_records)

# S4: Merged pre-extraction flow (4→2 LLM calls)
# START → metadata_and_structure (1 LLM) → inventory (1 LLM, synthesizes page_tags) → save_intelligence
agent_state.add_edge(START, "metadata_and_structure")
agent_state.add_edge("metadata_and_structure", "inventory")
agent_state.add_edge("inventory", "save_intelligence")
# E32-S1: Building__c extraction runs between save_intelligence and extract_items
agent_state.add_edge("save_intelligence", "extract_building")
# E32-S2: Item__c extraction runs after building extraction
agent_state.add_edge("extract_building", "extract_items")
agent_state.add_edge("extract_items", "normalize_to_sf")
agent_state.add_edge("normalize_to_sf", "validate")
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
