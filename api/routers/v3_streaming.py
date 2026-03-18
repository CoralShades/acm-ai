"""V3 SSE streaming endpoints for real-time pipeline events.

Exposes three Server-Sent Events endpoint categories under /v3/stream/:
  - /extraction/{operation_id}  — forwards extraction.* events
  - /ai/{operation_id}          — forwards ai.* events
  - /bulk/{operation_id}        — forwards bulk.* events

Each endpoint subscribes to the in-memory PipelineEventBus, filters events by
category prefix, serializes them to the SSE named-event format, and emits a
heartbeat comment every 15 seconds to keep TCP connections alive.

Does not replace the existing E27 SSE infrastructure (extraction_events.py,
agui_extraction.py) — both legacy endpoints remain fully operational.

Story: E31-S7 PipelineEventBus + SSE Infrastructure
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from open_notebook.extractors.pipeline_event_bus import (
    V3PipelineEvent,
    get_event_bus,
)

router = APIRouter(prefix="/v3/stream")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HEARTBEAT_INTERVAL_S: float = 15.0

_TERMINAL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "extraction.consensus_complete",
        "ai.validation_complete",
        "bulk.complete",
        "hitl.schema_mapping_resumed",
    }
)

_SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


# ---------------------------------------------------------------------------
# SSE serialisation helpers
# ---------------------------------------------------------------------------


def _format_sse_event(event: V3PipelineEvent) -> str:
    """Serialise a V3PipelineEvent to SSE named-event wire format.

    Format::

        event: <type>\\n
        data: <json>\\n
        \\n
    """
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


def _format_sse_done(operation_id: str, final_type: str) -> str:
    """Serialise the terminal done sentinel to SSE wire format."""
    payload = json.dumps({"operation_id": operation_id, "final_type": final_type})
    return f"event: done\ndata: {payload}\n\n"


def _format_sse_error(operation_id: str, message: str) -> str:
    """Serialise an error event to SSE wire format."""
    payload = json.dumps({"message": message, "operation_id": operation_id})
    return f"event: error\ndata: {payload}\n\n"


_HEARTBEAT_COMMENT = ": heartbeat\n\n"


# ---------------------------------------------------------------------------
# Core SSE generator
# ---------------------------------------------------------------------------


async def _sse_generator(
    operation_id: str,
    category_prefix: str,
) -> AsyncGenerator[str, None]:
    """Generate SSE text chunks for one category of V3 events.

    Subscribes to the PipelineEventBus for *operation_id*, forwards only
    events whose ``type`` starts with *category_prefix*, emits heartbeat
    comments every 15 s, and terminates the stream on terminal events or error.

    Args:
        operation_id: The operation to subscribe to.
        category_prefix: Event type prefix to forward (e.g. ``"extraction."``).
    """
    bus = get_event_bus()
    heartbeat_task: Optional[asyncio.Task[None]] = None

    async def _heartbeat_loop(queue: asyncio.Queue[Optional[str]]) -> None:
        """Put heartbeat sentinels into the render queue every 15 s."""
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL_S)
            await queue.put(None)  # None sentinel → heartbeat

    # We need interleaved heartbeats and events.  Use a local render queue so
    # the heartbeat task and the event subscriber can both produce output.
    render_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

    async def _forward_events() -> None:
        """Subscribe to bus and push formatted SSE strings into render_queue."""
        try:
            async for event in bus.subscribe(operation_id, timeout_seconds=300.0):
                if not event.type.startswith(category_prefix):
                    continue  # filter out other categories
                await render_queue.put(_format_sse_event(event))
                if event.type in _TERMINAL_EVENT_TYPES:
                    await render_queue.put(_format_sse_done(operation_id, event.type))
                    await render_queue.put("__DONE__")
                    return
        except asyncio.TimeoutError:
            await render_queue.put(
                _format_sse_error(
                    operation_id,
                    f"Event bus subscription timed out after 300s",
                )
            )
            await render_queue.put("__DONE__")
        except Exception as exc:
            logger.exception(
                f"[V3Stream] Unexpected error in event forwarder for {operation_id}: {exc}"
            )
            await render_queue.put(_format_sse_error(operation_id, str(exc)))
            await render_queue.put("__DONE__")

    forward_task = asyncio.create_task(_forward_events())
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(render_queue)  # type: ignore[arg-type]
    )

    try:
        while True:
            item = await render_queue.get()
            if item is None:
                # Heartbeat sentinel
                yield _HEARTBEAT_COMMENT
            elif item == "__DONE__":
                break
            else:
                yield item
    except GeneratorExit:
        logger.debug(f"[V3Stream] Client disconnected for operation {operation_id}")
    finally:
        forward_task.cancel()
        heartbeat_task.cancel()
        # Suppress CancelledError from the cancelled tasks
        for task in (forward_task, heartbeat_task):
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass


# ---------------------------------------------------------------------------
# Endpoint helpers
# ---------------------------------------------------------------------------


def _validate_operation_id(
    path_id: str,
    query_id: Optional[str],
) -> None:
    """Raise HTTP 400 if query param operation_id doesn't match path param."""
    if query_id is not None and query_id != path_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Query param operation_id '{query_id}' does not match "
                f"path param '{path_id}'."
            ),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/extraction/{operation_id}")
