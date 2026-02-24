"""
Agentic Extraction Orchestrator.

Dynamically routes document sections to appropriate extraction tools
and strategies based on page tags, document structure, and building
inventory. Replaces the monolithic extract loop with per-building
extraction using parallel processing.

Story: E1-S20 Agentic Extraction Orchestrator
"""

import asyncio
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.runnables import RunnableConfig
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from open_notebook.domain.notebook import Source
from open_notebook.extractors.acm_schemas import (
    ACMExtractionRecord,
    ACMExtractionResult,
    BuildingRoomContext,
)
from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingInventory,
    BuildingMeta,
)
from open_notebook.extractors.document_structure import (
    _PAGE_PATTERN,
    _page_num_from_match,
)
from open_notebook.extractors.page_tagger import (
    PageTaggingResult,
    SectionTaxonomy,
)
from open_notebook.extractors.parsers.base import DocumentMeta
from open_notebook.graphs.utils import (
    _is_qwen_model,
    is_auth_error,
    is_provider_schema_error,
    parse_json_response,
    provision_extraction_fallback_model,
)

# ---------------------------------------------------------------------------
# Free-form JSON normalization helpers
# ---------------------------------------------------------------------------


def _normalize_extraction_json(parsed: dict) -> dict:
    """Normalize LLM-generated JSON to match ACMExtractionResult schema.

    When using direct ainvoke() (no structured output grammar), the LLM
    may return fields with the wrong type.  Common mismatches:
      - ``data_issues`` as a plain string instead of ``List[str]``.

    This function mutates *parsed* in-place and returns it.
    """
    for record in parsed.get("records", []):
        if not isinstance(record, dict):
            continue
        di = record.get("data_issues")
        if isinstance(di, str):
            record["data_issues"] = [di] if di.strip() else []
    return parsed


# ---------------------------------------------------------------------------
# Task 1: Pydantic Models (AC #3, #5, #7)
# ---------------------------------------------------------------------------


class ExtractionStrategy(str, Enum):
    """Strategy for extracting a building's ACM records (Task 1.1)."""

    FULL_LLM = "full_llm"
    REGEX_ONLY = "regex_only"
    SKIP = "skip"


class BuildingExtractionPlan(BaseModel):
    """Extraction plan for a single building (Task 1.2)."""

    building_id: str
    building_name: Optional[str] = None
    page_range: Tuple[int, int]
    strategy: ExtractionStrategy
    complexity: str = "complex"
    context_summary: Optional[str] = None
    acm_item_count_estimate: Optional[int] = None


class ExtractionPlan(BaseModel):
    """Aggregate extraction plan for all buildings (Task 1.3)."""

    plans: List[BuildingExtractionPlan]
    total_buildings: int
    buildings_to_extract: int
    buildings_skipped: int
    estimated_llm_calls: int


class BuildingExtractionStats(BaseModel):
    """Extraction statistics for a single building (Task 1.4)."""

    building_id: str
    records_extracted: int = 0
    pages_processed: int = 0
    strategy_used: str = "full_llm"
    time_ms: int = 0
    errors: Optional[List[str]] = None


class OrchestratorStats(BaseModel):
    """Aggregate orchestration statistics (Task 1.5)."""

    total_buildings: int = 0
    buildings_extracted: int = 0
    buildings_skipped: int = 0
    total_records: int = 0
    strategy_distribution: Dict[str, int] = Field(default_factory=dict)
    total_time_ms: int = 0
    plan: Optional[ExtractionPlan] = None


# ---------------------------------------------------------------------------
# Task 2: Extraction Planning Logic (AC #1, #2, #3)
# ---------------------------------------------------------------------------


_SAMP_BUILDING_ID = re.compile(r"^[A-Z]\d+[A-Z]?$|^D\d{2,3}$")


