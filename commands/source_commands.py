import os
import re
import time
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import ensure_record_id, repo_create
from open_notebook.domain.acm import RawExtraction
from open_notebook.domain.notebook import Source
from open_notebook.domain.transformation import Transformation
from open_notebook.extractors.pipeline_events import StageId
from open_notebook.extractors.pipeline_logger import PipelineLogger
from open_notebook.extractors.providers import get_provider_registry
from open_notebook.extractors.providers.base import PipelineTimings, ProviderError
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)

DOCLING_DIRECT_TABLE_EXTRACTION = (
    os.environ.get("DOCLING_DIRECT_TABLE_EXTRACTION", "true").lower() == "true"
)

# Documents the env var name for the dual-provider feature flag.
# The effective value is computed dynamically inside _run_dual_provider_extraction()
# so that tests can monkeypatch os.environ without reloading this module.
V3_DUAL_PROVIDER_ENV_VAR = "V3_DUAL_PROVIDER"

try:
    from open_notebook.graphs.source import source_graph
except ImportError as e:
    logger.error(f"Failed to import source_graph: {e}")
    raise ValueError("source_graph not available")

try:
    import torch as _torch
except ImportError:
    _torch = None  # type: ignore[assignment]


def full_model_dump(model):
    if isinstance(model, BaseModel):
        return model.model_dump()
    elif isinstance(model, dict):
        return {k: full_model_dump(v) for k, v in model.items()}
    elif isinstance(model, list):
        return [full_model_dump(item) for item in model]
    else:
        return model


class SourceProcessingInput(CommandInput):
    source_id: str
    content_state: Dict[str, Any]
    notebook_ids: List[str]
    transformations: List[str]
    embed: bool


class SourceProcessingOutput(CommandOutput):
    success: bool
    source_id: str
    embedded_chunks: int = 0
    insights_created: int = 0
    processing_time: float
    error_message: Optional[str] = None


def _resolve_source_pdf_path(source: Source) -> Optional[str]:
    """Resolve the PDF path from a processed source.

    Resolves relative paths (e.g. 'data/uploads/file.pdf') to absolute
    so the worker can find files regardless of its CWD.
    """
    if source.asset and source.asset.file_path:
        from pathlib import Path

        p = Path(source.asset.file_path)
        if not p.is_absolute():
            p = p.resolve()
        return str(p)
    return None


