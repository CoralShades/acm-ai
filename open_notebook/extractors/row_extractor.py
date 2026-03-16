"""Per-row LLM extraction orchestrator for ACM register items.

Sends one table row at a time to a (small) LLM with a minimal 9-field JSON
schema.  Designed for Ollama models with num_ctx as low as 2048.

Main entry point is ``extract_all_rows()`` which:
  1. Splits multi-item rows (Type E1) via ``split_multi_item_row()``
  2. Extracts each row via ``extract_single_row()``
  3. Maps LLM output to ``ACMExtractionRecord`` via the deterministic mapper

No existing files are modified — this module only creates new code.
"""

import json
import os
import time
from copy import deepcopy
from typing import Any, Optional

from ai_prompter import Prompter
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from open_notebook.domain.acm_row_mappers import map_item_row_to_extraction_record
from open_notebook.domain.acm_row_schemas import ACMItemRow
from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.pipeline_event_bus import (
    PipelineEventBus,
    V3PipelineEvent,
)
from open_notebook.extractors.row_segmenter import RawTableRow
from open_notebook.graphs.utils import parse_json_response
from open_notebook.observability.langfuse_config import is_langfuse_enabled

# Default context window for per-row extraction (env-overridable).
_DEFAULT_ROW_NUM_CTX = 4096


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def build_kv_prompt(row: RawTableRow, building_context: str) -> str:
    """Build a key-value human-message string from a RawTableRow.

    Uses *original* column headers (from ``row.column_mapping``) rather than
    canonical names so the LLM sees the same labels as the PDF table.

    Args:
        row: The segmented table row to format.
        building_context: Human-readable building name/identifier for context.

    Returns:
        A multi-line string suitable for use as the HumanMessage content.
    """
    lines: list[str] = [f"Building: {building_context}"]
    if row.current_level:
        lines.append(f"Level: {row.current_level}")
    if row.extraction_notes:
        lines.append(f"Note: {row.extraction_notes}")
    lines.append("\nRow data:")
    for canonical, value in row.cells.items():
        if value.strip():
            original = row.column_mapping.get(canonical, canonical)
            lines.append(f"  {original}: {value}")
    return "\n".join(lines)


def _render_system_prompt(template_name: str) -> str:
    """Render a Jinja system prompt from the ``prompts/acm/`` directory.

    Args:
        template_name: Template name without extension, e.g. ``"row_extraction"``.

    Returns:
        Rendered prompt string.
    """
    return Prompter(prompt_template=f"acm/{template_name}").render(data={})


# ---------------------------------------------------------------------------
# Single-row extraction
# ---------------------------------------------------------------------------


async def extract_single_row(
    row: RawTableRow,
    building_context: str,
    model: BaseChatModel,
    langfuse_handler: Any = None,
) -> ACMItemRow:
    """Extract a single ACM item from one table row via LLM.

    Renders the ``row_extraction`` system prompt, builds a KV human message
    from *row*, calls the model, and validates the JSON response into an
    ``ACMItemRow``.  On parse/validation failure, retries **once** with the
    error message appended to the human message.

    Args:
        row: Segmented table row with cell data.
        building_context: Building name/id for the system prompt.
        model: A LangChain ``BaseChatModel`` (typically ChatOllama).
        langfuse_handler: Optional Langfuse callback handler for tracing.

    Returns:
        Validated ``ACMItemRow`` with 9 extracted fields.

    Raises:
        ValueError: If both attempts fail to produce a valid ACMItemRow.
    """
    system_prompt = _render_system_prompt("row_extraction")
    human_msg = build_kv_prompt(row, building_context)

    config: dict[str, Any] = {}
    if langfuse_handler is not None:
        config["callbacks"] = [langfuse_handler]

    max_attempts = 2
    last_error: Optional[str] = None

    for attempt in range(1, max_attempts + 1):
        current_human = human_msg
        if last_error is not None:
            current_human += (
                f"\n\nPrevious attempt failed: {last_error}\n"
                "Please return valid JSON matching the schema exactly."
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=current_human),
        ]

        try:
            response = await model.ainvoke(messages, config=config)
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            parsed = parse_json_response(content)
            item = ACMItemRow.model_validate(parsed)
            return item
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Row extraction attempt {attempt}/{max_retries} failed for row "
                "{row_idx}: {error}",
                attempt=attempt,
                max_retries=max_attempts,
                row_idx=row.row_index,
                error=last_error,
            )

    raise ValueError(
        f"Failed to extract row {row.row_index} after {max_attempts} attempts: "
        f"{last_error}"
    )