def _select_strategy(
    building: BuildingMeta,
    page_tags: Optional[PageTaggingResult],
) -> ExtractionStrategy:
    """Select extraction strategy for a building based on complexity and page tags."""
    # ARA-style buildings (name-based IDs) always need LLM extraction
    # because regex_only only handles SAMP B###-R#### room patterns
    if not _SAMP_BUILDING_ID.match(building.building_id):
        return ExtractionStrategy.FULL_LLM

    if not page_tags:
        return ExtractionStrategy.FULL_LLM

    # Check if ANY of this building's pages are register pages (section_id=4)
    building_pages = [
        tag
        for tag in page_tags.pages
        if building.page_start
        <= tag.page_number
        <= (building.page_end or building.page_start)
    ]
    register_pages = [
        p for p in building_pages if p.section_id == SectionTaxonomy.ASBESTOS_REGISTER
    ]

    if not register_pages:
        return (
            ExtractionStrategy.FULL_LLM
        )  # Use LLM when page tagging can't confirm register location

    if building.complexity == BuildingComplexity.SIMPLE:
        return ExtractionStrategy.REGEX_ONLY

    return ExtractionStrategy.FULL_LLM


def _build_context_summary(
    building: BuildingMeta,
    document_meta: Optional[DocumentMeta] = None,
) -> str:
    """Create a context summary string for a building extraction."""
    parts = [f"Building {building.building_id}"]
    if building.name:
        parts.append(f"'{building.name}'")
    if building.year:
        parts.append(f"built {building.year}")
    if building.construction:
        parts.append(f"({building.construction})")
    if document_meta and document_meta.consultant_name:
        parts.append(f"| consultant: {document_meta.consultant_name}")
    if document_meta and document_meta.site_name:
        parts.append(f"| site: {document_meta.site_name}")
    return " ".join(parts)


def plan_extraction(
    building_inventory: BuildingInventory,
    page_tags: Optional[PageTaggingResult] = None,
    document_meta: Optional[DocumentMeta] = None,
) -> ExtractionPlan:
    """Generate an extraction plan from building inventory and page tags (Task 2.2)."""
    plans: List[BuildingExtractionPlan] = []

    for building in building_inventory.buildings:
        strategy = _select_strategy(building, page_tags)
        page_end = building.page_end or building.page_start

        plans.append(
            BuildingExtractionPlan(
                building_id=building.building_id,
                building_name=building.name,
                page_range=(building.page_start, page_end),
                strategy=strategy,
                complexity=building.complexity.value
                if isinstance(building.complexity, BuildingComplexity)
                else str(building.complexity),
                context_summary=_build_context_summary(building, document_meta),
                acm_item_count_estimate=building.acm_item_count_estimate,
            )
        )

    buildings_to_extract = sum(
        1 for p in plans if p.strategy != ExtractionStrategy.SKIP
    )
    buildings_skipped = sum(1 for p in plans if p.strategy == ExtractionStrategy.SKIP)
    estimated_llm_calls = sum(
        1 for p in plans if p.strategy == ExtractionStrategy.FULL_LLM
    )

    return ExtractionPlan(
        plans=plans,
        total_buildings=len(plans),
        buildings_to_extract=buildings_to_extract,
        buildings_skipped=buildings_skipped,
        estimated_llm_calls=estimated_llm_calls,
    )


def should_use_orchestrator(state: dict) -> bool:
    """Decide whether to use the orchestrator path or legacy path (Task 2.3)."""
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    if not inventory:
        return False
    if not inventory.buildings or inventory.total_buildings == 0:
        return False
    return True


# ---------------------------------------------------------------------------
# Task 3: Per-Building Extraction (AC #2, #4, #5)
# ---------------------------------------------------------------------------


ROOM_ENTRY_PATTERN = re.compile(
    r"([A-Z]\d+[A-Z]?-R\d+)\s*(?:[-\u2013]|\t)\s*(.+?)(?:\n|$)"
)
NO_ACM_PATTERN = re.compile(
    r"(?:No\s+Asbestos|Not\s+Detected|NAD|No\s+ACM)", re.IGNORECASE
)


