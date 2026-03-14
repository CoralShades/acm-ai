"""
ACM Extraction Background Commands

Handles async ACM data extraction from processed source documents.
Uses AI-powered LangGraph extraction for accurate parsing of Docling output.

Story: E1-S7 AI-Powered ACM Extraction
Fix: Bug #60 — Atomic claim prevents worker race condition (duplicate processing)
"""

import asyncio
import os
import time
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import repo_query
from open_notebook.domain.acm import ACMRecord, BuildingRecord
from open_notebook.domain.notebook import Source
from open_notebook.graphs.acm_extraction import extract_acm_from_source


def _generate_worker_id() -> str:
    """Generate a unique worker identifier from hostname + PID.

    Returns:
        A string like 'DESKTOP-ABC:12345' uniquely identifying this worker process.
    """
    import socket

    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}:{pid}"


async def _try_claim_command(command_id: str, worker_id: str) -> bool:
    """Atomically claim a command record to prevent duplicate processing.

    Uses SurrealDB UPDATE with WHERE clause for at-most-once delivery.
    Only succeeds if `claimed_by` is not already set on the record.

    Args:
        command_id: The SurrealDB command record ID (e.g., 'command:abc123').
        worker_id: Unique identifier for this worker process.

    Returns:
        True if the claim succeeded (this worker should process), False if
        already claimed by another worker.
    """
    result = await repo_query(
        "UPDATE type::thing($cmd_id) SET claimed_by = $worker_id, "
        "claimed_at = time::now() "
        "WHERE claimed_by IS NONE "
        "RETURN AFTER;",
        {"cmd_id": command_id, "worker_id": worker_id},
    )
    # UPDATE ... WHERE returns empty list if the WHERE clause didn't match
    if isinstance(result, list) and len(result) > 0:
        # Check if any result actually has our worker_id (claim succeeded)
        for row in result:
            if isinstance(row, dict) and row.get("claimed_by") == worker_id:
                return True
    return False


async def _write_terminal_status(command_id: str, status: str, records: int = 0) -> None:
    """Write terminal status to extraction_progress table.

    The PipelineLogger inside the graph writes 'running' status but may not
    write terminal status reliably. This ensures the frontend and polling
    scripts always see completion.

    Args:
        command_id: The SurrealDB command record ID (e.g., 'command:abc123').
        status: Terminal status string — 'completed' or 'failed'.
        records: Total records extracted (0 for failure paths).
    """
    try:
        import re
        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(command_id))
        await repo_query(
            f"""
            UPDATE extraction_progress:{safe_id} SET
                status = $status,
                records_total = $records,
                updated_at = time::now();
            """,
            {"status": status, "records": records},
        )
    except Exception as e:
        logger.warning(f"Failed to write terminal status for {command_id}: {e}")


class ACMExtractionInput(CommandInput):
    """Input for ACM extraction command."""

    source_id: str
    model_id: Optional[str] = None  # Optional model override
    force: bool = False  # Delete existing records before extraction (default: False)
    embed_records: bool = True  # Embed records for semantic search (E1-S6)