# ---------------------------------------------------------------------------
# Multi-item cell splitting (Type E1)
# ---------------------------------------------------------------------------


async def split_multi_item_row(
    row: RawTableRow,
    model: BaseChatModel,
) -> list[RawTableRow]:
    """Split a multi-item row into individual sub-rows via LLM.

    For Type E1 rows where a single cell contains multiple ACM items
    separated by newlines.  The LLM is asked to split the content into
    individual ``{"item_text": ..., "location": ...}`` objects.

    If the LLM fails or returns unparseable output, the original row is
    returned unchanged (graceful degradation).

    Args:
        row: A ``RawTableRow`` with ``needs_llm_split=True``.
        model: A LangChain ``BaseChatModel`` for the split call.

    Returns:
        List of ``RawTableRow`` objects — one per sub-item if splitting
        succeeded, or a single-element list containing the original row
        if splitting failed.
    """
    # Find the multi-item cell (the one with newlines + material keywords)
    multi_cell_key: Optional[str] = None
    multi_cell_value: Optional[str] = None
    for key, value in row.cells.items():
        if "\n" in value:
            multi_cell_key = key
            multi_cell_value = value
            break

    if multi_cell_key is None or multi_cell_value is None:
        logger.debug(
            "No multi-item cell found in row {idx}, returning as-is",
            idx=row.row_index,
        )
        return [row]

    system_prompt = _render_system_prompt("row_split")
    human_msg = f"Cell content:\n{multi_cell_value}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    try:
        response = await model.ainvoke(messages)
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        # Parse JSON array from response
        # Strip markdown fences if present
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
        if stripped.endswith("```"):
            stripped = stripped.rsplit("```", 1)[0]
        stripped = stripped.strip()

        items = json.loads(stripped)
        if not isinstance(items, list) or len(items) == 0:
            logger.warning(
                "LLM split returned non-list or empty for row {idx}",
                idx=row.row_index,
            )
            return [row]

        # Build sub-rows
        sub_rows: list[RawTableRow] = []
        for i, item in enumerate(items):
            item_text = item.get("item_text", "").strip()
            location = item.get("location", "").strip()
            if not item_text:
                continue

            new_cells = deepcopy(row.cells)
            # Replace the multi-item cell with just this item's text
            new_cells[multi_cell_key] = item_text
            if location:
                # Try to populate a location-like canonical column
                for loc_key in ("room_location", "specific_location"):
                    if loc_key in new_cells:
                        new_cells[loc_key] = location
                        break
                else:
                    new_cells["specific_location"] = location

            sub_row = RawTableRow(
                source_id=row.source_id,
                building_id=row.building_id,
                table_index=row.table_index,
                row_index=row.row_index,
                page_number=row.page_number,
                cells=new_cells,
                raw_text=f"{item_text} | {location}" if location else item_text,
                column_mapping=deepcopy(row.column_mapping),
                confidence=row.confidence * 0.9,
                needs_llm_split=False,
                is_synthetic=row.is_synthetic,
                carried_forward_fields=list(row.carried_forward_fields),
                edge_case_type="E1",
                extraction_notes=row.extraction_notes,
                current_level=row.current_level,
                source_table_num_rows=row.source_table_num_rows,
                source_table_num_cols=row.source_table_num_cols,
                bbox=deepcopy(row.bbox) if row.bbox else None,
            )
            sub_rows.append(sub_row)

        if not sub_rows:
            logger.warning(
                "LLM split produced no valid sub-items for row {idx}",
                idx=row.row_index,
            )
            return [row]

        logger.info(
            "Split row {idx} into {count} sub-items",
            idx=row.row_index,
            count=len(sub_rows),
        )
        return sub_rows

    except Exception as exc:
        logger.warning(
            "Failed to split multi-item row {idx}: {error}. Returning original row.",
            idx=row.row_index,
            error=str(exc),
        )
        return [row]


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------