def _extract_building_content(content: str, page_start: int, page_end: int) -> str:
    """Extract content between page markers for a building's page range (Task 3.2)."""
    matches = list(_PAGE_PATTERN.finditer(content))
    if not matches:
        return content

    start_pos = None
    end_pos = len(content)

    for match in matches:
        page_num = _page_num_from_match(match)
        if page_num == page_start and start_pos is None:
            start_pos = match.start()
        if page_num > page_end:
            end_pos = match.start()
            break

    if start_pos is None:
        # Page marker not found; try to find the closest preceding marker
        for match in matches:
            page_num = _page_num_from_match(match)
            if page_num <= page_start:
                start_pos = match.start()
            else:
                break
        if start_pos is None:
            return content

    return content[start_pos:end_pos]


def _create_building_prompt_context(
    plan: BuildingExtractionPlan,
    doc_meta: Optional[DocumentMeta] = None,
) -> dict:
    """Merge building metadata and document metadata into a prompt context dict (Task 3.3)."""
    ctx: Dict[str, Any] = {
        "building_id": plan.building_id,
        "building_name": plan.building_name,
        "page_start": plan.page_range[0],
        "page_end": plan.page_range[1],
        "complexity": plan.complexity,
    }
    if doc_meta:
        ctx["consultant_name"] = doc_meta.consultant_name
        ctx["site_name"] = doc_meta.site_name
        ctx["report_date"] = doc_meta.report_date
    return ctx


def _regex_extract_simple_building(
    content: str,
    building_id: str,
    building_name: Optional[str] = None,
    page_start: Optional[int] = None,
) -> List[ACMExtractionRecord]:
    """Extract records from a simple building using regex (Task 3.4).

    For simple buildings (typically "No Asbestos Found"), create one
    ACMExtractionRecord per room entry with result='Not Detected'.
    """
    records: List[ACMExtractionRecord] = []

    for match in ROOM_ENTRY_PATTERN.finditer(content):
        room_id = match.group(1)
        room_name = match.group(2).strip()

        records.append(
            ACMExtractionRecord(
                building_id=building_id,
                building_name=building_name,
                room_id=room_id,
                room_name=room_name,
                product="N/A",
                material_description="No asbestos containing materials found",
                result="Negative",
                extraction_confidence="high",
                page_number=page_start,
            )
        )

    return records


ROOM_HEADER_PATTERN = re.compile(r"B\d{3}\s*-\s*R\d{4,5}")
# ARA-format item pattern: numbered items like "1." or "1\n" at start of line
ARA_ITEM_PATTERN = re.compile(r"(?:^|\n)(\d+)\.\s", re.MULTILINE)
SUB_CHUNK_ROOM_THRESHOLD = 12  # ~250 tokens/record; 32768 tokens fits many more safely


def _split_building_by_rooms(
    content: str, max_rooms: int = SUB_CHUNK_ROOM_THRESHOLD
) -> List[str]:
    """Split building content into sub-chunks by room/item groups.

    Finds room header boundaries (SAMP format) or numbered item boundaries
    (ARA format) and groups them into sub-chunks of max_rooms each to avoid
    output token truncation.
    """
    room_matches = list(ROOM_HEADER_PATTERN.finditer(content))

    # Fallback to ARA-format numbered items when SAMP pattern finds nothing
    if not room_matches:
        room_matches = list(ARA_ITEM_PATTERN.finditer(content))

    if len(room_matches) <= max_rooms:
        return [content]

    chunks: List[str] = []
    for i in range(0, len(room_matches), max_rooms):
        start = room_matches[i].start()
        # End at the start of the next group (or end of content)
        end_idx = i + max_rooms
        end = (
            room_matches[end_idx].start()
            if end_idx < len(room_matches)
            else len(content)
        )
        chunks.append(content[start:end])

    logger.info(
        f"Split building content into {len(chunks)} sub-chunks "
        f"({len(room_matches)} items, threshold={max_rooms})"
    )
    return chunks


