"""Tests for E1-S21: Extraction Pipeline Observability & Structured Logging.

Tests cover:
- Pydantic pipeline event models (serialization, enum values)
- PipelineLogger (stage transitions, timing, summary generation)
- Structured log format verification
- Integration: extraction produces pipeline_run in output
"""

import io
import time

import pytest
from loguru import logger

from open_notebook.extractors.pipeline_events import (
    STAGE_METADATA,
    PipelineCompletedEvent,
    PipelineRunState,
    PipelineRunStatus,
    PipelineStartedEvent,
    StageCompletedEvent,
    StageEnteredEvent,
    StageFailedEvent,
    StageId,
    StageProgressEvent,
    StageState,
    StageStatus,
    now_iso,
)
from open_notebook.extractors.pipeline_logger import PipelineLogger

# =====================================================================
# Test Pipeline Event Models
# =====================================================================


class TestStageIdEnum:
    """Test StageId enum values."""

    def test_all_stages_defined(self):
        assert len(StageId) == 7

    def test_stage_values(self):
        assert StageId.STRUCTURE == "STRUCTURE"
        assert StageId.PREFLIGHT == "PREFLIGHT"
        assert StageId.ORCHESTRATOR == "ORCHESTRATOR"
        assert StageId.EXTRACT == "EXTRACT"
        assert StageId.VALIDATE == "VALIDATE"
        assert StageId.CORRECT == "CORRECT"
        assert StageId.STORE == "STORE"


class TestStageStatusEnum:
    """Test StageStatus enum values."""

    def test_all_statuses_defined(self):
        assert len(StageStatus) == 5

    def test_status_values(self):
        assert StageStatus.PENDING == "pending"
        assert StageStatus.RUNNING == "running"
        assert StageStatus.COMPLETE == "complete"
        assert StageStatus.FAILED == "failed"
        assert StageStatus.SKIPPED == "skipped"


class TestPipelineRunStatusEnum:
    """Test PipelineRunStatus enum values."""

    def test_all_statuses_defined(self):
        assert len(PipelineRunStatus) == 5

    def test_status_values(self):
        assert PipelineRunStatus.IDLE == "idle"
        assert PipelineRunStatus.RUNNING == "running"
        assert PipelineRunStatus.COMPLETED == "completed"
        assert PipelineRunStatus.FAILED == "failed"
        assert PipelineRunStatus.PARTIAL == "partial"


class TestStageMetadata:
    """Test stage metadata constants."""

    def test_all_stages_have_metadata(self):
        for stage_id in StageId:
            assert stage_id in STAGE_METADATA, f"Missing metadata for {stage_id}"
            meta = STAGE_METADATA[stage_id]
            assert "name" in meta
            assert "description" in meta
            assert "log_prefix" in meta


class TestStageState:
    """Test StageState model."""

    def test_default_values(self):
        state = StageState(id=StageId.EXTRACT)
        assert state.status == StageStatus.PENDING
        assert state.progress == 0.0
        assert state.duration_ms is None
        assert state.metrics == {}

    def test_serialization(self):
        state = StageState(
            id=StageId.EXTRACT,
            status=StageStatus.COMPLETE,
            duration_ms=1500,
            record_count=42,
            metrics={"chunks": 7},
        )
        data = state.model_dump()
        assert data["id"] == "EXTRACT"
        assert data["status"] == "complete"
        assert data["duration_ms"] == 1500
        assert data["record_count"] == 42
        assert data["metrics"]["chunks"] == 7


class TestPipelineRunState:
    """Test PipelineRunState model."""

    def test_get_stage_creates_new(self):
        run = PipelineRunState(run_id="test", source_id="source:123")
        stage = run.get_stage(StageId.EXTRACT)
        assert stage.id == StageId.EXTRACT
        assert stage.status == StageStatus.PENDING

    def test_get_stage_returns_existing(self):
        run = PipelineRunState(run_id="test", source_id="source:123")
        stage1 = run.get_stage(StageId.EXTRACT)
        stage1.status = StageStatus.RUNNING
        stage2 = run.get_stage(StageId.EXTRACT)
        assert stage2.status == StageStatus.RUNNING

    def test_serialization_json(self):
        run = PipelineRunState(
            run_id="abc",
            source_id="source:123",
            status=PipelineRunStatus.COMPLETED,
            total_records=42,
            models_used=["gpt-4o"],
        )
        data = run.model_dump(mode="json")
        assert data["run_id"] == "abc"
        assert data["total_records"] == 42
        assert data["models_used"] == ["gpt-4o"]