class ACMExtractionOutput(CommandOutput):
    """Output from ACM extraction command."""

    success: bool
    source_id: str
    records_created: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    records_embedded: int = 0  # E1-S6: Count of records with embeddings
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

    # --- Atomic claim: prevent worker race condition (Bug #60) ---
    command_id = None
    if input_data.execution_context:
        command_id = input_data.execution_context.command_id

    if command_id:
        worker_id = _generate_worker_id()
        claimed = await _try_claim_command(command_id, worker_id)
        if not claimed:
            logger.warning(
                f"Command {command_id} already claimed by another worker, "
                f"skipping (this worker: {worker_id})"
            )
            return ACMExtractionOutput(
                success=False,
                source_id=source_id,
                processing_time=time.time() - start_time,
                error_message="Command already claimed by another worker",
                extraction_method="ai",
            )
        logger.info(f"Command {command_id} claimed by worker {worker_id}")
    # --- End atomic claim ---

    try:
        logger.info(f"Starting AI-powered ACM extraction for source: {source_id}")

        # --- Update source.command to point to acm_extract job (Bug #1: fixes "0/9 stages") ---
        # The frontend reads source.command_id to determine which command to track.
        # process_source sets it to the process_source job, but by the time acm_extract
        # runs, that job is done. Update it so SSE/polling uses the correct command_id.
        if command_id:
            try:
                from open_notebook.database.repository import ensure_record_id

                _temp_source = await Source.get(source_id)
                if _temp_source:
                    _temp_source.command = ensure_record_id(command_id)
                    await _temp_source.save()
                    logger.info(
                        f"Updated source {source_id} command to acm_extract: {command_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to update source command for {source_id}: {e}")
        # --- End command update ---

        # Validate source_id format
        if not source_id or not isinstance(source_id, str):
            raise ValueError("source_id must be a non-empty string")

        # 1. Load source — wait for text content (race condition: process_source may still be running)
        MAX_WAIT_SECONDS = 120
        POLL_INTERVAL = 5
        source = None
        for _ in range(MAX_WAIT_SECONDS // POLL_INTERVAL):
            source = await Source.get(source_id)
            if source and source.full_text:
                break
            logger.info(
                f"Source {source_id} text not ready yet, waiting {POLL_INTERVAL}s..."
            )
            await asyncio.sleep(POLL_INTERVAL)

        if not source:
            raise ValueError(f"Source {source_id} not found")

        if not source.full_text:
            raise RuntimeError(
                f"Source {source_id} text unavailable after {MAX_WAIT_SECONDS}s - "
                "process_source may still be running or failed"
            )

        # Enhanced start logging (E1-S21)
        text_len = len(source.full_text) if source.full_text else 0
        logger.info(
            f"Source loaded: title='{source.title}', text_length={text_len} chars"
        )

        # 2. Delete existing records if force=True (get actual count from operation)
        deleted_count = 0
        if force:
            deleted_count = await ACMRecord.delete_by_source(source_id)
            # Also delete building records to avoid unique index collision on re-extraction
            bldg_deleted = await BuildingRecord.delete_by_source(source_id)
            if deleted_count > 0 or bldg_deleted > 0:
                logger.info(
                    f"Deleted {deleted_count} ACM records and {bldg_deleted} building records "
                    f"for source {source_id}"
                )

            # Check if table sections need re-extraction
            # (docling_document_json may be NULL or empty {} for sources processed before v3.5)
            from open_notebook.database.repository import ensure_record_id as _eri

            _sid = _eri(source_id)
            table_check = await repo_query(
                "SELECT count() as cnt FROM acm_table_section "
                "WHERE source_id=$sid AND (docling_document_json IS NULL OR docling_document_json = {}) "
                "GROUP ALL;",
                {"sid": _sid},
            )
            null_count = (
                table_check[0]["cnt"]
                if isinstance(table_check, list) and len(table_check) > 0
                else 0
            )
            if null_count > 0:
                logger.info(
                    f"Found {null_count} stale acm_table_section rows "
                    f"(missing docling_document_json) for {source_id} — re-extracting"
                )
                await repo_query(
                    "DELETE FROM acm_table_section WHERE source_id=$sid;",
                    {"sid": _sid},
                )
                # Re-run table extraction to populate docling_document_json
                from commands.source_commands import (
                    _resolve_source_pdf_path,
                    _run_dual_provider_extraction,
                    _store_docling_tables,
                )

                pdf_path = _resolve_source_pdf_path(source)
                if pdf_path:
                    merged_tables, _timings = await _run_dual_provider_extraction(
                        source_id=source_id,
                        pdf_path=pdf_path,
                    )
                    if merged_tables:
                        await _store_docling_tables(source_id, merged_tables)
                        logger.info(
                            f"Re-extracted {len(merged_tables)} tables for {source_id}"
                        )

        # Extract command_id from execution context for progress tracking
        # (command_id already set above during atomic claim)

        # 3. Run AI extraction (deletion already handled above, so pass force=False)
        result = await extract_acm_from_source(
            source=source,
            model_id=model_id,
            force=False,  # Don't delete again, we already handled it
            command_id=command_id,
        )

        processing_time = time.time() - start_time

        # 4. Return result
        if result.status == "failed":
            logger.error(f"AI ACM extraction failed for {source_id}: {result.error}")
            if command_id:
                await _write_terminal_status(command_id, "failed", 0)
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
            if command_id:
                await _write_terminal_status(command_id, "completed", 0)
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

        # 5. Embed records for semantic search (E1-S6)
        embedded_count = 0
        if input_data.embed_records and result.total_records > 0:
            embed_start = time.time()
            try:
                from api.services.acm_embedding_service import ACMEmbeddingService
                from open_notebook.domain.acm import ACMEmbeddingConfig

                logger.info(
                    f"[PIPELINE] [EMBED] STARTED | Embedding {result.total_records} records..."
                )

                # Load the freshly created records
                records = await ACMRecord.get_by_source(source_id)

                if records:
                    # Embed records
                    embedding_service = ACMEmbeddingService(ACMEmbeddingConfig())
                    embedded_records = await embedding_service.embed_records(records)

                    # Save embedded records back to database
                    for record in embedded_records:
                        if record.embedding:
                            await record.save()
                            embedded_count += 1

                    embed_time = time.time() - embed_start
                    logger.info(
                        f"[PIPELINE] [EMBED] COMPLETED in {embed_time:.1f}s | "
                        f"{embedded_count}/{len(records)} records embedded"
                    )

            except Exception as e:
                embed_time = time.time() - embed_start
                # Embedding failure should not fail the entire extraction
                logger.warning(
                    f"[PIPELINE] [EMBED] FAILED in {embed_time:.1f}s | "
                    f"records saved without embeddings: {e}"
                )

        processing_time = time.time() - start_time

        # Convert ConfidenceDistribution model to dict for output serialization
        conf_dist = None
        if result.confidence_distribution:
            conf_dist = result.confidence_distribution.model_dump()

        if command_id:
            await _write_terminal_status(command_id, "completed", result.total_records)

        return ACMExtractionOutput(
            success=True,
            source_id=source_id,
            records_created=result.total_records,
            records_deleted=deleted_count,
            records_failed=result.records_failed,
            records_embedded=embedded_count,
            processing_time=processing_time,
            confidence_distribution=conf_dist,
            extraction_method="ai",
        )

    except RuntimeError as e:
        # Transaction conflicts - retry
        logger.warning(f"Transaction conflict during ACM extraction: {e}")
        raise

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"ACM extraction failed for {source_id}: {e}")
        if command_id:
            await _write_terminal_status(command_id, "failed", 0)
        return ACMExtractionOutput(
            success=False,
            source_id=source_id,
            processing_time=processing_time,
            error_message=str(e),
            extraction_method="ai",
        )