async def _llm_extract_building(
    building_content: str,
    plan: BuildingExtractionPlan,
    state: dict,
) -> List[ACMExtractionRecord]:
    """Run LLM extraction on building content using existing extraction logic.

    For buildings with many rooms, splits content into sub-chunks to avoid
    output token truncation (32768 max_tokens).
    """
    from ai_prompter import Prompter

    from open_notebook.graphs.utils import provision_langchain_model

    model_id = state.get("model_id")
    doc_meta: Optional[DocumentMeta] = state.get("document_metadata")

    # Check room count and sub-chunk if needed
    sub_chunks = _split_building_by_rooms(building_content)

    all_records: List[ACMExtractionRecord] = []

    for chunk_idx, chunk_content in enumerate(sub_chunks):
        prompt_ctx = _create_building_prompt_context(plan, doc_meta)

        # Provision model BEFORE prompt rendering so we can detect model family
        model = await provision_langchain_model(
            chunk_content,
            model_id,
            "extraction",
            temperature=0.1,
            max_tokens=32768,
        )

        is_qwen = _is_qwen_model(model)
        model_family = "qwen" if is_qwen else "default"

        prompter = Prompter(prompt_template="acm/building_extraction")
        system_prompt = prompter.render(
            data={
                "building_context": prompt_ctx,
                "content": chunk_content,
                "model_family": model_family,
            }
        )

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Extract ACM records from the building content provided."
            ),
        ]

        async def _invoke(
            active_model, active_is_qwen: bool
        ) -> ACMExtractionResult:
            if active_is_qwen:
                response_text = ""
                try:
                    raw_response = await active_model.ainvoke(messages)
                    response_text = (
                        raw_response.content
                        if hasattr(raw_response, "content")
                        else str(raw_response)
                    )
                    parsed = parse_json_response(response_text)
                    _normalize_extraction_json(parsed)
                    result_local: ACMExtractionResult = ACMExtractionResult.model_validate(
                        parsed
                    )
                    logger.info(
                        f"Building {plan.building_id} Qwen direct JSON: "
                        f"{len(result_local.records)} records"
                    )
                    return result_local
                except (ValueError, ValidationError) as qwen_err:
                    logger.error(
                        f"Building {plan.building_id} Qwen JSON parsing failed: {qwen_err}. "
                        f"Response preview: {response_text[:200] if response_text else 'N/A'}"
                    )
                    raise

            chain = active_model.with_structured_output(ACMExtractionResult)
            return await chain.ainvoke(messages)

        try:
            result = await _invoke(model, is_qwen)
        except Exception as invoke_err:
            if is_auth_error(invoke_err):
                failed_model_name = (
                    getattr(model, "model_name", None)
                    or getattr(model, "model", None)
                    or str(model_id or "unknown")
                )
                fallback_model = await provision_extraction_fallback_model(
                    str(failed_model_name),
                    temperature=0.1,
                    max_tokens=32768,
                )
                if fallback_model is None:
                    raise

                model = fallback_model
                is_qwen = _is_qwen_model(model)
                logger.warning(
                    "Building extraction auth failure for model "
                    f"'{failed_model_name}', switched to fallback model "
                    f"'{getattr(model, 'model_name', getattr(model, 'model', 'unknown'))}'"
                )
                result = await _invoke(model, is_qwen)
            elif is_provider_schema_error(invoke_err):
                # Provider (e.g. Amazon Bedrock, Google Vertex AI) rejected
                # the structured output request. Fall back to direct invocation
                # with manual JSON parsing, mirroring the Qwen pattern.
                logger.warning(
                    f"Building {plan.building_id}: Provider schema/compat error "
                    f"detected ({invoke_err}). Falling back to direct "
                    "invocation with manual JSON parsing."
                )
                pl = state.get("pipeline_logger")
                if pl:
                    pl._log(
                        f"  Provider error detected — falling back to direct "
                        f"JSON parsing for {plan.building_id}",
                        level="warning"
                    )
                try:
                    raw_response = await model.ainvoke(messages)
                    response_text = (
                        raw_response.content
                        if hasattr(raw_response, "content")
                        else str(raw_response)
                    )
                    parsed = parse_json_response(response_text)
                    _normalize_extraction_json(parsed)
                    result = ACMExtractionResult.model_validate(parsed)
                    logger.info(
                        f"Building {plan.building_id} schema-error fallback "
                        f"succeeded: {len(result.records)} records"
                    )
                    if pl:
                        pl._log(
                            f"  Fallback succeeded: {len(result.records)} records "
                            f"from {plan.building_id}"
                        )
                except (ValueError, ValidationError) as fallback_err:
                    logger.error(
                        f"Building {plan.building_id} schema-error fallback "
                        f"JSON parsing failed: {fallback_err}"
                    )
                    if pl:
                        pl._log(
                            f"  Fallback JSON parsing FAILED: {fallback_err}",
                            level="error"
                        )
                    raise
            else:
                raise

        if len(sub_chunks) > 1:
            logger.info(
                f"Building {plan.building_id} sub-chunk {chunk_idx + 1}/{len(sub_chunks)}: "
                f"{len(result.records)} records"
            )

        all_records.extend(result.records)

    return all_records