async def stream_extraction(
    operation_id: str,
    operation_id_query: Optional[str] = Query(
        None,
        alias="operation_id",
        description="Optional assertion that must match the path parameter.",
    ),
) -> StreamingResponse:
    """SSE stream for extraction.* pipeline events.

    Forwards ``extraction.started``, ``extraction.provider_complete``, and
    ``extraction.consensus_complete`` events for the given operation.

    The stream terminates automatically on ``extraction.consensus_complete``.
    """
    _validate_operation_id(operation_id, operation_id_query)
    logger.info(f"[V3Stream] /extraction SSE opened for operation {operation_id}")
    return StreamingResponse(
        _sse_generator(operation_id, "extraction."),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/ai/{operation_id}")
async def stream_ai(
    operation_id: str,
    operation_id_query: Optional[str] = Query(
        None,
        alias="operation_id",
        description="Optional assertion that must match the path parameter.",
    ),
) -> StreamingResponse:
    """SSE stream for ai.* pipeline events.

    Forwards ``ai.building_extracted``, ``ai.items_extracted``, and
    ``ai.validation_complete`` events for the given operation.

    The stream terminates automatically on ``ai.validation_complete``.
    """
    _validate_operation_id(operation_id, operation_id_query)
    logger.info(f"[V3Stream] /ai SSE opened for operation {operation_id}")
    return StreamingResponse(
        _sse_generator(operation_id, "ai."),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/hitl/{operation_id}")
async def stream_hitl(
    operation_id: str,
    operation_id_query: Optional[str] = Query(
        None,
        alias="operation_id",
        description="Optional assertion that must match the path parameter.",
    ),
) -> StreamingResponse:
    """SSE stream for hitl.* pipeline events.

    Forwards ``hitl.schema_mapping_review`` and ``hitl.schema_mapping_resumed``
    events for the given operation.

    The stream terminates automatically on ``hitl.schema_mapping_resumed``.
    """
    _validate_operation_id(operation_id, operation_id_query)
    logger.info(f"[V3Stream] /hitl SSE opened for operation {operation_id}")
    return StreamingResponse(
        _sse_generator(operation_id, "hitl."),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/bulk/{operation_id}")
async def stream_bulk(
    operation_id: str,
    operation_id_query: Optional[str] = Query(
        None,
        alias="operation_id",
        description="Optional assertion that must match the path parameter.",
    ),
) -> StreamingResponse:
    """SSE stream for bulk.* pipeline events.

    Forwards ``bulk.progress`` and ``bulk.complete`` events for the given
    operation.

    The stream terminates automatically on ``bulk.complete``.
    """
    _validate_operation_id(operation_id, operation_id_query)
    logger.info(f"[V3Stream] /bulk SSE opened for operation {operation_id}")
    return StreamingResponse(
        _sse_generator(operation_id, "bulk."),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
