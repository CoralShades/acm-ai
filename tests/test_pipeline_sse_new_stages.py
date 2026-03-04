"""Tests for new pipeline stages: DOCLING_EXTRACTION and NO_ACCESS_RECOVERY.

Validates that:
1. New StageId enums exist and have metadata
2. PipelineLogger handles new stages correctly
3. Stage ordering is consistent

Story: E27-S2 SSE/AG-UI Pipeline Visibility
"""

import pytest

from open_notebook.extractors.pipeline_events import (
    STAGE_METADATA,
    StageId,
    StageStatus,
)
from open_notebook.extractors.pipeline_logger import PipelineLogger


class TestNewStageIds:
    """Verify new StageId enums exist and have metadata."""

    def test_docling_extraction_stage_exists(self):
        assert hasattr(StageId, "DOCLING_EXTRACTION")
        assert StageId.DOCLING_EXTRACTION.value == "DOCLING_EXTRACTION"

    def test_no_access_recovery_stage_exists(self):
        assert hasattr(StageId, "NO_ACCESS_RECOVERY")
        assert StageId.NO_ACCESS_RECOVERY.value == "NO_ACCESS_RECOVERY"

    def test_docling_extraction_has_metadata(self):
        meta = STAGE_METADATA.get(StageId.DOCLING_EXTRACTION)
        assert meta is not None
        assert "name" in meta
        assert "description" in meta
        assert "log_prefix" in meta
        assert "Docling" in meta["name"]

    def test_no_access_recovery_has_metadata(self):
        meta = STAGE_METADATA.get(StageId.NO_ACCESS_RECOVERY)
        assert meta is not None
        assert "name" in meta
        assert "description" in meta
        assert "log_prefix" in meta
        assert "Recovery" in meta["name"] or "Access" in meta["name"]

    def test_all_stages_have_metadata(self):
        """Every StageId must have a corresponding metadata entry."""
        for stage in StageId:
            assert stage in STAGE_METADATA, f"Missing metadata for {stage}"

    def test_stage_count_is_nine(self):
        """Verify total stage count after adding two new stages."""
        assert len(StageId) == 9


class TestPipelineLoggerNewStages:
    """Verify PipelineLogger handles new stages without errors."""

    def test_logger_accepts_docling_stage(self):
        pl = PipelineLogger(source_id="test:123")
        # Should not raise
        pl.stage_enter(StageId.DOCLING_EXTRACTION, "Starting Docling extraction")
        pl.stage_complete(
            StageId.DOCLING_EXTRACTION,
            summary="3 tables extracted",
            tables_found=3,
        )
        state = pl.summary()
        stage = state.stages.get("DOCLING_EXTRACTION")
        assert stage is not None
        assert stage.status == StageStatus.COMPLETE

    def test_logger_accepts_recovery_stage(self):
        pl = PipelineLogger(source_id="test:456")
        pl.stage_enter(StageId.NO_ACCESS_RECOVERY, "Scanning for missed records")
        pl.stage_complete(
            StageId.NO_ACCESS_RECOVERY,
            summary="2 records recovered",
            records_recovered=2,
        )
        state = pl.summary()
        stage = state.stages.get("NO_ACCESS_RECOVERY")
        assert stage is not None
        assert stage.status == StageStatus.COMPLETE
        assert stage.metrics.get("records_recovered") == 2

    def test_logger_skip_recovery_stage(self):
        pl = PipelineLogger(source_id="test:789")
        pl.stage_skip(StageId.NO_ACCESS_RECOVERY, "No full_text available")
        state = pl.summary()
        stage = state.stages.get("NO_ACCESS_RECOVERY")
        assert stage is not None
        assert stage.status == StageStatus.SKIPPED

    def test_logger_fail_docling_stage(self):
        pl = PipelineLogger(source_id="test:fail")
        pl.stage_enter(StageId.DOCLING_EXTRACTION, "Starting")
        pl.stage_fail(StageId.DOCLING_EXTRACTION, error="Docling import failed")
        state = pl.summary()
        stage = state.stages.get("DOCLING_EXTRACTION")
        assert stage is not None
        assert stage.status == StageStatus.FAILED
        assert stage.error is not None
        assert "Docling" in stage.error.message
