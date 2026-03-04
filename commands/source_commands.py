import os
import re
import time
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import ensure_record_id, repo_create
from open_notebook.domain.notebook import Source
from open_notebook.domain.transformation import Transformation
from open_notebook.extractors.pipeline_events import StageId
from open_notebook.extractors.pipeline_logger import PipelineLogger
from open_notebook.extractors.providers import get_provider_registry
from open_notebook.extractors.providers.base import ProviderError
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)

DOCLING_DIRECT_TABLE_EXTRACTION = (
    os.environ.get("DOCLING_DIRECT_TABLE_EXTRACTION", "true").lower() == "true"
)

try:
    from open_notebook.graphs.source import source_graph
except ImportError as e:
    logger.error(f"Failed to import source_graph: {e}")
    raise ValueError("source_graph not available")


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
    """Resolve the PDF path from a processed source."""
    if source.asset and source.asset.file_path:
        return str(source.asset.file_path)
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

    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
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

            tables.append(
                {
                    "table_index": idx,
                    "page": page_no,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "csv": df.to_csv(index=False),
                    "markdown": df.to_markdown(index=False),
                    "html": table.export_to_html(doc=doc),
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
    return tables


async def _store_docling_tables(source_id: str, tables: List[Dict[str, Any]]) -> None:
    """Store Docling DataFrame tables in acm_table_section."""
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
            },
        )


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
                    # E31-S2: Use provider registry instead of inline Docling call
                    provider = get_provider_registry().get_default()
                    extraction_result = provider.extract(
                        pdf_path, pipeline_logger=docling_pl
                    )
                    docling_tables = [
                        {
                            "table_index": t.table_index,
                            "page": t.page,
                            "rows": t.row_count,
                            "columns": t.columns,
                            "csv": t.csv,
                            "markdown": t.markdown,
                            "html": t.html,
                        }
                        for t in extraction_result.tables
                    ]
                    if docling_tables:
                        await _store_docling_tables(
                            str(processed_source.id), docling_tables
                        )
                        logger.info(
                            f"Stored {len(docling_tables)} Docling tables "
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