class TestEventModels:
    """Test SSE event models serialize correctly."""

    def test_pipeline_started_event(self):
        event = PipelineStartedEvent(
            run_id="abc",
            source_id="source:123",
            started_at=now_iso(),
            total_pages=52,
        )
        data = event.model_dump()
        assert data["run_id"] == "abc"
        assert data["total_pages"] == 52

    def test_stage_entered_event(self):
        event = StageEnteredEvent(
            run_id="abc",
            stage_id=StageId.EXTRACT,
            stage_name="Extract",
            entered_at=now_iso(),
        )
        data = event.model_dump()
        assert data["stage_id"] == "EXTRACT"

    def test_stage_progress_event(self):
        event = StageProgressEvent(
            run_id="abc",
            stage_id=StageId.EXTRACT,
            progress=0.5,
            message="Chunk 3/7",
            records_so_far=25,
        )
        data = event.model_dump()
        assert data["progress"] == 0.5
        assert data["records_so_far"] == 25

    def test_stage_completed_event(self):
        event = StageCompletedEvent(
            run_id="abc",
            stage_id=StageId.VALIDATE,
            completed_at=now_iso(),
            duration_ms=150,
            records_extracted=82,
            summary="82 accepted, 5 rejected",
        )
        data = event.model_dump()
        assert data["duration_ms"] == 150

    def test_stage_failed_event(self):
        event = StageFailedEvent(
            run_id="abc",
            stage_id=StageId.EXTRACT,
            failed_at=now_iso(),
            duration_ms=3000,
            error="Model timeout",
        )
        data = event.model_dump()
        assert data["error"] == "Model timeout"

    def test_pipeline_completed_event(self):
        event = PipelineCompletedEvent(
            run_id="abc",
            source_id="source:123",
            completed_at=now_iso(),
            total_duration_ms=24000,
            total_records=82,
            records_rejected=5,
            confidence_distribution={"high": 68, "medium": 12, "low": 2},
        )
        data = event.model_dump()
        assert data["total_records"] == 82
        assert data["confidence_distribution"]["high"] == 68


# =====================================================================
# Test PipelineLogger
# =====================================================================


class TestPipelineLogger:
    """Test PipelineLogger stage transitions and summary."""

    def test_init_sets_running(self):
        pl = PipelineLogger(source_id="source:123", total_pages=52)
        assert pl.source_id == "source:123"
        assert pl.total_pages == 52
        assert pl._state.status == PipelineRunStatus.RUNNING

    def test_stage_enter(self):
        pl = PipelineLogger(source_id="source:123")
        pl.stage_enter(StageId.STRUCTURE, "Extracting metadata...")
        stage = pl._state.get_stage(StageId.STRUCTURE)
        assert stage.status == StageStatus.RUNNING
        assert stage.entered_at is not None

    def test_stage_progress(self):
        pl = PipelineLogger(source_id="source:123")
        pl.stage_enter(StageId.EXTRACT)
        pl.stage_progress(StageId.EXTRACT, "Chunk 2/5", progress=0.4, records_so_far=12)
        stage = pl._state.get_stage(StageId.EXTRACT)
        assert stage.progress == 0.4
        assert stage.metrics["records_so_far"] == 12

    def test_stage_complete_with_timing(self):
        pl = PipelineLogger(source_id="source:123")
        pl.stage_enter(StageId.VALIDATE)
        time.sleep(0.05)  # Small sleep to get measurable duration
        pl.stage_complete(StageId.VALIDATE, "82 accepted", accepted=82)
        stage = pl._state.get_stage(StageId.VALIDATE)
        assert stage.status == StageStatus.COMPLETE
        assert stage.duration_ms is not None
        assert stage.duration_ms >= 0
        assert stage.metrics["accepted"] == 82

    def test_stage_fail(self):
        pl = PipelineLogger(source_id="source:123")
        pl.stage_enter(StageId.EXTRACT)
        pl.stage_fail(StageId.EXTRACT, "Model timeout")
        stage = pl._state.get_stage(StageId.EXTRACT)
        assert stage.status == StageStatus.FAILED
        assert stage.error is not None
        assert stage.error.message == "Model timeout"

    def test_stage_skip(self):
        pl = PipelineLogger(source_id="source:123")
        pl.stage_skip(StageId.ORCHESTRATOR, "Not enough buildings")
        stage = pl._state.get_stage(StageId.ORCHESTRATOR)
        assert stage.status == StageStatus.SKIPPED

    def test_log_model(self):
        pl = PipelineLogger(source_id="source:123")
        pl.log_model("gpt-4o", "extraction")
        pl.log_model("gpt-4o", "correction")  # Duplicate should not add
        pl.log_model("gemini-2.0-flash", "extraction")
        assert pl._state.models_used == ["gpt-4o", "gemini-2.0-flash"]

    def test_complete_summary(self):
        pl = PipelineLogger(source_id="source:123", total_pages=52)

        # Simulate full pipeline
        pl.stage_enter(StageId.STRUCTURE)
        pl.stage_complete(StageId.STRUCTURE, "Done")
        pl.stage_enter(StageId.EXTRACT)
        pl.stage_complete(StageId.EXTRACT, "87 records")
        pl.stage_enter(StageId.VALIDATE)
        pl.stage_complete(StageId.VALIDATE, "82 accepted")
        pl.stage_enter(StageId.STORE)
        pl.stage_complete(StageId.STORE, "82 saved")

        result = pl.complete(
            total_records=82,
            records_rejected=5,
            confidence_distribution={"high": 68, "medium": 12, "low": 2},
            total_chunks=7,
            total_buildings=4,
        )

        assert result.status == PipelineRunStatus.COMPLETED
        assert result.total_records == 82
        assert result.records_rejected == 5
        assert result.total_chunks == 7
        assert result.total_buildings == 4
        assert result.total_duration_ms is not None
        assert result.confidence_distribution["high"] == 68

    def test_fail_summary(self):
        pl = PipelineLogger(source_id="source:123")
        result = pl.fail("Pipeline exploded")
        assert result.status == PipelineRunStatus.FAILED
        assert result.total_duration_ms is not None

    def test_summary_returns_copy(self):
        pl = PipelineLogger(source_id="source:123")
        s1 = pl.summary()
        s2 = pl.summary()
        assert s1 is not s2


