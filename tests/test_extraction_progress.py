"""Tests for extraction progress persistence and SSE streaming.

Tests cover:
- PipelineLogger DB persistence (command_id enables persistence)
- PipelineLogger file sink (logs/acm-extraction.log)
- PipelineLogger log entry buffering
- SSE endpoint response format
- Command status enrichment with extraction progress
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.pipeline_events import (
    PipelineRunState,
    PipelineRunStatus,
    StageId,
    StageStatus,
)
from open_notebook.extractors.pipeline_logger import PipelineLogger

# =====================================================================
# Test PipelineLogger with command_id (DB persistence)
# =====================================================================


class TestPipelineLoggerCommandId:
    """Test PipelineLogger command_id parameter and log buffering."""

    def test_command_id_stored(self):
        """PipelineLogger stores command_id when provided."""
        pl = PipelineLogger(
            source_id="source:test",
            total_pages=5,
            command_id="command:abc123",
        )
        assert pl.command_id == "command:abc123"

    def test_command_id_none_by_default(self):
        """PipelineLogger has None command_id when not provided."""
        pl = PipelineLogger(source_id="source:test", total_pages=5)
        assert pl.command_id is None

    def test_log_entries_buffered(self):
        """Log entries are buffered in _log_entries list."""
        pl = PipelineLogger(source_id="source:test", total_pages=3)
        # __init__ already logs 3 lines (separator, start msg, separator)
        initial_count = len(pl._log_entries)
        assert initial_count >= 3

        pl.stage_enter(StageId.STRUCTURE, "Analyzing document")
        assert len(pl._log_entries) == initial_count + 1
        assert "STRUCTURE" in pl._log_entries[-1]
        assert "STARTED" in pl._log_entries[-1]

    def test_log_entries_include_timestamps(self):
        """Each log entry has a timestamp prefix."""
        pl = PipelineLogger(source_id="source:test")
        # Log entries should have [HH:MM:SS] prefix
        for entry in pl._log_entries:
            assert entry.startswith("[")
            assert "]" in entry

    def test_stage_lifecycle_updates_log_entries(self):
        """Full stage lifecycle produces expected log entries."""
        pl = PipelineLogger(source_id="source:test")
        initial = len(pl._log_entries)

        pl.stage_enter(StageId.EXTRACT, "Starting extraction")
        pl.stage_progress(StageId.EXTRACT, "Chunk 1/3", progress=0.33)
        pl.stage_complete(StageId.EXTRACT, "Done", record_count=10)

        new_entries = pl._log_entries[initial:]
        assert len(new_entries) == 3
        assert "STARTED" in new_entries[0]
        assert "Chunk 1/3" in new_entries[1]
        assert "COMPLETED" in new_entries[2]

    def test_complete_updates_state(self):
        """complete() updates internal state correctly."""
        pl = PipelineLogger(source_id="source:test")
        state = pl.complete(
            total_records=25,
            records_rejected=2,
            total_chunks=5,
            total_buildings=3,
        )
        assert state.status == PipelineRunStatus.COMPLETED
        assert state.total_records == 25
        assert state.records_rejected == 2
        assert state.total_chunks == 5
        assert state.total_buildings == 3
        assert state.completed_at is not None
        assert state.total_duration_ms is not None

    def test_fail_updates_state(self):
        """fail() updates internal state correctly."""
        pl = PipelineLogger(source_id="source:test")
        state = pl.fail("Something went wrong")
        assert state.status == PipelineRunStatus.FAILED
        assert state.completed_at is not None

    def test_schedule_persist_skipped_without_command_id(self):
        """_schedule_persist is a no-op when command_id is None."""
        pl = PipelineLogger(source_id="source:test")
        # Should not raise even without event loop
        pl._schedule_persist()

    def test_state_serialization(self):
        """PipelineRunState can be serialized to JSON for DB storage."""
        pl = PipelineLogger(
            source_id="source:test",
            total_pages=10,
            command_id="command:xyz",
        )
        pl.stage_enter(StageId.STRUCTURE)
        pl.stage_complete(StageId.STRUCTURE)
        pl.stage_enter(StageId.EXTRACT, "Extracting records")

        state_json = pl._state.model_dump_json()
        parsed = json.loads(state_json)

        assert parsed["source_id"] == "source:test"
        assert parsed["status"] == "running"
        assert "STRUCTURE" in parsed["stages"]
        assert parsed["stages"]["STRUCTURE"]["status"] == "complete"
        assert "EXTRACT" in parsed["stages"]
        assert parsed["stages"]["EXTRACT"]["status"] == "running"


# =====================================================================
# Test PipelineLogger file sink
# =====================================================================


class TestPipelineLoggerFileSink:
    """Test dedicated log file output."""

    def test_write_to_file_creates_log_dir(self, tmp_path):
        """_write_to_file creates logs/ directory if needed."""
        from open_notebook.extractors import pipeline_logger

        # Override log dir for test
        original_dir = pipeline_logger._LOG_DIR
        original_file = pipeline_logger._LOG_FILE
        original_handler = pipeline_logger._file_handler

        try:
            pipeline_logger._LOG_DIR = tmp_path / "testlogs"
            pipeline_logger._LOG_FILE = pipeline_logger._LOG_DIR / "test.log"
            pipeline_logger._file_handler = None  # Reset handler

            pipeline_logger._write_to_file("[PIPELINE] Test message")

            assert (tmp_path / "testlogs").exists()
            log_content = (tmp_path / "testlogs" / "test.log").read_text()
            assert "[PIPELINE] Test message" in log_content
        finally:
            pipeline_logger._LOG_DIR = original_dir
            pipeline_logger._LOG_FILE = original_file
            pipeline_logger._file_handler = original_handler


# =====================================================================
# Test extraction progress REST endpoint
# =====================================================================


class TestExtractionProgressEndpoint:
    """Test the extraction progress REST endpoint logic."""

    @pytest.mark.asyncio
    async def test_get_progress_returns_none_when_empty(self):
        """_get_progress returns None when no record exists."""
        from api.routers.extraction_events import _get_progress

        mock_db = AsyncMock()
        mock_db.query = AsyncMock(return_value=[[]])

        with patch("api.routers.extraction_events.db_connection") as mock_conn:
            mock_conn.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_conn.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await _get_progress("command:nonexistent")
            # Returns None when no rows found
            assert result is None

    @pytest.mark.asyncio
    async def test_get_progress_returns_record(self):
        """_get_progress returns progress record when found."""
        from api.routers.extraction_events import _get_progress

        state = PipelineRunState(
            run_id="abc123",
            source_id="source:test",
            status=PipelineRunStatus.RUNNING,
        )

        mock_row = {
            "command_id": "command:test",
            "run_id": "abc123",
            "source_id": "source:test",
            "status": "running",
            "state_json": state.model_dump_json(),
            "log_entries": ["[10:00:00] test"],
            "updated_at": "2026-02-12T00:00:00Z",
        }

        mock_db = AsyncMock()
        mock_db.query = AsyncMock(return_value=[[mock_row]])

        with patch("api.routers.extraction_events.db_connection") as mock_conn:
            mock_conn.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_conn.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await _get_progress("command:test")

        assert result is not None
        assert result["command_id"] == "command:test"
        assert result["status"] == "running"


# =====================================================================
# Test command status enrichment
# =====================================================================


class TestCommandStatusEnrichment:
    """Test that command status includes extraction progress."""

    @pytest.mark.asyncio
    async def test_enrichment_adds_progress(self):
        """get_command_status includes extraction progress when available."""
        from api.command_service import CommandService

        mock_status = MagicMock()
        mock_status.status = "running"
        mock_status.result = None
        mock_status.created = "2026-02-12T00:00:00Z"
        mock_status.updated = "2026-02-12T00:01:00Z"
        mock_status.progress = None

        progress_data = {
            "pipeline_status": "running",
            "state": {"status": "running", "stages": {}},
            "log_entries": ["test"],
        }

        with (
            patch(
                "api.command_service.get_command_status",
                new_callable=AsyncMock,
                return_value=mock_status,
            ),
            patch.object(
                CommandService,
                "_get_extraction_progress",
                new_callable=AsyncMock,
                return_value=progress_data,
            ),
        ):
            result = await CommandService.get_command_status("command:test")

        assert result["progress"] is not None
        assert result["progress"]["pipeline_status"] == "running"
        assert result["progress"]["state"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_no_enrichment_without_progress(self):
        """get_command_status returns None progress when no extraction progress."""
        from api.command_service import CommandService

        mock_status = MagicMock()
        mock_status.status = "running"
        mock_status.result = None
        mock_status.created = None
        mock_status.updated = None
        mock_status.progress = None

        with (
            patch(
                "api.command_service.get_command_status",
                new_callable=AsyncMock,
                return_value=mock_status,
            ),
            patch.object(
                CommandService,
                "_get_extraction_progress",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await CommandService.get_command_status("command:test")

        assert result["progress"] is None
