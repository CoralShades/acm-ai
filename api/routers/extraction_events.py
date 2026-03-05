"""SSE streaming endpoint for real-time extraction progress.

Streams PipelineRunState updates from the extraction_progress table
to the frontend via Server-Sent Events (SSE).
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from open_notebook.database.repository import db_connection, repo_query

router = APIRouter()

# SSE config
_POLL_INTERVAL_S = 1.0
_HEARTBEAT_INTERVAL_S = 15.0
_TERMINAL_STATUSES = {"completed", "failed", "partial"}


async def _get_progress(command_id: str) -> Optional[dict]:
    """Fetch extraction progress from SurrealDB."""
    try:
        async with db_connection() as db:
            result = await db.query(
                "SELECT * FROM extraction_progress WHERE command_id = $cid LIMIT 1;",
                {"cid": command_id},
            )
            # SurrealDB returns [[...]] for query results
            if result and isinstance(result, list):
                rows = result[0] if isinstance(result[0], list) else result
                if rows and isinstance(rows, list) and len(rows) > 0:
                    return rows[0]
                # Handle {"result": [...]} wrapper
                if isinstance(rows, dict) and "result" in rows:
                    inner = rows["result"]
                    if inner and len(inner) > 0:
                        return inner[0]
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch extraction progress: {e}")
        return None


_MAX_EMPTY_POLLS = 10  # Fail fast after 10s if no DB row found (E35-S5)


async def _sse_generator(command_id: str):
    """Generate SSE events by polling extraction_progress table.

    E35-S5: Pre-flight check — if the job is already in a terminal state on
    first connection, emit the terminal event immediately and close the stream.
    Also fail fast if no DB row is found after _MAX_EMPTY_POLLS ticks.
    """
    last_updated = None
    heartbeat_counter = 0
    polls_per_heartbeat = int(_HEARTBEAT_INTERVAL_S / _POLL_INTERVAL_S)
    empty_poll_count = 0

    while True:
        progress = await _get_progress(command_id)

        if progress:
            empty_poll_count = 0
            current_updated = str(progress.get("updated_at", ""))
            if current_updated != last_updated:
                last_updated = current_updated
                # Build SSE data payload
                data = {
                    "status": progress.get("status", "running"),
                    "state": json.loads(progress["state_json"])
                    if progress.get("state_json")
                    else None,
                    "log_entries": progress.get("log_entries", []),
                }
                yield f"data: {json.dumps(data)}\n\n"

                # Close stream on terminal status
                if progress.get("status") in _TERMINAL_STATUSES:
                    yield f"event: done\ndata: {json.dumps({'status': progress['status']})}\n\n"
                    return
        else:
            empty_poll_count += 1
            if empty_poll_count >= _MAX_EMPTY_POLLS:
                yield (
                    f"event: error\n"
                    f"data: {json.dumps({'status': 'not_found', 'command_id': command_id})}\n\n"
                )
                return

        # Heartbeat to keep connection alive
        if heartbeat_counter >= polls_per_heartbeat:
            yield ": heartbeat\n\n"
            heartbeat_counter = 0

        heartbeat_counter += 1
        await asyncio.sleep(_POLL_INTERVAL_S)


@router.get("/acm/extraction-progress/{command_id}/stream")
async def stream_extraction_progress(command_id: str):
    """SSE endpoint for real-time extraction progress updates.

    Connect with EventSource to receive pipeline state updates
    as the extraction progresses through stages.
    """
    return StreamingResponse(
        _sse_generator(command_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/acm/extraction-progress/{command_id}")
async def get_extraction_progress(command_id: str):
    """REST endpoint to get current extraction progress state.

    Returns the current pipeline state and log entries.
    Used as polling fallback when SSE is unavailable.
    """
    progress = await _get_progress(command_id)
    if not progress:
        raise HTTPException(
            status_code=404, detail="No progress found for this command"
        )

    state = None
    if progress.get("state_json"):
        try:
            state = json.loads(progress["state_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "command_id": command_id,
        "status": progress.get("status", "unknown"),
        "state": state,
        "log_entries": progress.get("log_entries", []),
        "updated_at": progress.get("updated_at"),
    }


@router.get("/acm/extraction-progress")
async def list_extraction_progress(
    status: Optional[str] = Query(
        None, description="Filter by status: running, completed, failed"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all extraction progress records with optional status filter.

    Used by the Extraction Monitor page (E15-S2).
    """
    where_clause = ""
    params: dict = {"limit": limit, "offset": offset}
    if status:
        where_clause = "WHERE status = $status"
        params["status"] = status

    query = (
        f"SELECT * FROM extraction_progress {where_clause} "
        f"ORDER BY updated_at DESC LIMIT $limit START $offset"
    )
    count_query = f"SELECT count() FROM extraction_progress {where_clause} GROUP ALL"
    try:
        results = await repo_query(query, params)
        count_result = await repo_query(
            count_query,
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        )
    except Exception as e:
        logger.error(f"Failed to list extraction progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    total = 0
    if count_result and isinstance(count_result, list) and len(count_result) > 0:
        total = count_result[0].get("count", 0)

    items = []
    for row in results or []:
        state = None
        if row.get("state_json"):
            try:
                state = json.loads(row["state_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        items.append(
            {
                "id": row.get("id"),
                "command_id": row.get("command_id"),
                "source_id": row.get("source_id"),
                "status": row.get("status", "unknown"),
                "state": state,
                "log_entries": row.get("log_entries", []),
                "token_limit_exceeded": row.get("token_limit_exceeded", False),
                "chunk_count": row.get("chunk_count"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
        )

    return {"items": items, "total": total}
