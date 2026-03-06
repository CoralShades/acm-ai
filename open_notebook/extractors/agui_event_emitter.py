"""AGUIEventEmitter — emits AG-UI protocol events during extraction.

Persists events to the SurrealDB `agui_events` table for relay
by the API SSE endpoint. Follows the same fire-and-forget pattern
as PipelineLogger._schedule_persist().

Story: E17-S1 AG-UI Extraction Pipeline Endpoint
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger


class AGUIEventEmitter:
    """Emits AG-UI protocol events during extraction.

    Events are persisted to SurrealDB agui_events table for the API
    SSE endpoint to poll and relay to the frontend.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        from pydantic_core import core_schema

        return core_schema.any_schema()

    def __init__(self, command_id: str, source_id: str) -> None:
        self.command_id = command_id
        self.source_id = source_id
        self.run_id = str(uuid.uuid4())
        self._sequence = 0
        self._start_time = time.monotonic()

    def _next_seq(self) -> int:
        self._sequence += 1
        return self._sequence

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _schedule_emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """Fire-and-forget event persistence to SurrealDB."""
        seq = self._next_seq()
        ts = self._now_iso()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_event(seq, event_type, payload, ts))
        except RuntimeError:
            pass  # No running event loop (e.g., in tests)

    async def _persist_event(
        self, sequence: int, event_type: str, payload: dict[str, Any], timestamp: str
    ) -> None:
        """Write a single event to the agui_events table."""
        try:
            from open_notebook.database.repository import db_connection

            async with db_connection() as db:
                await db.query(
                    """
                    CREATE agui_events SET
                        command_id = $command_id,
                        sequence = $sequence,
                        type = $type,
                        payload = $payload,
                        timestamp = $timestamp;
                    """,
                    {
                        "command_id": self.command_id,
                        "sequence": sequence,
                        "type": event_type,
                        "payload": payload,
                        "timestamp": timestamp,
                    },
                )
        except Exception as e:
            logger.debug(f"[AGUI] Failed to persist event: {e}")

    # ------------------------------------------------------------------
    # AG-UI Event Methods
    # ------------------------------------------------------------------

    async def emit_run_started(self) -> None:
        """Emit RunStarted event at the beginning of extraction."""
        self._schedule_emit(
            "RunStarted",
            {
                "run_id": self.run_id,
                "thread_id": self.command_id,
                "source_id": self.source_id,
            },
        )

    async def emit_step_started(self, step_name: str) -> None:
        """Emit StepStarted for a graph node entering execution."""
        self._schedule_emit(
            "StepStarted",
            {"step_name": step_name, "run_id": self.run_id},
        )

    async def emit_step_finished(self, step_name: str, **metrics: Any) -> None:
        """Emit StepFinished for a graph node completing."""
        payload: dict[str, Any] = {
            "step_name": step_name,
            "run_id": self.run_id,
        }
        if metrics:
            payload["metrics"] = metrics
        self._schedule_emit("StepFinished", payload)

    async def emit_state_delta(self, patches: list[dict[str, Any]]) -> None:
        """Emit StateDelta with RFC 6902 JSON Patch operations."""
        self._schedule_emit(
            "StateDelta",
            {"patches": patches, "run_id": self.run_id},
        )

    async def emit_tool_call_start(self, tool_call_id: str, tool_name: str) -> None:
        """Emit ToolCallStart when a tool/node begins processing."""
        self._schedule_emit(
            "ToolCallStart",
            {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "run_id": self.run_id,
            },
        )

    async def emit_tool_call_args(self, tool_call_id: str, args_json: str) -> None:
        """Emit ToolCallArgs with the arguments for a tool call."""
        self._schedule_emit(
            "ToolCallArgs",
            {
                "tool_call_id": tool_call_id,
                "args": args_json,
                "run_id": self.run_id,
            },
        )

    async def emit_tool_call_end(
        self, tool_call_id: str, result_summary: Optional[str] = None
    ) -> None:
        """Emit ToolCallEnd when a tool call completes."""
        payload: dict[str, Any] = {
            "tool_call_id": tool_call_id,
            "run_id": self.run_id,
        }
        if result_summary:
            payload["result"] = result_summary
        self._schedule_emit("ToolCallEnd", payload)

    async def emit_reasoning_content(self, message_id: str, delta: str) -> None:
        """Emit ReasoningContent with a reasoning token delta."""
        self._schedule_emit(
            "ReasoningContent",
            {
                "message_id": message_id,
                "delta": delta,
                "run_id": self.run_id,
            },
        )

    async def emit_run_finished(self, total_records: int = 0) -> None:
        """Emit RunFinished at the end of extraction."""
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._schedule_emit(
            "RunFinished",
            {
                "run_id": self.run_id,
                "total_records": total_records,
                "duration_ms": elapsed_ms,
            },
        )

    async def emit_run_error(self, error: str) -> None:
        """Emit RunError when extraction fails."""
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._schedule_emit(
            "RunError",
            {
                "run_id": self.run_id,
                "error": error,
                "duration_ms": elapsed_ms,
            },
        )
