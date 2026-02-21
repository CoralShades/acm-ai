"""AG-UI SSE endpoint for extraction pipeline events.

Polls the `agui_events` SurrealDB table and streams events as SSE
to the frontend. Works alongside the existing extraction-progress
SSE endpoint (non-breaking).

Story: E17-S1 AG-UI Extraction Pipeline Endpoint
"""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger

from open_notebook.database.repository import db_connection

router = APIRouter()

# SSE config
_POLL_INTERVAL_S = 0.5
_HEARTBEAT_INTERVAL_S = 15.0
_TERMINAL_TYPES = {"RunFinished", "RunError"}


async def _poll_events(command_id: str, after_seq: int = 0) -> list[dict]:
    """Fetch new AG-UI events from SurrealDB after a given sequence number."""
    try:
        async with db_connection() as db:
            result = await db.query(
                """
                SELECT * FROM agui_events
                WHERE command_id = $cid AND sequence > $after_seq
                ORDER BY sequence ASC
                LIMIT 50;
                """,
                {"cid": command_id, "after_seq": after_seq},
            )
            if result and isinstance(result, list):
                rows = result[0] if isinstance(result[0], list) else result
                if isinstance(rows, list):
                    return rows
                if isinstance(rows, dict) and "result" in rows:
                    inner = rows["result"]
                    if isinstance(inner, list):
                        return inner
        return []
    except Exception as e:
        logger.debug(f"[AGUI] Failed to poll events: {e}")
        return []


async def _sse_generator(command_id: str):
    """Generate SSE events by polling agui_events table."""
    last_seq = 0
    heartbeat_counter = 0
    polls_per_heartbeat = int(_HEARTBEAT_INTERVAL_S / _POLL_INTERVAL_S)

    while True:
        events = await _poll_events(command_id, last_seq)

        for event in events:
            seq = event.get("sequence", 0)
            if seq > last_seq:
                last_seq = seq

            event_type = event.get("type", "unknown")
            payload = event.get("payload", {})
            timestamp = event.get("timestamp", "")

            sse_data = {
                "type": event_type,
                "sequence": seq,
                "timestamp": timestamp,
                **payload,
            }
            yield f"event: {event_type}\ndata: {json.dumps(sse_data)}\n\n"

            # Close stream on terminal events
            if event_type in _TERMINAL_TYPES:
                yield f"event: done\ndata: {json.dumps({'type': event_type})}\n\n"
                return

        # Heartbeat to keep connection alive
        if heartbeat_counter >= polls_per_heartbeat:
            yield ": heartbeat\n\n"
            heartbeat_counter = 0

        heartbeat_counter += 1
        await asyncio.sleep(_POLL_INTERVAL_S)


@router.get("/agui/extraction/{command_id}/stream")
async def stream_agui_extraction(command_id: str):
    """SSE endpoint streaming AG-UI protocol events for an extraction run.

    Connect with EventSource to receive real-time extraction events
    including step progress, state deltas, tool calls, and reasoning tokens.
    """
    return StreamingResponse(
        _sse_generator(command_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