async def _extract_tables_with_docling(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> List[Dict[str, Any]]:
    """
    Run Docling Direct API on PDF, return list of table dicts.
    Runs AFTER PyMuPDF text extraction (does not replace it).

    Uses DocumentConverter directly, bypassing content-core's serialization
    layer that caused E24's row-fragmentation regression.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    if pipeline_logger:
        pipeline_logger.stage_enter(
            StageId.DOCLING_EXTRACTION, "Starting Docling table extraction"
        )

    pipeline_options = PdfPipelineOptions(do_table_structure=True, do_ocr=False)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True

    # OCR disabled: ARA PDFs are native (selectable text), not scanned images.
    # RapidOCR on 30+ pages of native text causes a CPU-bound hang (>100s).
    # The PDF parser extracts text natively; OCR is only needed for scanned docs.

    # accelerator_options belongs on PdfPipelineOptions, NOT DocumentConverter.
    # AUTO lets Docling use GPU when PyTorch has correct CUDA kernels (e.g.
    # cu128 on RTX 5090) and falls back to CPU otherwise.
    try:
        from docling.datamodel.accelerator_options import (
            AcceleratorDevice,
            AcceleratorOptions,
        )

        pipeline_options.accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.AUTO,
        )
    except ImportError:
        pass  # Older docling version without accelerator_options

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        },
    )

    result = converter.convert(pdf_path)
    doc = result.document

    tables: List[Dict[str, Any]] = []
    for idx, table in enumerate(doc.tables):
        try:
            df = table.export_to_dataframe(doc=doc)

            # --- Normalization pipeline (patterns validated in E25-S1) ---

            # 1. Fix split sample numbers: "34511-039- 001" → "34511-039-001"
            df = df.map(
                lambda v: re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))
                if isinstance(v, str)
                else v
            )

            # 2. Strip "Asbestos " prefix from hazard status
            for col in df.columns:
                col_str = str(col).lower()
                if "hazard" in col_str or "status" in col_str:
                    df[col] = df[col].apply(
                        lambda v: re.sub(r"^Asbestos\s+", "", str(v))
                        if isinstance(v, str)
                        else v
                    )

            page_no = table.prov[0].page_no if table.prov else -1

            # Capture lossless cell-level JSON for per-row extraction
            try:
                docling_json = table.data.model_dump(mode="json")
            except Exception as dj_err:
                logger.warning(f"Docling table {idx}: model_dump() failed: {dj_err}")
                docling_json = None

            tables.append(
                {
                    "table_index": idx,
                    "page": page_no,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "csv": df.to_csv(index=False),
                    "markdown": df.to_markdown(index=False),
                    "html": table.export_to_html(doc=doc),
                    "docling_json": docling_json,
                }
            )

            logger.info(
                f"Docling table {idx}: page={page_no}, rows={len(df)}, "
                f"cols={len(df.columns)}"
            )
        except Exception as e:
            logger.warning(f"Docling table {idx} export failed: {e}")
            continue

    if pipeline_logger:
        pipeline_logger.stage_complete(
            StageId.DOCLING_EXTRACTION,
            summary=f"Extracted {len(tables)} tables from {pdf_path}",
            tables_found=len(tables),
            total_rows=sum(t["rows"] for t in tables),
        )

    logger.info(f"Docling Direct API: {len(tables)} tables extracted from {pdf_path}")

    # Gap detection: warn when Docling skips pages between first and last
    # register-like tables. Helps diagnose missing records caused by
    # TableFormer failing to detect small table fragments (e.g. 1-2 rows
    # at a page boundary). See: Broadmeadows page 8 bug.
    register_pages = sorted({t["page"] for t in tables if t.get("rows", 0) >= 3})
    if len(register_pages) >= 2:
        expected_range = set(range(register_pages[0], register_pages[-1] + 1))
        all_table_pages = {t["page"] for t in tables}
        gap_pages = expected_range - all_table_pages
        if gap_pages:
            logger.warning(
                f"Docling table gap detected: pages {sorted(gap_pages)} have no "
                f"tables between first register table (page {register_pages[0]}) "
                f"and last (page {register_pages[-1]}). Small table fragments "
                f"on these pages may have been missed by TableFormer."
            )

    return tables


async def _store_docling_tables(source_id: str, tables: List[Dict[str, Any]]) -> None:
    """Store merged provider tables in acm_table_section with consensus metadata."""
    for table in tables:
        await repo_create(
            "acm_table_section",
            {
                "source_id": ensure_record_id(source_id),
                "page_start": table["page"],
                "page_end": table["page"],
                "raw_html": table.get("html"),
                "raw_text": table.get("markdown"),
                "structured_json": table.get("csv"),
                "table_type": "docling_direct_api",
                "building_name": None,
                "consensus_tier": table.get("consensus_tier"),
                "consensus_scores": table.get("consensus_scores"),
                "docling_document_json": table.get("docling_json"),
            },
        )


async def _store_raw_extractions(
    source_id: str,
    extraction_result,  # NormalizedExtractionResult
) -> int:
    """
    Persist per-provider raw extraction outputs to the raw_extraction table.

    Called immediately after provider.extract() succeeds, before
    _store_docling_tables. Returns count of rows stored.
    """
    import json

    stored = 0
    provider_id = extraction_result.provider_id
    backend_label = f"{provider_id}:2.x"

    for table in extraction_result.tables:
        bbox_dict = None
        if table.bbox is not None:
            bbox_dict = {
                "x": table.bbox.x,
                "y": table.bbox.y,
                "width": table.bbox.width,
                "height": table.bbox.height,
                "page": table.bbox.page,
            }

        # Serialise column + row count into structured_json
        structured = json.dumps(
            {
                "columns": table.columns,
                "row_count": table.row_count,
                "col_count": table.col_count,
                "table_index": table.table_index,
            }
        )

        raw = RawExtraction(
            source_id=source_id,
            provider_id=provider_id,
            extraction_backend=backend_label,
            page_number=table.page,
            raw_html=table.html,
            raw_markdown=table.markdown,
            structured_json=structured,
            bbox=bbox_dict,
            confidence=None,  # NormalizedTable has no top-level confidence in E31-S2
            officer_edits=[],
        )
        await raw.save()
        stored += 1

    logger.info(
        f"Stored {stored} raw extractions for source {source_id} "
        f"(provider={provider_id})"
    )
    return stored


def _merge_provider_tables(
    docling_result: "Any",
    mineru_result: "Any",
) -> List[Dict[str, Any]]:
    """
    Merge per-provider table outputs into a unified list for acm_table_section storage.

    Pure function — no I/O, no async. Groups tables by page number and computes
    row_divergence to assign a consensus_tier to each merged table.

    Args:
        docling_result: NormalizedExtractionResult from DoclingAdapter.extract().
        mineru_result: NormalizedExtractionResult from MinerUAdapter.extract().

    Returns:
        List of table dicts with keys: table_index, page, rows, columns, csv,
        markdown, html, consensus_tier, consensus_scores.
    """
    from collections import defaultdict

    from open_notebook.extractors.strategy_registry import (
        FallbackId,
        emit_fallback_telemetry,
    )

    # Index by page number; page <= 0 means unknown — handle separately
    # Use lists to support multiple tables per page (Bug Fix 11 Phase 2)

    docling_by_page: Dict[int, list] = defaultdict(list)
    mineru_by_page: Dict[int, list] = defaultdict(list)

    unknown_docling = []
    unknown_mineru = []

    for t in docling_result.tables:
        if t.page > 0:
            docling_by_page[t.page].append(t)
        else:
            unknown_docling.append(t)

    for t in mineru_result.tables:
        if t.page > 0:
            mineru_by_page[t.page].append(t)
        else:
            unknown_mineru.append(t)

    merged: List[Dict[str, Any]] = []
    all_pages = sorted(set(docling_by_page.keys()) | set(mineru_by_page.keys()))

    for page in all_pages:
        d_tables = docling_by_page.get(page, [])
        m_tables = mineru_by_page.get(page, [])

        if d_tables and not m_tables:
            # Only Docling has this page — emit each table
            for dt in d_tables:
                merged.append(
                    {
                        "table_index": dt.table_index,
                        "page": page,
                        "rows": dt.row_count,
                        "columns": dt.columns,
                        "csv": dt.csv,
                        "markdown": dt.markdown,
                        "html": dt.html,
                        "consensus_tier": "single_provider",
                        "consensus_scores": None,
                        "docling_json": dt.docling_json,
                    }
                )

        elif m_tables and not d_tables:
            # Only MinerU has this page — emit each table
            for mt in m_tables:
                merged.append(
                    {
                        "table_index": mt.table_index,
                        "page": page,
                        "rows": mt.row_count,
                        "columns": mt.columns,
                        "csv": mt.csv,
                        "markdown": mt.markdown,
                        "html": mt.html,
                        "consensus_tier": "single_provider",
                        "consensus_scores": None,
                        "docling_json": None,
                    }
                )

        else:
            # Both providers have this page — pair by index, compute consensus
            # Pair tables positionally; extras from either side go as single_provider
            max_len = max(len(d_tables), len(m_tables))
            for i in range(max_len):
                d_table = d_tables[i] if i < len(d_tables) else None
                m_table = m_tables[i] if i < len(m_tables) else None

                if d_table and not m_table:
                    merged.append(
                        {
                            "table_index": d_table.table_index,
                            "page": page,
                            "rows": d_table.row_count,
                            "columns": d_table.columns,
                            "csv": d_table.csv,
                            "markdown": d_table.markdown,
                            "html": d_table.html,
                            "consensus_tier": "single_provider",
                            "consensus_scores": None,
                            "docling_json": d_table.docling_json,
                        }
                    )
                elif m_table and not d_table:
                    merged.append(
                        {
                            "table_index": m_table.table_index,
                            "page": page,
                            "rows": m_table.row_count,
                            "columns": m_table.columns,
                            "csv": m_table.csv,
                            "markdown": m_table.markdown,
                            "html": m_table.html,
                            "consensus_tier": "single_provider",
                            "consensus_scores": None,
                            "docling_json": None,
                        }
                    )
                else:
                    d_rows = d_table.row_count  # type: ignore[union-attr]
                    m_rows = m_table.row_count  # type: ignore[union-attr]

                    denom = max(d_rows, m_rows)
                    row_divergence = abs(d_rows - m_rows) / denom if denom > 0 else 0.0
                    total_rows = d_rows + m_rows
                    scores = {
                        "docling": d_rows / total_rows if total_rows > 0 else 0.0,
                        "mineru": m_rows / total_rows if total_rows > 0 else 0.0,
                        "row_divergence": row_divergence,
                        "agreement": 1.0 - row_divergence,
                    }

                    if row_divergence > 0.40:
                        consensus_tier = "multi_provider_conflict"
                        emit_fallback_telemetry(
                            FallbackId.F9_PROVIDER_CONFLICT,
                            building_name=f"page={page}",
                            reason=f"row_divergence={row_divergence:.3f} (docling={d_rows}, mineru={m_rows})",
                        )
                    else:
                        consensus_tier = "multi_provider_agreement"
                        emit_fallback_telemetry(
                            FallbackId.F10_CONSENSUS_ARBITRATION,
                            building_name=f"page={page}",
                            reason=f"row_divergence={row_divergence:.3f} — MinerU HTML preferred",
                        )

                    merged.append(
                        {
                            "table_index": d_table.table_index,  # type: ignore[union-attr]
                            "page": page,
                            "rows": d_rows,
                            "columns": d_table.columns,  # type: ignore[union-attr]
                            "csv": d_table.csv,  # type: ignore[union-attr]
                            "markdown": d_table.markdown,  # type: ignore[union-attr]
                            "html": m_table.html
                            or d_table.html,  # Prefer MinerU HTML  # type: ignore[union-attr]
                            "consensus_tier": consensus_tier,
                            "consensus_scores": scores,
                            "docling_json": d_table.docling_json,  # type: ignore[union-attr]
                        }
                    )

    # Append unknown-page tables (page <= 0), Docling first, then MinerU
    _table_counter = len(merged)
    for t in unknown_docling:
        merged.append(
            {
                "table_index": _table_counter,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
                "docling_json": t.docling_json,
            }
        )
        _table_counter += 1

    for t in unknown_mineru:
        merged.append(
            {
                "table_index": _table_counter,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
                "docling_json": None,
            }
        )
        _table_counter += 1

    logger.info(
        f"_merge_provider_tables: {len(merged)} merged tables "
        f"(docling={len(docling_result.tables)}, mineru={len(mineru_result.tables)})"
    )
    return merged


async def _run_dual_provider_extraction(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> tuple[List[Dict[str, Any]], PipelineTimings]:
    """
    Run Docling then (optionally) MinerU sequentially to prevent VRAM contention.

    Returns merged table dicts ready for _store_docling_tables() and a
    PipelineTimings object with wall-clock measurements for each stage.
    When dual-provider is disabled, returns Docling-only tables with
    consensus_tier='single_provider'.

    Args:
        source_id: Fully qualified source record ID (e.g. 'source:abc123').
        pdf_path: Absolute path to the PDF file on disk.
        pipeline_logger: Optional PipelineLogger for stage observability.

    Returns:
        Tuple of (merged table dicts, PipelineTimings).
    """
    registry = get_provider_registry()
    timings = PipelineTimings()

    # Step 1: Always run Docling first
    t0 = time.perf_counter()
    docling_provider = registry.get_provider("docling")
    docling_result = docling_provider.extract(pdf_path, pipeline_logger=pipeline_logger)
    docling_provider.cleanup()
    await _store_raw_extractions(source_id, docling_result)
    timings.docling_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        f"Docling extracted {len(docling_result.tables)} tables from {pdf_path}"
    )

    # Step 2: Check dual-provider gate (read dynamically for testability)
    dual_enabled = (
        os.environ.get("V3_DUAL_PROVIDER", "true").lower() == "true"
        and os.environ.get("MINERU_ENABLED", "false").lower() == "true"
    )

    if not dual_enabled:
        logger.info(
            "Dual-provider disabled (V3_DUAL_PROVIDER or MINERU_ENABLED not set); "
            "returning Docling-only results."
        )
        timings.total_provider_ms = timings.docling_ms
        logger.info(
            f"Provider timings | "
            f"docling={timings.docling_ms}ms "
            f"mineru={timings.mineru_ms}ms "
            f"merge={timings.merge_ms}ms "
            f"total={timings.total_provider_ms}ms"
        )
        return (
            [
                {
                    "table_index": t.table_index,
                    "page": t.page,
                    "rows": t.row_count,
                    "columns": t.columns,
                    "csv": t.csv,
                    "markdown": t.markdown,
                    "html": t.html,
                    "consensus_tier": "single_provider",
                    "consensus_scores": None,
                    "docling_json": t.docling_json,
                }
                for t in docling_result.tables
            ],
            timings,
        )

    # AC3: flush GPU cache between providers (CUDA-safe guard)
    t1 = time.perf_counter()
    if _torch is not None and _torch.cuda.is_available():
        _torch.cuda.empty_cache()
        logger.debug("GPU cache flushed between Docling and MinerU")
    timings.gpu_flush_ms = int((time.perf_counter() - t1) * 1000)

    # Step 3: Run MinerU second (GPU released by Docling at this point)
    t2 = time.perf_counter()
    try:
        mineru_provider = registry.get_provider("mineru")
        mineru_result = mineru_provider.extract(pdf_path)
        mineru_provider.cleanup()
        await _store_raw_extractions(source_id, mineru_result)
        timings.mineru_ms = int((time.perf_counter() - t2) * 1000)
        logger.info(
            f"MinerU extracted {len(mineru_result.tables)} tables from {pdf_path}"
        )
    except (ProviderError, KeyError) as e:
        timings.mineru_ms = int((time.perf_counter() - t2) * 1000)
        logger.warning(f"MinerU extraction failed — falling back to Docling-only: {e}")
        timings.total_provider_ms = (
            timings.docling_ms + timings.gpu_flush_ms + timings.mineru_ms
        )
        logger.info(
            f"Provider timings | "
            f"docling={timings.docling_ms}ms "
            f"mineru={timings.mineru_ms}ms "
            f"merge={timings.merge_ms}ms "
            f"total={timings.total_provider_ms}ms"
        )
        return (
            [
                {
                    "table_index": t.table_index,
                    "page": t.page,
                    "rows": t.row_count,
                    "columns": t.columns,
                    "csv": t.csv,
                    "markdown": t.markdown,
                    "html": t.html,
                    "consensus_tier": "single_provider",
                    "consensus_scores": None,
                    "docling_json": t.docling_json,
                }
                for t in docling_result.tables
            ],
            timings,
        )

    # Step 4: Merge results
    t3 = time.perf_counter()
    merged = _merge_provider_tables(docling_result, mineru_result)
    timings.merge_ms = int((time.perf_counter() - t3) * 1000)

    timings.total_provider_ms = (
        timings.docling_ms + timings.gpu_flush_ms + timings.mineru_ms + timings.merge_ms
    )
    logger.info(
        f"Provider timings | "
        f"docling={timings.docling_ms}ms "
        f"mineru={timings.mineru_ms}ms "
        f"merge={timings.merge_ms}ms "
        f"total={timings.total_provider_ms}ms"
    )
    return merged, timings


@command(
    "process_source",
    app="open_notebook",
    retry={
        "max_attempts": 5,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "retry_on": [RuntimeError],
    },
)
async def process_source_command(
    input_data: SourceProcessingInput,
) -> SourceProcessingOutput:
    """
    Process source content using the source_graph workflow
    """
    start_time = time.time()

    try:
        logger.info(f"Starting source processing for source: {input_data.source_id}")
        logger.info(f"Notebook IDs: {input_data.notebook_ids}")
        logger.info(f"Transformations: {input_data.transformations}")
        logger.info(f"Embed: {input_data.embed}")

        # 1. Load transformation objects from IDs
        transformations = []
        for trans_id in input_data.transformations:
            logger.info(f"Loading transformation: {trans_id}")
            transformation = await Transformation.get(trans_id)
            if not transformation:
                raise ValueError(f"Transformation '{trans_id}' not found")
            transformations.append(transformation)

        logger.info(f"Loaded {len(transformations)} transformations")

        # 2. Get existing source record to update its command field
        source = await Source.get(input_data.source_id)
        if not source:
            raise ValueError(f"Source '{input_data.source_id}' not found")

        # Update source with command reference
        source.command = (
            ensure_record_id(input_data.execution_context.command_id)
            if input_data.execution_context
            else None
        )
        await source.save()

        logger.info(f"Updated source {source.id} with command reference")

        # 3. Process source with all notebooks
        logger.info(f"Processing source with {len(input_data.notebook_ids)} notebooks")

        langfuse_handler = get_langfuse_handler()
        callbacks = append_langfuse_callback([], langfuse_handler)
        invoke_metadata = build_langfuse_metadata(
            source_id=input_data.source_id,
            extraction_model="source_graph",
            document_type="source_processing",
            command_id=str(input_data.execution_context.command_id)
            if input_data.execution_context
            else None,
            extra_metadata={"workflow": "source_graph"},
        )

        # Execute source_graph with all notebooks
        try:
            if callbacks:
                result = await source_graph.ainvoke(
                    {  # type: ignore[arg-type]
                        "content_state": input_data.content_state,
                        "notebook_ids": input_data.notebook_ids,  # Use notebook_ids (plural) as expected by SourceState
                        "apply_transformations": transformations,
                        "embed": input_data.embed,
                        "source_id": input_data.source_id,  # Add the source_id to the state
                    },
                    config={
                        "callbacks": callbacks,
                        "metadata": invoke_metadata,
                    },
                )
            else:
                result = await source_graph.ainvoke(
                    {  # type: ignore[arg-type]
                        "content_state": input_data.content_state,
                        "notebook_ids": input_data.notebook_ids,  # Use notebook_ids (plural) as expected by SourceState
                        "apply_transformations": transformations,
                        "embed": input_data.embed,
                        "source_id": input_data.source_id,  # Add the source_id to the state
                    }
                )
        finally:
            flush_langfuse_handler(langfuse_handler)

        processed_source = result["source"]

        # 3b. Docling Direct API parallel extraction (E26, ADR-001 D5)
        # Runs AFTER PyMuPDF saves full_text — zero regression risk
        if DOCLING_DIRECT_TABLE_EXTRACTION:
            pdf_path = _resolve_source_pdf_path(processed_source)
            if pdf_path and pdf_path.lower().endswith(".pdf"):
                # Create a PipelineLogger for Docling stage visibility (E27-S2)
                docling_command_id = (
                    str(input_data.execution_context.command_id)
                    if input_data.execution_context
                    else None
                )
                docling_pl = PipelineLogger(
                    source_id=str(processed_source.id),
                    command_id=docling_command_id,
                )
                try:
                    # E31-S5: Dual-provider sequential extraction with consensus merge
                    merged_tables, _timings = await _run_dual_provider_extraction(
                        source_id=str(processed_source.id),
                        pdf_path=pdf_path,
                        pipeline_logger=docling_pl,
                    )
                    if merged_tables:
                        await _store_docling_tables(
                            str(processed_source.id), merged_tables
                        )
                        logger.info(
                            f"Stored {len(merged_tables)} consensus tables "
                            f"for source {processed_source.id}"
                        )
                except ProviderError as e:
                    docling_pl.stage_fail(
                        StageId.DOCLING_EXTRACTION,
                        error=str(e),
                    )
                    logger.error(f"Docling table extraction failed: {e}")
                    # Non-fatal — PyMuPDF text is already saved
                except Exception as e:
                    docling_pl.stage_fail(
                        StageId.DOCLING_EXTRACTION,
                        error=str(e),
                    )
                    logger.error(f"Unexpected error during table extraction: {e}")
                    # Non-fatal — PyMuPDF text is already saved

        # 4. Gather processing results (notebook associations handled by source_graph)
        embedded_chunks = (
            await processed_source.get_embedded_chunks() if input_data.embed else 0
        )
        insights_list = await processed_source.get_insights()
        insights_created = len(insights_list)

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully processed source: {processed_source.id} in {processing_time:.2f}s"
        )
        logger.info(
            f"Created {insights_created} insights and {embedded_chunks} embedded chunks"
        )

        return SourceProcessingOutput(
            success=True,
            source_id=str(processed_source.id),
            embedded_chunks=embedded_chunks,
            insights_created=insights_created,
            processing_time=processing_time,
        )

    except RuntimeError as e:
        # Transaction conflicts should be retried by surreal-commands
        logger.warning(f"Transaction conflict, will retry: {e}")
        raise

    except Exception as e:
        # Other errors are permanent failures
        processing_time = time.time() - start_time
        logger.error(f"Source processing failed: {e}")

        return SourceProcessingOutput(
            success=False,
            source_id=input_data.source_id,
            processing_time=processing_time,
            error_message=str(e),
        )
