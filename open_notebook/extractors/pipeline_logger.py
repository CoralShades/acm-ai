"""PipelineLogger — structured stage-by-stage logging for the ACM extraction pipeline.

Wraps loguru to emit structured [PIPELINE] log lines and internally builds
a PipelineRunState for future SSE streaming integration.

Persists state to SurrealDB extraction_progress table for real-time
frontend progress tracking via SSE streaming.

Story: E1-S21 Extraction Pipeline Observability & Structured Logging
"""

import asyncio
import os
import time
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from open_notebook.extractors.pipeline_events import (
    STAGE_METADATA,
    PipelineRunState,
    PipelineRunStatus,
    StageError,
    StageId,
    StageStatus,
    now_utc,
)

# Width of separator lines
_SEP_WIDTH = 64

# Log file config
_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "acm-extraction.log"
_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
_LOG_BACKUP_COUNT = 5

# Module-level file handler (shared across PipelineLogger instances)
_file_handler: Optional[RotatingFileHandler] = None


def _get_file_handler() -> RotatingFileHandler:
    """Get or create the rotating file handler for extraction logs."""
    global _file_handler
    if _file_handler is None:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _file_handler = RotatingFileHandler(
            str(_LOG_FILE),
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
    return _file_handler


def _write_to_file(message: str) -> None:
    """Write a timestamped message to the extraction log file."""
    try:
        handler = _get_file_handler()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        record_msg = f"[{ts}] {message}\n"
        handler.stream.write(record_msg)
        handler.stream.flush()
    except Exception:
        pass  # File logging is best-effort


class PipelineLogger:
    """Structured pipeline logger that emits [PIPELINE] log lines.

    Each extraction run gets its own PipelineLogger instance (not a singleton).
    Methods update both terminal output (via loguru) and internal PipelineRunState.
    When command_id is provided, state is persisted to SurrealDB for SSE streaming.
    """

    def __init__(
        self,
        source_id: str,
        total_pages: int = 0,
        command_id: Optional[str] = None,
    ) -> None:
        self.run_id = str(uuid.uuid4())[:8]
        self.source_id = source_id
        self.total_pages = total_pages
        self.command_id = command_id
        self._stage_timers: dict[str, float] = {}
        self._log_entries: list[str] = []
        self._state = PipelineRunState(
            run_id=self.run_id,
            source_id=source_id,
            status=PipelineRunStatus.RUNNING,
            started_at=now_utc(),
            total_pages=total_pages,
        )
        self._pipeline_start = time.monotonic()

        # Emit pipeline start banner
        start_msg = f"Starting extraction for {source_id} ({total_pages} pages)"
        self._log(f"[PIPELINE] {'=' * _SEP_WIDTH}")
        self._log(f"[PIPELINE] {start_msg}")
        self._log(f"[PIPELINE] {'=' * _SEP_WIDTH}")

        # Persist initial state
        self._schedule_persist()

    # ------------------------------------------------------------------
    # Internal logging + persistence
    # ------------------------------------------------------------------

    def _log(self, message: str, level: str = "info") -> None:
        """Log to loguru, file, and buffer."""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

        # Append to in-memory buffer for DB persistence
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self._log_entries.append(f"[{ts}] {message}")

        # Write to dedicated log file
        _write_to_file(message)

    def _schedule_persist(self) -> None:
        """Schedule async state persistence (fire-and-forget from sync context)."""
        if not self.command_id:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_state())
        except RuntimeError:
            # No running event loop - skip persistence (e.g., in tests)
            pass

    async def _persist_state(self) -> None:
        """Upsert current pipeline state to SurrealDB extraction_progress table."""
        if not self.command_id:
            return
        try:
            from open_notebook.database.repository import db_connection

            state_json = self._state.model_dump_json()
            # Keep last 200 log entries to avoid unbounded growth
            recent_logs = self._log_entries[-200:]

            async with db_connection() as db:
                await db.query(
                    """
                    UPSERT extraction_progress
                    SET command_id = $command_id,
                        run_id = $run_id,
                        source_id = $source_id,
                        status = $status,
                        state_json = $state_json,
                        log_entries = $log_entries,
                        updated_at = time::now()
                    WHERE command_id = $command_id;
                    """,
                    {
                        "command_id": self.command_id,
                        "run_id": self.run_id,
                        "source_id": self.source_id,
                        "status": self._state.status.value,
                        "state_json": state_json,
                        "log_entries": recent_logs,
                    },
                )
        except Exception as e:
            # DB persistence is best-effort — don't break the pipeline
            logger.debug(f"[PIPELINE] Failed to persist state: {e}")

    # ------------------------------------------------------------------
    # Stage lifecycle
    # ------------------------------------------------------------------

    def stage_enter(self, stage_id: StageId, message: str = "") -> None:
        """Log stage entry and start timing."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        display_msg = message or STAGE_METADATA[stage_id]["description"]

        self._stage_timers[stage_id.value] = time.monotonic()
        stage = self._state.get_stage(stage_id)
        stage.status = StageStatus.RUNNING
        stage.entered_at = now_utc()
        stage.message = display_msg

        self._log(f"[PIPELINE] [{prefix}] STARTED | {display_msg}")
        self._schedule_persist()

    def stage_progress(
        self,
        stage_id: StageId,
        message: str,
        progress: float = 0.0,
        **metrics: Any,
    ) -> None:
        """Log intra-stage progress (e.g., per-chunk updates)."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        stage = self._state.get_stage(stage_id)
        stage.progress = progress
        stage.message = message
        if metrics:
            stage.metrics.update(metrics)

        parts = [f"[PIPELINE] [{prefix}] {message}"]
        for k, v in metrics.items():
            parts.append(f"{k}={v}")
        self._log(" | ".join(parts))
        self._schedule_persist()

    def stage_complete(
        self,
        stage_id: StageId,
        summary: str = "",
        **metrics: Any,
    ) -> None:
        """Log stage completion with timing and metrics."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        start = self._stage_timers.get(stage_id.value, time.monotonic())
        duration_s = time.monotonic() - start
        duration_ms = int(duration_s * 1000)

        stage = self._state.get_stage(stage_id)
        stage.status = StageStatus.COMPLETE
        stage.completed_at = now_utc()
        stage.duration_ms = duration_ms
        stage.progress = 1.0
        if metrics:
            stage.metrics.update(metrics)
        if "record_count" in metrics:
            stage.record_count = metrics["record_count"]

        parts = [f"[PIPELINE] [{prefix}] COMPLETED in {duration_s:.1f}s"]
        if summary:
            parts.append(summary)
        for k, v in metrics.items():
            parts.append(f"{k}={v}")
        self._log(" | ".join(parts))
        self._schedule_persist()

    def stage_fail(self, stage_id: StageId, error: str) -> None:
        """Log stage failure."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        start = self._stage_timers.get(stage_id.value, time.monotonic())
        duration_s = time.monotonic() - start
        duration_ms = int(duration_s * 1000)

        stage = self._state.get_stage(stage_id)
        stage.status = StageStatus.FAILED
        stage.completed_at = now_utc()
        stage.duration_ms = duration_ms
        stage.error = StageError(message=error)

        self._log(
            f"[PIPELINE] [{prefix}] FAILED in {duration_s:.1f}s | {error}",
            level="error",
        )
        self._schedule_persist()

    def stage_skip(self, stage_id: StageId, reason: str = "") -> None:
        """Log that a stage was skipped."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        stage = self._state.get_stage(stage_id)
        stage.status = StageStatus.SKIPPED
        stage.message = reason or "Skipped"

        self._log(f"[PIPELINE] [{prefix}] SKIPPED | {reason}")
        self._schedule_persist()

    # ------------------------------------------------------------------
    # Model tracking
    # ------------------------------------------------------------------

    def log_model(self, model_id: str, purpose: str = "extraction") -> None:
        """Track which AI model was used."""
        if model_id and model_id not in self._state.models_used:
            self._state.models_used.append(model_id)
        self._log(f"[PIPELINE] Model provisioned: {model_id} ({purpose})")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def complete(
        self,
        total_records: int = 0,
        records_rejected: int = 0,
        records_unidentified: int = 0,
        confidence_distribution: Optional[dict] = None,
        total_chunks: int = 0,
        total_buildings: int = 0,
        strategy_distribution: Optional[dict] = None,
    ) -> PipelineRunState:
        """Finalize the pipeline run and log the summary block."""
        total_duration_s = time.monotonic() - self._pipeline_start
        total_duration_ms = int(total_duration_s * 1000)

        self._state.status = PipelineRunStatus.COMPLETED
        self._state.completed_at = now_utc()
        self._state.total_duration_ms = total_duration_ms
        self._state.total_records = total_records
        self._state.records_rejected = records_rejected
        self._state.records_unidentified = records_unidentified
        self._state.total_chunks = total_chunks
        self._state.total_buildings = total_buildings
        if confidence_distribution:
            self._state.confidence_distribution = confidence_distribution
        if strategy_distribution:
            self._state.strategy_distribution = strategy_distribution

        # Emit summary block
        sep = "=" * _SEP_WIDTH
        self._log(f"[PIPELINE] {sep}")
        self._log(
            f"[PIPELINE] EXTRACTION COMPLETE | {total_records} records in {total_duration_s:.1f}s"
        )
        self._log(
            f"[PIPELINE]   Pages: {self._state.total_pages} | "
            f"Chunks: {total_chunks} | Buildings: {total_buildings}"
        )
        self._log(
            f"[PIPELINE]   Records: {total_records} created, "
            f"{records_rejected} rejected, {records_unidentified} unidentified"
        )
        if confidence_distribution:
            dist_str = ", ".join(f"{k}={v}" for k, v in confidence_distribution.items())
            self._log(f"[PIPELINE]   Confidence: {dist_str}")
        if self._state.models_used:
            self._log(f"[PIPELINE]   Models: {', '.join(self._state.models_used)}")
        if strategy_distribution:
            strat_str = ", ".join(f"{k}={v}" for k, v in strategy_distribution.items())
            self._log(f"[PIPELINE]   Strategy: {strat_str}")
        self._log(f"[PIPELINE] {sep}")

        self._schedule_persist()
        return self._state

    def fail(self, error: str) -> PipelineRunState:
        """Mark the entire pipeline as failed."""
        total_duration_s = time.monotonic() - self._pipeline_start
        total_duration_ms = int(total_duration_s * 1000)

        self._state.status = PipelineRunStatus.FAILED
        self._state.completed_at = now_utc()
        self._state.total_duration_ms = total_duration_ms

        sep = "=" * _SEP_WIDTH
        self._log(f"[PIPELINE] {sep}", level="error")
        self._log(
            f"[PIPELINE] EXTRACTION FAILED in {total_duration_s:.1f}s | {error}",
            level="error",
        )
        self._log(f"[PIPELINE] {sep}", level="error")

        self._schedule_persist()
        return self._state

    def summary(self) -> PipelineRunState:
        """Return current pipeline run state (read-only snapshot)."""
        return self._state.model_copy()