async def extract_building(
    plan: BuildingExtractionPlan,
    content: str,
    state: dict,
) -> Tuple[List[ACMExtractionRecord], BuildingExtractionStats]:
    """Extract ACM records for a single building (Task 3.1)."""
    start = time.time()
    building_content = _extract_building_content(
        content, plan.page_range[0], plan.page_range[1]
    )
    pages_processed = plan.page_range[1] - plan.page_range[0] + 1

    if plan.strategy == ExtractionStrategy.SKIP:
        elapsed = int((time.time() - start) * 1000)
        return [], BuildingExtractionStats(
            building_id=plan.building_id,
            records_extracted=0,
            pages_processed=0,
            strategy_used=ExtractionStrategy.SKIP.value,
            time_ms=elapsed,
        )

    if plan.strategy == ExtractionStrategy.REGEX_ONLY:
        try:
            records = _regex_extract_simple_building(
                building_content,
                plan.building_id,
                plan.building_name,
                page_start=plan.page_range[0],
            )

            # E20-S2: Yield check — escalate to FULL_LLM if regex yield is too low
            estimate = plan.acm_item_count_estimate or 0
            should_escalate = False
            if estimate > 0 and len(records) < estimate * 0.5:
                should_escalate = True
                logger.warning(
                    f"Building {plan.building_id}: REGEX_ONLY yield "
                    f"{len(records)}/{estimate} < 50% — escalating to FULL_LLM"
                )
            elif estimate == 0 and len(records) == 0 and building_content.strip():
                should_escalate = True
                logger.warning(
                    f"Building {plan.building_id}: REGEX_ONLY yield 0 records "
                    f"(no estimate) with non-empty content — escalating to FULL_LLM"
                )

            if should_escalate:
                try:
                    records = await _llm_extract_building(building_content, plan, state)
                    for rec in records:
                        if not rec.building_name and plan.building_name:
                            rec.building_name = plan.building_name
                        if not rec.page_number:
                            rec.page_number = plan.page_range[0]
                    elapsed = int((time.time() - start) * 1000)
                    return records, BuildingExtractionStats(
                        building_id=plan.building_id,
                        records_extracted=len(records),
                        pages_processed=pages_processed,
                        strategy_used="regex_escalated_to_llm",
                        time_ms=elapsed,
                    )
                except Exception as llm_err:
                    logger.error(
                        f"Building {plan.building_id} LLM escalation failed: {llm_err}"
                    )
                    # Fall through to return the (empty) regex records

            elapsed = int((time.time() - start) * 1000)
            return records, BuildingExtractionStats(
                building_id=plan.building_id,
                records_extracted=len(records),
                pages_processed=pages_processed,
                strategy_used=ExtractionStrategy.REGEX_ONLY.value,
                time_ms=elapsed,
            )
        except Exception as e:
            logger.error(f"Building {plan.building_id} regex extraction failed: {e}")
            elapsed = int((time.time() - start) * 1000)
            return [], BuildingExtractionStats(
                building_id=plan.building_id,
                records_extracted=0,
                pages_processed=pages_processed,
                strategy_used=ExtractionStrategy.REGEX_ONLY.value,
                time_ms=elapsed,
                errors=[str(e)],
            )

    # FULL_LLM path
    try:
        pl = state.get("pipeline_logger")
        if pl:
            pl._log(
                f"  FULL_LLM: Building {plan.building_id} ({plan.building_name}) | "
                f"content_len={len(building_content)} | pages={pages_processed}"
            )
        records = await _llm_extract_building(building_content, plan, state)
        if pl:
            pl._log(
                f"  FULL_LLM result: {len(records)} records from {plan.building_id}"
            )
        # Ensure building context propagates to all records
        for rec in records:
            if not rec.building_name and plan.building_name:
                rec.building_name = plan.building_name
            if not rec.page_number:
                rec.page_number = plan.page_range[0]
        elapsed = int((time.time() - start) * 1000)
        return records, BuildingExtractionStats(
            building_id=plan.building_id,
            records_extracted=len(records),
            pages_processed=pages_processed,
            strategy_used=ExtractionStrategy.FULL_LLM.value,
            time_ms=elapsed,
        )
    except Exception as e:
        logger.error(f"Building {plan.building_id} extraction failed: {e}")
        pl = state.get("pipeline_logger")
        if pl:
            pl._log(
                f"  FULL_LLM ERROR: Building {plan.building_id} failed: {e}",
                level="error"
            )
        elapsed = int((time.time() - start) * 1000)
        return [], BuildingExtractionStats(
            building_id=plan.building_id,
            records_extracted=0,
            pages_processed=pages_processed,
            strategy_used=ExtractionStrategy.FULL_LLM.value,
            time_ms=elapsed,
            errors=[str(e)],
        )