async def extract_all_rows(
    rows: list[RawTableRow],
    building_context: str,
    model: BaseChatModel,
    source_id: str,
    building_id: str,
    event_bus: Optional[PipelineEventBus] = None,
    langfuse_handler: Any = None,
) -> list[ACMExtractionRecord]:
    """Extract ACM records from a list of segmented table rows.

    This is the main orchestrator for per-row extraction:

    1. For each row, if ``needs_llm_split`` is True, call
       ``split_multi_item_row()`` to get sub-rows.
    2. For each (sub-)row, call ``extract_single_row()`` to get an
       ``ACMItemRow``.
    3. Map each ``ACMItemRow`` to an ``ACMExtractionRecord`` via the
       deterministic mapper.
    4. On extraction failure after retries, create a low-confidence record
       with the failure noted in ``data_issues``.
    5. Emit SSE progress events via ``event_bus`` if provided.

    Args:
        rows: List of ``RawTableRow`` objects from the segmenter.
        building_context: Human-readable building name for prompts.
        model: A LangChain ``BaseChatModel`` (typically ChatOllama).
        source_id: Source document identifier for record provenance.
        building_id: Building identifier for record provenance.
        event_bus: Optional ``PipelineEventBus`` for SSE progress events.
        langfuse_handler: Optional Langfuse callback handler for tracing.

    Returns:
        List of ``ACMExtractionRecord`` objects, one per successfully
        extracted row (or low-confidence fallback).
    """
    records: list[ACMExtractionRecord] = []
    total = len(rows)

    # Flatten rows: expand multi-item rows first
    flat_rows: list[RawTableRow] = []
    for row in rows:
        if row.needs_llm_split:
            try:
                sub_rows = await split_multi_item_row(row, model)
                flat_rows.extend(sub_rows)
            except Exception as exc:
                logger.error(
                    "Unexpected error splitting row {idx}: {error}",
                    idx=row.row_index,
                    error=str(exc),
                )
                flat_rows.append(row)
        else:
            flat_rows.append(row)

    total_flat = len(flat_rows)
    logger.info(
        "Extracting {total} rows ({flat} after splits) for building '{building}'",
        total=total,
        flat=total_flat,
        building=building_context,
    )

    for i, row in enumerate(flat_rows):
        start_time = time.monotonic()

        try:
            item_row = await extract_single_row(
                row=row,
                building_context=building_context,
                model=model,
                langfuse_handler=langfuse_handler,
            )
            record = map_item_row_to_extraction_record(
                row=item_row,
                building_id=building_id,
                source_id=source_id,
                page_number=row.page_number,
                row_index=row.row_index,
            )
            records.append(record)

            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.debug(
                "Row {i}/{total}: extracted '{product}' in {ms}ms",
                i=i + 1,
                total=total_flat,
                product=item_row.item_name,
                ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "Row {i}/{total}: extraction failed after retries ({ms}ms): {error}",
                i=i + 1,
                total=total_flat,
                ms=duration_ms,
                error=str(exc),
            )
            # Create a low-confidence fallback record from raw row data
            fallback_record = _build_fallback_record(
                row=row,
                building_id=building_id,
                source_id=source_id,
                error_msg=str(exc),
            )
            records.append(fallback_record)

        # Emit SSE progress event
        if event_bus is not None:
            try:
                progress_event = V3PipelineEvent(
                    type="extraction.row_progress",
                    operation_id=source_id,
                    data={
                        "building_id": building_id,
                        "building_name": building_context,
                        "row": i + 1,
                        "total": total_flat,
                        "message": f"Row {i + 1}/{total_flat} extracted for {building_context}",
                    },
                )
                await event_bus.publish(progress_event)
            except Exception as bus_exc:
                logger.debug(
                    "Failed to publish SSE event: {error}",
                    error=str(bus_exc),
                )

    logger.info(
        "Completed extraction: {count}/{total} records for building '{building}'",
        count=len(records),
        total=total_flat,
        building=building_context,
    )

    return records


def _build_fallback_record(
    row: RawTableRow,
    building_id: str,
    source_id: str,
    error_msg: str,
) -> ACMExtractionRecord:
    """Build a low-confidence fallback record when extraction fails.

    Uses raw cell data to populate as many fields as possible without LLM
    assistance.

    Args:
        row: The raw table row that failed extraction.
        building_id: Building identifier.
        source_id: Source document identifier.
        error_msg: The error message from the failed extraction.

    Returns:
        An ``ACMExtractionRecord`` with ``extraction_confidence="low"`` and
        the error documented in ``data_issues``.
    """
    # Try to find a product/material description from the cells
    product = "Unknown"
    for key in ("item_description", "material", "product"):
        if key in row.cells and row.cells[key].strip():
            product = row.cells[key].strip()
            break

    # Try to find room name
    room_name = None
    for key in ("room_location", "room", "area"):
        if key in row.cells and row.cells[key].strip():
            room_name = row.cells[key].strip()
            break

    return ACMExtractionRecord(
        building_id=building_id,
        building_record_id=building_id,
        product=product,
        result="Unknown",
        room_name=room_name,
        floor_level=row.current_level,
        extraction_confidence="low",
        data_issues=[
            f"LLM extraction failed: {error_msg}",
            f"row_index: {row.row_index}",
            f"raw_text: {row.raw_text[:200]}",
        ],
        page_number=row.page_number,
    )