# =====================================================================
# Test Integration: ACMExtractionOutput includes pipeline_run
# =====================================================================


class TestACMExtractionOutputPipelineRun:
    """Test that ACMExtractionOutput schema includes pipeline_run field."""

    def test_pipeline_run_field_exists(self):
        from open_notebook.extractors.acm_schemas import ACMExtractionOutput

        output = ACMExtractionOutput(
            source_id="source:123",
            status="success",
            total_records=10,
        )
        assert output.pipeline_run is None

    def test_pipeline_run_with_data(self):
        from open_notebook.extractors.acm_schemas import ACMExtractionOutput

        pipeline_data = {
            "run_id": "abc",
            "source_id": "source:123",
            "status": "completed",
            "total_records": 42,
            "models_used": ["gpt-4o"],
        }
        output = ACMExtractionOutput(
            source_id="source:123",
            status="success",
            total_records=42,
            pipeline_run=pipeline_data,
        )
        assert output.pipeline_run is not None
        assert output.pipeline_run["total_records"] == 42


# =====================================================================
# Test Structured Log Format (Review Fix M3)
# =====================================================================


class TestStructuredLogFormat:
    """Verify [PIPELINE] log output format using loguru sink capture."""

    def _capture_logs(self):
        """Set up a StringIO sink to capture loguru output."""
        buf = io.StringIO()
        handler_id = logger.add(buf, format="{message}", level="DEBUG")
        return buf, handler_id

    def test_banner_format(self):
        buf, handler_id = self._capture_logs()
        try:
            PipelineLogger(source_id="source:test", total_pages=10)
            output = buf.getvalue()
            assert "[PIPELINE]" in output
            assert "Starting extraction for source:test (10 pages)" in output
            assert "=" * 64 in output
        finally:
            logger.remove(handler_id)

    def test_stage_enter_format(self):
        buf, handler_id = self._capture_logs()
        try:
            pl = PipelineLogger(source_id="source:test")
            pl.stage_enter(StageId.EXTRACT, "Processing 5 chunks")
            output = buf.getvalue()
            assert "[PIPELINE] [EXTRACT] STARTED | Processing 5 chunks" in output
        finally:
            logger.remove(handler_id)

    def test_stage_complete_format(self):
        buf, handler_id = self._capture_logs()
        try:
            pl = PipelineLogger(source_id="source:test")
            pl.stage_enter(StageId.VALIDATE)
            pl.stage_complete(StageId.VALIDATE, "82 accepted", accepted=82)
            output = buf.getvalue()
            assert "[PIPELINE] [VALIDATE] COMPLETED in" in output
            assert "82 accepted" in output
            assert "accepted=82" in output
        finally:
            logger.remove(handler_id)

    def test_stage_progress_format(self):
        buf, handler_id = self._capture_logs()
        try:
            pl = PipelineLogger(source_id="source:test")
            pl.stage_enter(StageId.EXTRACT)
            pl.stage_progress(
                StageId.EXTRACT, "Chunk 2/5", progress=0.4, records_so_far=12
            )
            output = buf.getvalue()
            assert "[PIPELINE] [EXTRACT] Chunk 2/5" in output
            assert "records_so_far=12" in output
        finally:
            logger.remove(handler_id)

    def test_stage_fail_format(self):
        buf, handler_id = self._capture_logs()
        try:
            pl = PipelineLogger(source_id="source:test")
            pl.stage_enter(StageId.EXTRACT)
            pl.stage_fail(StageId.EXTRACT, "Model timeout")
            output = buf.getvalue()
            assert "[PIPELINE] [EXTRACT] FAILED in" in output
            assert "Model timeout" in output
        finally:
            logger.remove(handler_id)

    def test_complete_summary_format(self):
        buf, handler_id = self._capture_logs()
        try:
            pl = PipelineLogger(source_id="source:test", total_pages=52)
            pl.log_model("gpt-4o", "extraction")
            result = pl.complete(
                total_records=82,
                records_rejected=5,
                confidence_distribution={"high": 68, "medium": 12, "low": 2},
                total_chunks=7,
                total_buildings=4,
            )
            output = buf.getvalue()
            assert "EXTRACTION COMPLETE | 82 records in" in output
            assert "Pages: 52" in output
            assert "Chunks: 7" in output
            assert "Buildings: 4" in output
            assert "Records: 82 created, 5 rejected" in output
            assert "Confidence: high=68" in output
            assert "Models: gpt-4o" in output
        finally:
            logger.remove(handler_id)