# ---------------------------------------------------------------------------
# Task 4: Parallel Orchestration (AC #4, #8)
# ---------------------------------------------------------------------------


def merge_building_results(
    results: List[Tuple[List[ACMExtractionRecord], BuildingExtractionStats]],
    extraction_plan: ExtractionPlan,
    total_start_time: float,
) -> Tuple[List[ACMExtractionRecord], OrchestratorStats]:
    """Combine records and stats from all building extractions (Task 4.2)."""
    all_records: List[ACMExtractionRecord] = []
    strategy_dist: Dict[str, int] = {}
    buildings_extracted = 0

    for records, stats in results:
        all_records.extend(records)
        strategy_dist[stats.strategy_used] = (
            strategy_dist.get(stats.strategy_used, 0) + 1
        )
        if stats.strategy_used != ExtractionStrategy.SKIP.value and not stats.errors:
            buildings_extracted += 1

    total_time = int((time.time() - total_start_time) * 1000)

    orchestrator_stats = OrchestratorStats(
        total_buildings=extraction_plan.total_buildings,
        buildings_extracted=buildings_extracted,
        buildings_skipped=extraction_plan.buildings_skipped,
        total_records=len(all_records),
        strategy_distribution=strategy_dist,
        total_time_ms=total_time,
        plan=extraction_plan,
    )

    return all_records, orchestrator_stats


