"""
Agentic Extraction Orchestrator.

Dynamically routes document sections to appropriate extraction tools
and strategies based on page tags, document structure, and building
inventory. Replaces the monolithic extract loop with per-building
extraction using parallel processing.

Story: E1-S20 Agentic Extraction Orchestrator
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.document_structure import (
    _PAGE_PATTERN,
    _page_num_from_match,
)
from open_notebook.extractors.parsers.base import DocumentMeta
from open_notebook.graphs.utils import (
    TruncationError,
    _get_v3_building_schema,
    _get_v3_item_schema,
    _inject_response_format,
    parse_json_response,
)

# ---------------------------------------------------------------------------
# E26-S3: Docling table injection helpers (ADR-001 D5)
# ---------------------------------------------------------------------------


async def _get_docling_tables(
    source_id: str,
    page_start: int,
    page_end: int,
) -> List[Dict[str, Any]]:
    """Load Docling Direct API tables from acm_table_section for a page range.

    Returns tables where table_type='docling_direct_api' and page falls
    within the building's page range.  Returns empty list if none found
    (graceful fallback to existing behavior).

    Retries once on connection timeout (common on Windows WebSocket).
    """
    import asyncio

    from open_notebook.database.repository import ensure_record_id, repo_query

    query = (
        "SELECT * FROM acm_table_section "
        "WHERE source_id = $source_id "
        "AND table_type = 'docling_direct_api' "
        "AND page_start <= $page_end "
        "AND page_end >= $page_start "
        "ORDER BY page_start ASC"
    )
    params = {
        "source_id": ensure_record_id(source_id),
        "page_start": page_start,
        "page_end": page_end,
    }

    # Retry once on timeout (WebSocket handshake can fail on Windows)
    for attempt in range(2):
        try:
            results = await repo_query(query, params)
            matched = results if results else []

            # Log warning if page range is excluding tables
            total_query = (
                "SELECT count() as cnt FROM acm_table_section "
                "WHERE source_id = $source_id "
                "AND table_type = 'docling_direct_api' "
                "GROUP ALL"
            )
            total_result = await repo_query(
                total_query,
                {"source_id": ensure_record_id(source_id)},
            )
            total_count = total_result[0].get("cnt", 0) if total_result else 0
            if total_count > len(matched):
                logger.warning(
                    f"Page range filter [{page_start}-{page_end}] excluded "
                    f"{total_count - len(matched)} of {total_count} total tables "
                    f"for source {source_id}"
                )
            return matched
        except Exception as e:
            if attempt == 0 and "timed out" in str(e).lower():
                logger.warning(
                    f"Docling table query timed out for {source_id}, retrying..."
                )
                await asyncio.sleep(1)
                continue
            logger.warning(f"Docling table query failed for {source_id}: {e}")
            return []
    return []


def _inject_docling_tables(
    building_content: str,
    docling_tables: List[Dict[str, Any]],
) -> str:
    """Inject Docling DataFrame markdown into building content for LLM context.

    Appends structured table data AFTER the existing building content,
    with clear section headers and an instruction for the LLM to prioritize
    the structured data for record extraction.
    """
    if not docling_tables:
        return building_content

    context_parts = [building_content]
    context_parts.append(
        "\n\n## Structured Table Data (from PDF table extraction)\n"
        "The following tables were extracted directly from the PDF with "
        "preserved row structure. Each row is a complete ACM register entry.\n"
    )

    for table in docling_tables:
        page = table.get("page_start", "?")
        raw_text = table.get("raw_text", "")
        if raw_text:
            context_parts.append(f"### Table (Page {page})\n{raw_text}\n")

    context_parts.append(
        "\n**IMPORTANT**: The structured table data above preserves exact row "
        "structure from the PDF. Each row represents one ACM record. Rows with "
        "'Same as', 'As Per', 'Not Sampled', or 'No Access' entries are separate "
        "records that must EACH be extracted as individual ACM records.\n"
    )

    return "\n".join(context_parts)


# ---------------------------------------------------------------------------
# Free-form JSON normalization helpers
# ---------------------------------------------------------------------------


# N4 fix: ordered list of known sample_result enum values (longest first so
# "Assumed Positive" is matched before "Positive").
_SAMPLE_RESULT_ENUMS = [
    "Assumed Positive",
    "Not Sampled",
    "No Access",
    "Positive",
    "Negative",
]


def _split_compound_sample_result(value: str) -> str:
    """Return the first valid sample_result enum found in a compound string.

    LLMs sometimes concatenate adjacent table columns, producing values like
    "Positive Assumed Positive" or "Negative No Access".  We scan for the
    first recognised enum token and return it, discarding the rest.

    N4 fix.
    """
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    # Fast path: already a valid single value
    if stripped in _SAMPLE_RESULT_ENUMS:
        return stripped
    # Scan for the first known enum token
    for enum_val in _SAMPLE_RESULT_ENUMS:
        if enum_val in stripped:
            return enum_val
    return stripped  # unchanged — validator will handle it


def _normalize_extraction_json(parsed: dict) -> dict:
    """Normalize LLM-generated JSON to match extraction schema.

    Handles common LLM type mismatches:
      - ``data_issues`` as null or plain string → ``List[str]``
      - ``labelled`` as bool (true/false) → ``"Yes"``/``"No"`` string
      - ``sample_result`` compound values (N4) → first valid enum token

    This function mutates *parsed* in-place and returns it.
    """
    for record in parsed.get("records", []):
        if not isinstance(record, dict):
            continue
        di = record.get("data_issues")
        if isinstance(di, str):
            record["data_issues"] = [di] if di.strip() else []
        elif di is None:
            # LLM often returns "data_issues": null — coerce to empty list so
            # ACMExtractionRecord(List[str]) validation does not fail.
            record["data_issues"] = []
        # Coerce labelled bool→str (Ollama returns true/false instead of Yes/No)
        labelled = record.get("labelled")
        if isinstance(labelled, bool):
            record["labelled"] = "Yes" if labelled else "No"
        # N4 fix: split compound sample_result values
        sr = record.get("sample_result")
        if sr:
            record["sample_result"] = _split_compound_sample_result(sr)
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
    fallback_tags: List[str] = Field(default_factory=list)


class OrchestratorStats(BaseModel):
    """Aggregate orchestration statistics (Task 1.5)."""

    total_buildings: int = 0
    buildings_extracted: int = 0
    buildings_skipped: int = 0
    total_records: int = 0
    strategy_distribution: Dict[str, int] = Field(default_factory=dict)
    total_time_ms: int = 0
    plan: Optional[ExtractionPlan] = None
    fallback_activated: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Task 3: Per-Building Extraction (AC #2, #4, #5)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# E30-S7: V3 Two-Phase Extraction Helpers
# ---------------------------------------------------------------------------


async def _v3_extract_building_meta(
    building_content: str,
    plan: BuildingExtractionPlan,
    state: dict,
    schema_bundle: Optional[Any],
) -> Optional[Any]:
    """Phase 1: Extract Building__c metadata using v3_building_extraction.jinja.

    Returns None on failure (falls back to continuing without building meta).
    """
    from ai_prompter import Prompter

    from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult
    from open_notebook.extractors.prompt_context_builder import build_picklist_context
    from open_notebook.graphs.utils import provision_langchain_model

    model_id = state.get("model_id")
    doc_meta: Optional[DocumentMeta] = state.get("document_metadata")
    runnable_config: Optional[Any] = state.get("_langchain_config")

    try:
        prompt_ctx = _create_building_prompt_context(plan, doc_meta)
        picklists = build_picklist_context(schema_bundle, acm_classification=None)

        model = await provision_langchain_model(
            building_content,
            model_id,
            "extraction",
            temperature=0.1,
            max_tokens=32768,
        )
        model = _inject_response_format(
            model, _get_v3_building_schema(), "BuildingExtractionResult"
        )

        prompter = Prompter(prompt_template="acm/v3_building_extraction")
        system_prompt = prompter.render(
            data={
                "building_context": prompt_ctx,
                "picklists": picklists,
            }
        )

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"## Document Content\n\n{building_content}\n\nExtract the building metadata from the document content above."
            ),
        ]

        raw_response = await model.ainvoke(messages, config=runnable_config)
        response_text = (
            raw_response.content
            if hasattr(raw_response, "content")
            else str(raw_response)
        )
        parsed = parse_json_response(response_text)
        result: BuildingExtractionResult = BuildingExtractionResult.model_validate(
            parsed
        )
        logger.info(
            f"V3 Phase 1 [{plan.building_id}]: building_name={result.building_name!r}, "
            f"confidence={result.extraction_confidence}"
        )
        return result
    except Exception as e:
        logger.warning(
            f"V3 Phase 1 [{plan.building_id}] failed — continuing without building meta: {e}"
        )
        return None


async def _v3_extract_items(
    building_content: str,
    plan: BuildingExtractionPlan,
    building_meta: Optional[Any],
    state: dict,
    schema_bundle: Optional[Any],
    docling_tables: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    """Phase 2: Extract Item__c records using v3_item_extraction.jinja.

    building_meta is passed from Phase 1 to subset Item_Name__c picklist.
    Returns ACMItemExtractionResult (records may be empty if no ACM data).
    """
    from ai_prompter import Prompter

    from open_notebook.extractors.acm_schemas_v3 import ACMItemExtractionResult
    from open_notebook.extractors.prompt_context_builder import build_picklist_context
    from open_notebook.graphs.utils import provision_langchain_model

    model_id = state.get("model_id")
    doc_meta: Optional[DocumentMeta] = state.get("document_metadata")
    runnable_config: Optional[Any] = state.get("_langchain_config")

    # Determine acm_classification from Phase 1 for item name subsetting
    # (Phase 1 result does not carry acm_classification directly; use None to get default groups)
    acm_classification: Optional[str] = None

    try:
        prompt_ctx = _create_building_prompt_context(plan, doc_meta)
        picklists = build_picklist_context(
            schema_bundle, acm_classification=acm_classification
        )
        building_meta_dict = (
            building_meta.model_dump() if building_meta is not None else {}
        )

        model = await provision_langchain_model(
            building_content,
            model_id,
            "extraction",
            temperature=0.1,
            max_tokens=32768,
        )
        model = _inject_response_format(
            model, _get_v3_item_schema(), "ACMItemExtractionResult"
        )

        prompter = Prompter(prompt_template="acm/v3_item_extraction")
        system_prompt = prompter.render(
            data={
                "building_context": prompt_ctx,
                "building_meta": building_meta_dict,
                "picklists": picklists,
            }
        )

        from langchain_core.messages import HumanMessage, SystemMessage

        # Build HumanMessage with table priority when Docling tables are available
        if docling_tables:
            tables_html = "\n\n".join(
                f"### Table (Page {t.get('page_start', '?')})\n{t.get('raw_text', '')}"
                for t in docling_tables
                if t.get("raw_text")
            )
            human_content = (
                f"## Structured Tables (from PDF extraction — PRIMARY SOURCE)\n\n"
                f"{tables_html}\n\n"
                f"## Raw Text (for context only)\n\n"
                f"{building_content}\n\n"
                f"Extract all ACM items from the tables above. "
                f"Use raw text only to resolve ambiguities."
            )
        else:
            human_content = (
                f"## Document Content\n\n"
                f"{building_content}\n\n"
                f"Extract all ACM item records from the building content above."
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        raw_response = await model.ainvoke(messages, config=runnable_config)
        response_text = (
            raw_response.content
            if hasattr(raw_response, "content")
            else str(raw_response)
        )
        parsed = parse_json_response(response_text)
        _normalize_extraction_json(
            parsed
        )  # coerce data_issues null→[], labelled bool→str
        result: ACMItemExtractionResult = ACMItemExtractionResult.model_validate(parsed)
        logger.info(
            f"V3 Phase 2 [{plan.building_id}]: {len(result.records)} records, "
            f"status={result.status}"
        )
        return result
    except TruncationError as te:
        logger.warning(
            f"V3 Phase 2 [{plan.building_id}] JSON truncated — returning truncated result: {te}"
        )
        return ACMItemExtractionResult(
            records=[],
            status="truncated",
            extraction_notes=f"JSON truncated: {te}",
        )
    except Exception as e:
        logger.warning(
            f"V3 Phase 2 [{plan.building_id}] failed — returning empty result: {e}"
        )
        from open_notebook.extractors.acm_schemas_v3 import ACMItemExtractionResult

        return ACMItemExtractionResult(records=[], status="invalid")


def _normalize_v3_records(
    building_meta: Optional[Any],
    item_result: Any,
    plan: BuildingExtractionPlan,
) -> List[ACMExtractionRecord]:
    """Map V3 SF field names -> ACMExtractionRecord for pipeline compatibility.

    Bridges V3 two-phase output to the existing V2 ACMExtractionRecord format
    so that validate -> correct -> deduplicate -> save stages are unchanged.

    Args:
        building_meta: BuildingExtractionResult from Phase 1 (may be None).
        item_result: ACMItemExtractionResult from Phase 2.
        plan: BuildingExtractionPlan — plan.building_id is authoritative.

    Returns:
        List of ACMExtractionRecord instances.
    """
    records: List[ACMExtractionRecord] = []

    # Extract building-level fields from Phase 1 (if available)
    bldg_name: Optional[str] = None
    bldg_identifying_company: Optional[str] = None
    if building_meta is not None:
        bldg_name = building_meta.building_name
        bldg_identifying_company = building_meta.identifying_company

    for item in item_result.records:
        # Map Internal_External__c -> area_type
        area_type: Optional[str] = None
        ie = item.internal_external
        if ie == "Internal":
            area_type = "Interior"
        elif ie in ("External", "External & Internal"):
            area_type = "Exterior"

        # Map labelled -> acm_labelled bool
        acm_labelled: Optional[bool] = None
        if item.labelled == "Yes":
            acm_labelled = True
        elif item.labelled == "No":
            acm_labelled = False

        # Build data_issues list
        data_issues = list(item.data_issues) if item.data_issues else []
        if item.if_other_item_name:
            data_issues.append(f"Item name: {item.if_other_item_name}")

        # quantity: already str in ACMItemRecord
        quantity_str = item.quantity

        record = ACMExtractionRecord(
            # Building identity — plan.building_id is authoritative
            building_id=plan.building_id,
            building_name=bldg_name or plan.building_name,
            # Location
            room_name=item.room_or_area,
            floor_level=item.level,
            location=item.location_in_room,
            area_type=area_type,
            # ACM classification
            product=item.item_name or "",
            material_description=item.acm_sub_classification,
            friable=item.friability_of_material,
            # Sample and assessment
            result=item.sample_result
            or ("Assumed Positive" if item.no_access else "Unknown"),
            sample_result=item.sample_result,
            sample_no=item.nata_sample_no,
            material_condition=item.condition,
            disturbance_potential=item.disturbance_potential,
            quantity=quantity_str,
            acm_labelled=acm_labelled,
            acm_label_details=item.labelled_details,
            # Notes
            hygienist_recommendations=item.hygienist_recommendations,
            additional_comments=item.additional_comments,
            identifying_company=bldg_identifying_company,
            # Pipeline flags
            no_access=item.no_access,
            extraction_confidence=item.extraction_confidence,
            data_issues=data_issues,
            page_number=item.page_number,
        )
        records.append(record)

    return records
