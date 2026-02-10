"""PipelineLogger — structured stage-by-stage logging for the ACM extraction pipeline.

Wraps loguru to emit structured [PIPELINE] log lines and internally builds
a PipelineRunState for future SSE streaming integration.

Story: E1-S21 Extraction Pipeline Observability & Structured Logging
"""

import time
import uuid
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


class PipelineLogger:
    """Structured pipeline logger that emits [PIPELINE] log lines.

    Each extraction run gets its own PipelineLogger instance (not a singleton).
    Methods update both terminal output (via loguru) and internal PipelineRunState.
    """

    def __init__(self, source_id: str, total_pages: int = 0) -> None:
        self.run_id = str(uuid.uuid4())[:8]
        self.source_id = source_id
        self.total_pages = total_pages
        self._stage_timers: dict[str, float] = {}
        self._state = PipelineRunState(
            run_id=self.run_id,
            source_id=source_id,
            status=PipelineRunStatus.RUNNING,
            started_at=now_utc(),
            total_pages=total_pages,
        )
        self._pipeline_start = time.monotonic()

        # Emit pipeline start banner
        logger.info(f"[PIPELINE] {'=' * _SEP_WIDTH}")
        logger.info(
            f"[PIPELINE] Starting extraction for {source_id} ({total_pages} pages)"
        )
        logger.info(f"[PIPELINE] {'=' * _SEP_WIDTH}")

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

        logger.info(f"[PIPELINE] [{prefix}] STARTED | {display_msg}")

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
        logger.info(" | ".join(parts))

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
        logger.info(" | ".join(parts))

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

        logger.error(f"[PIPELINE] [{prefix}] FAILED in {duration_s:.1f}s | {error}")

    def stage_skip(self, stage_id: StageId, reason: str = "") -> None:
        """Log that a stage was skipped."""
        prefix = STAGE_METADATA[stage_id]["log_prefix"]
        stage = self._state.get_stage(stage_id)
        stage.status = StageStatus.SKIPPED
        stage.message = reason or "Skipped"

        logger.info(f"[PIPELINE] [{prefix}] SKIPPED | {reason}")

    # ------------------------------------------------------------------
    # Model tracking
    # ------------------------------------------------------------------

    def log_model(self, model_id: str, purpose: str = "extraction") -> None:
        """Track which AI model was used."""
        if model_id and model_id not in self._state.models_used:
            self._state.models_used.append(model_id)
        logger.info(f"[PIPELINE] Model provisioned: {model_id} ({purpose})")

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
        logger.info(f"[PIPELINE] {sep}")
        logger.info(
            f"[PIPELINE] EXTRACTION COMPLETE | {total_records} records in {total_duration_s:.1f}s"
        )
        logger.info(
            f"[PIPELINE]   Pages: {self._state.total_pages} | "
            f"Chunks: {total_chunks} | Buildings: {total_buildings}"
        )
        logger.info(
            f"[PIPELINE]   Records: {total_records} created, "
            f"{records_rejected} rejected, {records_unidentified} unidentified"
        )
        if confidence_distribution:
            dist_str = ", ".join(f"{k}={v}" for k, v in confidence_distribution.items())
            logger.info(f"[PIPELINE]   Confidence: {dist_str}")
        if self._state.models_used:
            logger.info(f"[PIPELINE]   Models: {', '.join(self._state.models_used)}")
        if strategy_distribution:
            strat_str = ", ".join(f"{k}={v}" for k, v in strategy_distribution.items())
            logger.info(f"[PIPELINE]   Strategy: {strat_str}")
        logger.info(f"[PIPELINE] {sep}")

        return self._state

    def fail(self, error: str) -> PipelineRunState:
        """Mark the entire pipeline as failed."""
        total_duration_s = time.monotonic() - self._pipeline_start
        total_duration_ms = int(total_duration_s * 1000)

        self._state.status = PipelineRunStatus.FAILED
        self._state.completed_at = now_utc()
        self._state.total_duration_ms = total_duration_ms

        sep = "=" * _SEP_WIDTH
        logger.error(f"[PIPELINE] {sep}")
        logger.error(
            f"[PIPELINE] EXTRACTION FAILED in {total_duration_s:.1f}s | {error}"
        )
        logger.error(f"[PIPELINE] {sep}")

        return self._state

    def summary(self) -> PipelineRunState:
        """Return current pipeline run state (read-only snapshot)."""
        return self._state.model_copy()