async def _extract_buildings_parallel(
    plans: List[BuildingExtractionPlan],
    content: str,
    state: dict,
    max_concurrent: int = 3,
) -> List[Tuple[List[ACMExtractionRecord], BuildingExtractionStats]]:
    """Extract multiple buildings in parallel with concurrency limit (Task 4.3)."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _extract_with_limit(plan: BuildingExtractionPlan):
        async with semaphore:
            return await extract_building(plan, content, state)

    non_skip = [p for p in plans if p.strategy != ExtractionStrategy.SKIP]

    if not non_skip:
        return []

    tasks = [_extract_with_limit(plan) for plan in non_skip]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[Tuple[List[ACMExtractionRecord], BuildingExtractionStats]] = []
    for i, result in enumerate(raw_results):
        if isinstance(result, BaseException):
            plan = non_skip[i]
            logger.error(f"Building {plan.building_id} extraction failed: {result}")
            results.append(
                (
                    [],
                    BuildingExtractionStats(
                        building_id=plan.building_id,
                        records_extracted=0,
                        pages_processed=0,
                        strategy_used=plan.strategy.value,
                        time_ms=0,
                        errors=[str(result)],
                    ),
                )
            )
        else:
            results.append(result)

    return results


async def orchestrate_extraction(state: dict, config: RunnableConfig) -> dict:
    """Agentic orchestration node for the LangGraph pipeline (Task 4.1).

    Routes to per-building extraction using the orchestrator plan.
    This replaces the legacy prepare -> extract -> loop path when
    building inventory is available.
    """
    source: Source = state["source"]
    content = source.full_text or ""
    inventory: BuildingInventory = state["building_inventory"]
    page_tags: Optional[PageTaggingResult] = state.get("page_tags")
    doc_meta: Optional[DocumentMeta] = state.get("document_metadata")

    # Build context (mirrors prepare_context enrichment)
    context = BuildingRoomContext()
    if source.title:
        context.school_name = source.title

    total_start = time.time()

    # Generate extraction plan
    extraction_plan = plan_extraction(inventory, page_tags, doc_meta)

    logger.info(
        f"Orchestrator plan for source {source.id}: "
        f"{extraction_plan.total_buildings} buildings, "
        f"{extraction_plan.buildings_to_extract} to extract, "
        f"{extraction_plan.buildings_skipped} skipped, "
        f"{extraction_plan.estimated_llm_calls} LLM calls"
    )

    # Execute per-building extractions in parallel
    results = await _extract_buildings_parallel(
        extraction_plan.plans,
        content,
        state,
    )

    # Add SKIP stats for skipped buildings
    for plan in extraction_plan.plans:
        if plan.strategy == ExtractionStrategy.SKIP:
            results.append(
                (
                    [],
                    BuildingExtractionStats(
                        building_id=plan.building_id,
                        records_extracted=0,
                        pages_processed=0,
                        strategy_used=ExtractionStrategy.SKIP.value,
                        time_ms=0,
                    ),
                )
            )

    # Merge results
    all_records, orchestrator_stats = merge_building_results(
        results,
        extraction_plan,
        total_start,
    )

    # Log per-building errors for debugging zero-record extractions
    # Also surface to pipeline log (acm-extraction.log) since loguru may not persist
    pl = state.get("pipeline_logger")
    for records, stats in results:
        if stats.errors:
            logger.error(
                f"Building {stats.building_id} extraction errors: {stats.errors}"
            )
            if pl:
                pl._log(
                    f"  ERROR: Building {stats.building_id} errors: {stats.errors}",
                    level="error"
                )
        elif stats.records_extracted == 0 and stats.strategy_used != ExtractionStrategy.SKIP.value:
            logger.warning(
                f"Building {stats.building_id} returned 0 records "
                f"(strategy={stats.strategy_used}, pages={stats.pages_processed}, "
                f"time={stats.time_ms}ms) — check content or LLM response"
            )
            if pl:
                pl._log(
                    f"  WARNING: Building {stats.building_id} returned 0 records "
                    f"(strategy={stats.strategy_used}, pages={stats.pages_processed}, "
                    f"time={stats.time_ms}ms)",
                    level="warning"
                )

    logger.info(
        f"Orchestrator complete for source {source.id}: "
        f"{orchestrator_stats.total_records} records from "
        f"{orchestrator_stats.buildings_extracted} buildings "
        f"in {orchestrator_stats.total_time_ms}ms"
    )

    return {
        "records": all_records,
        "orchestrator_stats": orchestrator_stats,
        "context": context,
        "content": content,
        "start_time": state.get("start_time", time.time()),
    }
