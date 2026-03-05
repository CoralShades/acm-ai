"""Tests for E35-S1: Fix Sync Upload asyncio.run() Error.

Verifies that the sync upload path uses submit_command + await wait_for_command
instead of execute_command_sync (which calls asyncio.run() and fails inside
an already-running event loop).
"""

import inspect

import pytest


class TestImportChange:
    """AC1: sources.py should import submit_command + wait_for_command, not execute_command_sync."""

    def test_no_execute_command_sync_import(self):
        """execute_command_sync must not be imported."""
        import api.routers.sources as mod

        assert not hasattr(mod, "execute_command_sync"), (
            "execute_command_sync should not be imported — it uses asyncio.run()"
        )

    def test_has_submit_command_import(self):
        """submit_command must be available."""
        import api.routers.sources as mod

        assert hasattr(mod, "submit_command"), "submit_command should be imported"

    def test_has_wait_for_command_import(self):
        """wait_for_command must be available."""
        import api.routers.sources as mod

        assert hasattr(mod, "wait_for_command"), "wait_for_command should be imported"


class TestSyncPathSourceCode:
    """AC1, AC2: Verify the sync path code uses await, not asyncio.run()."""

    def test_sync_path_does_not_call_asyncio_run(self):
        """The source code must not contain asyncio.run() calls."""
        import api.routers.sources as mod

        source_code = inspect.getsource(mod)
        assert "asyncio.run(" not in source_code, (
            "sources.py must not call asyncio.run() — causes RuntimeError inside event loop"
        )

    def test_sync_path_calls_submit_command(self):
        """The sync path must call submit_command."""
        import api.routers.sources as mod

        source_code = inspect.getsource(mod)
        assert "submit_command(" in source_code, (
            "Sync path should call submit_command to queue the command"
        )

    def test_sync_path_awaits_wait_for_command(self):
        """The sync path must await wait_for_command."""
        import api.routers.sources as mod

        source_code = inspect.getsource(mod)
        assert "await wait_for_command(" in source_code, (
            "Sync path should await wait_for_command instead of asyncio.run()"
        )


class TestAsyncPathUnchanged:
    """AC3: The async upload path must not be affected."""

    def test_async_path_still_uses_command_service(self):
        """Async path should still use CommandService.submit_command_job."""
        import api.routers.sources as mod

        source_code = inspect.getsource(mod)
        # Async path uses CommandService class, not the module-level functions
        assert "CommandService.submit_command_job" in source_code, (
            "Async path should still use CommandService.submit_command_job"
        )


class TestWaitForCommandIsAsync:
    """AC4: Verify wait_for_command is a coroutine (awaitable)."""

    def test_wait_for_command_is_coroutine(self):
        """wait_for_command must be a coroutine function so it can be awaited."""
        from surreal_commands import wait_for_command

        assert inspect.iscoroutinefunction(wait_for_command), (
            "wait_for_command must be a coroutine function"
        )

    def test_submit_command_is_sync(self):
        """submit_command should be a regular sync function (just writes to DB)."""
        from surreal_commands import submit_command

        assert not inspect.iscoroutinefunction(submit_command), (
            "submit_command should be a sync function"
        )

    @pytest.mark.asyncio
    async def test_wait_for_command_does_not_call_asyncio_run(self):
        """wait_for_command source must not use asyncio.run()."""
        from surreal_commands.core import client

        source_code = inspect.getsource(client.wait_for_command)
        assert "asyncio.run(" not in source_code, (
            "wait_for_command must not call asyncio.run()"
        )
