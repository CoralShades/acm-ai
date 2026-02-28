"""Tests for pipeline visibility fixes (E27-S2 follow-up).

Verifies:
- Bug 1: acm_extract_command updates source.command to acm_extract command_id
- Bug 5: PipelineLogger log file path resolves to absolute repo/logs dir
- Bug 6: UPSERT uses deterministic record ID (not WHERE clause)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPipelineLoggerLogPath:
    """Bug 5: Log file path must be absolute and rooted at the project."""

    def test_log_dir_is_absolute(self):
        from open_notebook.extractors.pipeline_logger import _LOG_DIR

        assert _LOG_DIR.is_absolute(), f"_LOG_DIR should be absolute, got: {_LOG_DIR}"

    def test_log_dir_ends_with_logs(self):
        from open_notebook.extractors.pipeline_logger import _LOG_DIR

        assert _LOG_DIR.name == "logs", (
            f"_LOG_DIR should end with 'logs', got: {_LOG_DIR.name}"
        )

    def test_log_dir_is_under_project_root(self):
        from open_notebook.extractors.pipeline_logger import _LOG_DIR

        # The project root contains pyproject.toml
        project_root = _LOG_DIR.parent
        assert (project_root / "pyproject.toml").exists(), (
            f"_LOG_DIR parent should be project root with pyproject.toml, "
            f"got: {project_root}"
        )

    def test_log_file_path(self):
        from open_notebook.extractors.pipeline_logger import _LOG_FILE

        assert _LOG_FILE.name == "acm-extraction.log"
        assert _LOG_FILE.parent.is_absolute()


class TestUpsertSyntax:
    """Bug 6: UPSERT must use deterministic record ID, not WHERE clause."""

    @pytest.mark.asyncio
    async def test_persist_state_uses_record_id_not_where(self):
        """Verify the UPSERT query uses a record ID, not a WHERE clause."""
        from open_notebook.extractors.pipeline_events import (
            PipelineRunState,
            PipelineRunStatus,
            now_utc,
        )
        from open_notebook.extractors.pipeline_logger import PipelineLogger

        mock_db = AsyncMock()
        mock_db.query = AsyncMock(return_value=[])

        pl = PipelineLogger.__new__(PipelineLogger)
        pl.command_id = "command:test123"
        pl.run_id = "abcd1234"
        pl.source_id = "source:xyz"
        pl._log_entries = ["[12:00:00] test entry"]
        pl._stage_timers = {}
        pl._error_counts = {}
        pl._pipeline_start = 0

        pl._state = PipelineRunState(
            run_id=pl.run_id,
            source_id=pl.source_id,
            status=PipelineRunStatus.RUNNING,
            started_at=now_utc(),
            total_pages=0,
        )

        # db_connection is imported lazily inside _persist_state,
        # so patch it where it's imported from (the repository module).
        with patch(
            "open_notebook.database.repository.db_connection"
        ) as mock_conn:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_db)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_conn.return_value = mock_cm

            await pl._persist_state()

            # Verify query was called
            mock_db.query.assert_called_once()
            call_args = mock_db.query.call_args

            query = call_args[0][0]
            params = call_args[0][1]

            # Must NOT contain WHERE clause
            assert "WHERE" not in query, (
                f"UPSERT query should not use WHERE clause: {query}"
            )

            # Must contain record_id parameter
            assert "record_id" in params, (
                f"UPSERT should use deterministic record_id param: {params}"
            )

            # Record ID should be deterministic based on command_id
            expected_id = "extraction_progress:command_test123"
            assert params["record_id"] == expected_id, (
                f"Record ID should be '{expected_id}', got: {params['record_id']}"
            )


class TestCommandIdFlow:
    """Bug 1: acm_extract_command must update source.command."""

    @pytest.mark.asyncio
    async def test_acm_extract_updates_source_command(self):
        """Verify that acm_extract_command updates source.command to its own command_id."""
        from commands.acm_commands import ACMExtractionInput, acm_extract_command

        mock_source = MagicMock()
        mock_source.full_text = "Building 1\nRoom 101\nAsbestos: Yes"
        mock_source.title = "Test Source"
        mock_source.command = None
        mock_source.save = AsyncMock()

        mock_result = MagicMock()
        mock_result.status = "completed"
        mock_result.total_records = 5
        mock_result.records_failed = 0
        mock_result.confidence_distribution = MagicMock()
        mock_result.confidence_distribution.model_dump = MagicMock(
            return_value={"high": 3, "medium": 2}
        )

        mock_exec_ctx = MagicMock()
        mock_exec_ctx.command_id = "command:acm_extract_123"

        input_data = ACMExtractionInput(
            source_id="source:test1",
            embed_records=False,
        )
        input_data.execution_context = mock_exec_ctx

        with (
            patch(
                "commands.acm_commands._try_claim_command",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "commands.acm_commands.Source.get",
                new_callable=AsyncMock,
                return_value=mock_source,
            ),
            patch(
                "commands.acm_commands.extract_acm_from_source",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
            # ensure_record_id is imported locally in acm_commands.py,
            # so we patch it on the repository module where it's defined
            patch(
                "open_notebook.database.repository.ensure_record_id",
                side_effect=lambda x: x,
            ),
        ):
            result = await acm_extract_command(input_data)

        # Source.save should have been called (for command update)
        assert mock_source.save.called, (
            "source.save() should be called to persist command_id update"
        )

        # The command field should have been set
        assert mock_source.command == "command:acm_extract_123", (
            f"source.command should be updated to acm_extract command_id, "
            f"got: {mock_source.command}"
        )
