"""
ACM Extraction Background Commands

Handles async ACM data extraction from processed source documents.
"""

import time
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.domain.acm import ACMRecord
from open_notebook.domain.notebook import Source
from open_notebook.extractors.acm_extractor import extract_acm_records


class ACMExtractionInput(CommandInput):
    """Input for ACM extraction command."""

    source_id: str


class ACMExtractionOutput(CommandOutput):
    """Output from ACM extraction command."""

    success: bool
    source_id: str
    records_created: int = 0
    records_deleted: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None


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
    Extract ACM records from a processed source document.

    This command:
    1. Loads the source and its full_text (Docling markdown output)
    2. Deletes any existing ACM records for this source (idempotency)
    3. Parses the markdown to extract ACM table data
    4. Creates ACMRecord objects and saves to database
    """
    start_time = time.time()
    source_id = input_data.source_id

    try:
        logger.info(f"Starting ACM extraction for source: {source_id}")

        # 1. Load source
        source = await Source.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        if not source.full_text:
            raise ValueError(f"Source {source_id} has no text content")

        # 2. Delete existing records for idempotency
        deleted_count = await ACMRecord.delete_by_source(source_id)
        if deleted_count > 0:
            logger.info(
                f"Deleted {deleted_count} existing ACM records for re-extraction"
            )

        # 3. Extract ACM data from markdown
        extracted_dicts = extract_acm_records(source.full_text, source_id)

        if not extracted_dicts:
            logger.warning(f"No ACM records found in source {source_id}")
            return ACMExtractionOutput(
                success=True,
                source_id=source_id,
                records_created=0,
                records_deleted=deleted_count,
                processing_time=time.time() - start_time,
            )

        # 4. Create and save ACM records
        created_count = 0
        for record_dict in extracted_dicts:
            try:
                record = ACMRecord(**record_dict)
                await record.save()
                created_count += 1
            except Exception as e:
                logger.warning(f"Failed to create ACM record: {e}")
                continue

        processing_time = time.time() - start_time
        logger.info(
            f"ACM extraction complete for {source_id}: "
            f"{created_count} records created in {processing_time:.2f}s"
        )

        return ACMExtractionOutput(
            success=True,
            source_id=source_id,
            records_created=created_count,
            records_deleted=deleted_count,
            processing_time=processing_time,
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
        )
