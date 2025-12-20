"""
ACM Extraction Background Commands

Handles async ACM data extraction from processed source documents.
Uses AI-powered LangGraph extraction for accurate parsing of Docling output.

Story: E1-S7 AI-Powered ACM Extraction
"""

import time
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.domain.acm import ACMRecord
from open_notebook.domain.notebook import Source
from open_notebook.graphs.acm_extraction import extract_acm_from_source


class ACMExtractionInput(CommandInput):
    """Input for ACM extraction command."""

    source_id: str
    model_id: Optional[str] = None  # Optional model override
    force: bool = False  # Delete existing records before extraction (default: False)


class ACMExtractionOutput(CommandOutput):
    """Output from ACM extraction command."""

    success: bool
    source_id: str
    records_created: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    # New AI extraction fields
    confidence_distribution: Optional[dict] = None
    extraction_method: str = "ai"  # "ai" or "regex" (for fallback)


@command(
    "acm_extract",
    app="open_notebook",
    retry={
        "max_attempts": 3,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "retry_on": [RuntimeError],
    },
)
async def acm_extract_command(input_data: ACMExtractionInput) -> ACMExtractionOutput:
    """
    Extract ACM records from a processed source document using AI.

    This command:
    1. Loads the source and its full_text (Docling output)
    2. Uses LangGraph AI extraction to parse content
    3. Validates and deduplicates extracted records
    4. Saves ACMRecord objects to database with confidence scores

    The AI extraction handles:
    - Plain text without pipe tables (Docling format)
    - Context inference (building/room hierarchy)
    - Confidence scoring (high/medium/low)
    - Data issue tracking
    """
    start_time = time.time()
    source_id = input_data.source_id
    model_id = input_data.model_id
    force = input_data.force

    try:
        logger.info(f"Starting AI-powered ACM extraction for source: {source_id}")

        # Validate source_id format
        if not source_id or not isinstance(source_id, str):
            raise ValueError("source_id must be a non-empty string")

        # 1. Load source
        source = await Source.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        if not source.full_text:
            raise ValueError(f"Source {source_id} has no text content")

        # 2. Delete existing records if force=True (get actual count from operation)
        deleted_count = 0
        if force:
            deleted_count = await ACMRecord.delete_by_source(source_id)
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} existing ACM records for source {source_id}")

        # 3. Run AI extraction (deletion already handled above, so pass force=False)
        result = await extract_acm_from_source(
            source=source,
            model_id=model_id,
            force=False,  # Don't delete again, we already handled it
        )

        processing_time = time.time() - start_time

        # 4. Return result
        if result.status == "failed":
            logger.error(
                f"AI ACM extraction failed for {source_id}: {result.error}"
            )
            return ACMExtractionOutput(
                success=False,
                source_id=source_id,
                records_created=0,
                records_deleted=deleted_count,
                records_failed=result.records_failed,
                processing_time=processing_time,
                error_message=result.error,
                extraction_method="ai",
            )

        if result.status == "no_data":
            logger.info(f"No ACM records found in source {source_id}")
            return ACMExtractionOutput(
                success=True,
                source_id=source_id,
                records_created=0,
                records_deleted=deleted_count,
                records_failed=result.records_failed,
                processing_time=processing_time,
                extraction_method="ai",
            )

        logger.info(
            f"AI ACM extraction complete for {source_id}: "
            f"{result.total_records} records created in {processing_time:.2f}s "
            f"(confidence: {result.confidence_distribution})"
        )

        return ACMExtractionOutput(
            success=True,
            source_id=source_id,
            records_created=result.total_records,
            records_deleted=deleted_count,
            records_failed=result.records_failed,
            processing_time=processing_time,
            confidence_distribution=result.confidence_distribution,
            extraction_method="ai",
        )

    except RuntimeError as e:
        # Transaction conflicts - retry
        logger.warning(f"Transaction conflict during ACM extraction: {e}")
        raise

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"ACM extraction failed for {source_id}: {e}")
        return ACMExtractionOutput(
            success=False,
            source_id=source_id,
            processing_time=processing_time,
            error_message=str(e),
            extraction_method="ai",
        )
