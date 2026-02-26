import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.acm import ACMTableSection
from open_notebook.domain.notebook import Source
from open_notebook.domain.transformation import Transformation

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


MINERU_TABLE_TYPE = "register_html_mineru"


def _resolve_source_pdf_path(source: Source) -> Optional[str]:
    """Return local PDF path for MinerU extraction, if available."""
    if not source or not source.asset or not source.asset.file_path:
        return None

    file_path = str(source.asset.file_path)
    if Path(file_path).suffix.lower() != ".pdf":
        return None
    return file_path


async def _update_table_extraction_metadata(
    source_id: str, method: str, table_count: int
) -> None:
    """Persist table extraction metadata on source record."""
    try:
        await repo_query(
            """
            UPDATE $source_id SET
                table_extraction_method = $method,
                table_count = $table_count,
                table_extraction_updated = time::now()
            """,
            {
                "source_id": ensure_record_id(source_id),
                "method": method,
                "table_count": table_count,
            },
        )
    except Exception as e:
        logger.warning(
            "Failed to persist table extraction metadata for {source_id}: {error}",
            source_id=source_id,
            error=e,
        )


async def _store_mineru_tables(source: Source) -> int:
    """Extract and persist MinerU HTML tables with graceful Docling fallback."""
    pdf_path = _resolve_source_pdf_path(source)
    if not pdf_path:
        await _update_table_extraction_metadata(str(source.id), "docling", 0)
        return 0

    try:
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor
    except ImportError as e:
        logger.warning(
            "MinerU unavailable, skipping table extraction: {error}", error=e
        )
        await _update_table_extraction_metadata(str(source.id), "docling", 0)
        return 0

    try:
        extractor = MineruTableExtractor()
        tables = extractor.extract_tables_from_pdf(pdf_path)
    except Exception as e:
        logger.warning(
            "MinerU extraction failed for source {source_id}: {error}. "
            "Continuing with Docling-only path.",
            source_id=source.id,
            error=e,
        )
        await _update_table_extraction_metadata(str(source.id), "docling", 0)
        return 0

    if not tables:
        logger.warning(
            "MinerU returned zero tables for source {source_id}", source_id=source.id
        )
        await _update_table_extraction_metadata(str(source.id), "docling", 0)
        return 0

    await repo_query(
        "DELETE acm_table_section WHERE source_id = $source_id AND table_type = $table_type",
        {
            "source_id": ensure_record_id(source.id),
            "table_type": MINERU_TABLE_TYPE,
        },
    )

    saved_tables = 0
    for table in tables:
        raw_html = getattr(table, "html", "")
        if not raw_html:
            continue

        page_number = max(1, int(getattr(table, "page_number", 1) or 1))
        section = ACMTableSection(
            source_id=str(source.id),
            page_start=page_number,
            page_end=page_number,
            raw_html=raw_html,
            raw_text=None,
            building_name=None,
            table_type=MINERU_TABLE_TYPE,
        )
        await section.save()
        saved_tables += 1

    extraction_method = "hybrid" if saved_tables > 0 else "docling"
    await _update_table_extraction_metadata(
        str(source.id), extraction_method, saved_tables
    )

    logger.info(
        "MinerU persisted {count} tables for source {source_id}",
        count=saved_tables,
        source_id=source.id,
    )
    return saved_tables


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

        # Execute source_graph with all notebooks
        result = await source_graph.ainvoke(
            {  # type: ignore[arg-type]
                "content_state": input_data.content_state,
                "notebook_ids": input_data.notebook_ids,  # Use notebook_ids (plural) as expected by SourceState
                "apply_transformations": transformations,
                "embed": input_data.embed,
                "source_id": input_data.source_id,  # Add the source_id to the state
            }
        )

        processed_source = result["source"]

        mineru_table_count = await _store_mineru_tables(processed_source)
        if mineru_table_count > 0:
            logger.info(
                "Stored {count} MinerU HTML tables for source {source_id}",
                count=mineru_table_count,
                source_id=processed_source.id,
            )

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
