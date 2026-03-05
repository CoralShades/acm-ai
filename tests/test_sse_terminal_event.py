"""Tests for E35-S5: SSE Terminal Event for Completed Jobs.

Verifies that the extraction_events SSE generator emits an immediate terminal
event when the job is already completed, and closes the stream without blocking.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest


class TestSSETerminalEventCompleted:
    """Verify _sse_generator emits terminal event for already-completed jobs."""

    @pytest.mark.asyncio
    async def test_completed_job_emits_done_immediately(self):
        """A completed job emits data + event: done on the first poll tick."""
        from api.routers.extraction_events import _sse_generator

        progress_row = {
            "status": "completed",
            "state_json": json.dumps({"status": "completed", "total_records": 42}),
            "log_entries": ["Done"],
            "updated_at": "2026-03-05T10:00:00Z",
        }

        with patch(
            "api.routers.extraction_events._get_progress",
            new_callable=AsyncMock,
            return_value=progress_row,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:completed_job"):
                chunks.append(chunk)

        # Should emit exactly: data event + event:done — then close
        assert len(chunks) == 2
        assert chunks[0].startswith("data: ")
        data_payload = json.loads(chunks[0].removeprefix("data: ").strip())
        assert data_payload["status"] == "completed"

        assert "event: done" in chunks[1]
        done_payload = json.loads(chunks[1].split("data: ", 1)[1].strip())
        assert done_payload["status"] == "completed"

    @pytest.mark.asyncio
    async def test_failed_job_emits_done_immediately(self):
        """A failed job emits data + event: done on the first poll tick."""
        from api.routers.extraction_events import _sse_generator

        progress_row = {
            "status": "failed",
            "state_json": None,
            "log_entries": ["Error: extraction failed"],
            "updated_at": "2026-03-05T10:00:00Z",
        }

        with patch(
            "api.routers.extraction_events._get_progress",
            new_callable=AsyncMock,
            return_value=progress_row,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:failed_job"):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert "event: done" in chunks[1]
        done_payload = json.loads(chunks[1].split("data: ", 1)[1].strip())
        assert done_payload["status"] == "failed"

    @pytest.mark.asyncio
    async def test_not_found_job_emits_error_after_max_polls(self):
        """When no DB row exists, generator emits error after _MAX_EMPTY_POLLS."""
        from api.routers.extraction_events import _MAX_EMPTY_POLLS, _sse_generator

        mock_progress = AsyncMock(return_value=None)
        with patch(
            "api.routers.extraction_events._get_progress",
            mock_progress,
        ), patch(
            "api.routers.extraction_events.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:missing_job"):
                chunks.append(chunk)

        # Should emit exactly one error event after _MAX_EMPTY_POLLS ticks
        error_chunks = [c for c in chunks if "event: error" in c]
        assert len(error_chunks) == 1
        err_payload = json.loads(error_chunks[0].split("data: ", 1)[1].strip())
        assert err_payload["status"] == "not_found"
        assert mock_progress.call_count == _MAX_EMPTY_POLLS

    @pytest.mark.asyncio
    async def test_running_job_does_not_close_stream_early(self):
        """A running job does NOT emit event: done — stream remains open."""
        from api.routers.extraction_events import _sse_generator

        call_count = 0

        async def mock_get_progress(command_id: str):
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                raise asyncio.CancelledError()
            return {
                "status": "running",
                "state_json": json.dumps({"status": "running"}),
                "log_entries": [],
                "updated_at": f"2026-03-05T10:00:0{call_count}Z",
            }

        with patch(
            "api.routers.extraction_events._get_progress",
            side_effect=mock_get_progress,
        ), patch(
            "api.routers.extraction_events.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            chunks = []
            try:
                async for chunk in _sse_generator("cmd:running_job"):
                    chunks.append(chunk)
            except asyncio.CancelledError:
                pass

        # No done events for a running job
        done_chunks = [c for c in chunks if "event: done" in c]
        assert len(done_chunks) == 0
        # But data events were emitted for the running ticks
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        assert len(data_chunks) >= 1
