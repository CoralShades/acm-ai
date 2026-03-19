"""
Job Lifecycle API Endpoints

Provides REST endpoints for managing ACM extraction job lifecycle:
- Cancel a running extraction
- Restart a failed extraction
- Query job status by source_id
- Duplicate guard (can-extract check)

The surreal-commands library stores jobs in the `command` table with fields:
  id, app, name, args (contains source_id), status, created, updated.

Active statuses: 'new', 'running'
Terminal statuses: 'completed', 'failed', 'canceled'
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api.command_service import CommandService
from open_notebook.database.repository import repo_query
from open_notebook.extractors.pipeline_event_bus import V3PipelineEvent, get_event_bus

router = APIRouter()

# ---------------------------------------------------------------------------
# Status constants — mirrors surreal_commands.core.client.CommandStatus
# ---------------------------------------------------------------------------

_ACTIVE_STATUSES = ("new", "running")
_TERMINAL_STATUSES = ("completed", "failed", "canceled")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class JobStatusResponse(BaseModel):
    """Status of the latest command for a source."""

    command_id: str = Field(..., description="SurrealDB record ID of the command")
    status: str = Field(..., description="Command status")
    created_at: Optional[str] = Field(None, description="ISO-8601 creation timestamp")
    updated_at: Optional[str] = Field(None, description="ISO-8601 last-update timestamp")


class CancelResponse(BaseModel):
    cancelled: bool
    command_id: str


class RestartResponse(BaseModel):
    command_id: str
    restarted: bool


class CanExtractResponse(BaseModel):
    can_extract: bool
    reason: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_latest_command_for_source(
    source_id: str,
) -> Optional[dict]:
    """Return the most-recently created command row for *source_id*, or None.

    The `command` table stores extraction args in `args.source_id`.  We
    normalise the source_id to both bare ID and record-prefixed forms so that
    queries work regardless of how the caller passes the identifier.
    """
    # Build both variants: "source:abc123" and "abc123"
    bare_id = source_id.split(":")[-1] if ":" in source_id else source_id
    full_id = f"source:{bare_id}" if not source_id.startswith("source:") else source_id

    result = await repo_query(
        """
        SELECT id, status, created, updated
        FROM command
        WHERE app = 'open_notebook'
          AND name = 'acm_extract'
          AND (args.source_id = $full_id OR args.source_id = $bare_id)
        ORDER BY created DESC
        LIMIT 1;
        """,
        {"full_id": full_id, "bare_id": bare_id},
    )

    if not result:
        return None

    # repo_query may return [[row]] or [row] depending on SurrealDB SDK version
    rows = result[0] if isinstance(result[0], list) else result
    if not rows:
        return None

    row = rows[0] if isinstance(rows, list) else rows
    return row if isinstance(row, dict) else None


async def _get_active_command_for_source(source_id: str) -> Optional[dict]:
    """Return the active (new/running) command row for *source_id*, or None."""
    bare_id = source_id.split(":")[-1] if ":" in source_id else source_id
    full_id = f"source:{bare_id}" if not source_id.startswith("source:") else source_id

    result = await repo_query(
        """
        SELECT id, status, created, updated
        FROM command
        WHERE app = 'open_notebook'
          AND name = 'acm_extract'
          AND (args.source_id = $full_id OR args.source_id = $bare_id)
          AND status IN ['new', 'running']
        ORDER BY created DESC
        LIMIT 1;
        """,
        {"full_id": full_id, "bare_id": bare_id},
    )

    if not result:
        return None

    rows = result[0] if isinstance(result[0], list) else result
    if not rows:
        return None

    row = rows[0] if isinstance(rows, list) else rows
    return row if isinstance(row, dict) else None


def _row_to_status_response(row: dict) -> JobStatusResponse:
    """Convert a raw command table row to a JobStatusResponse."""
    return JobStatusResponse(
        command_id=str(row.get("id", "")),
        status=str(row.get("status", "unknown")),
        created_at=str(row["created"]) if row.get("created") else None,
        updated_at=str(row["updated"]) if row.get("updated") else None,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/jobs/{source_id}/status", response_model=JobStatusResponse)
async def get_job_status(source_id: str) -> JobStatusResponse:
    """Return the latest command status for *source_id*.

    Returns 404 if no extraction commands exist for the source.
    """
    row = await _get_latest_command_for_source(source_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No extraction commands found for source '{source_id}'",
        )
    return _row_to_status_response(row)


@router.get("/jobs/{source_id}/can-extract", response_model=CanExtractResponse)
async def can_extract(source_id: str) -> CanExtractResponse:
    """Duplicate-guard endpoint.

    Returns ``can_extract: true`` when no pending/running commands exist for
    the source, or ``can_extract: false`` with the blocking command ID as the
    reason when one is found.
    """
    active = await _get_active_command_for_source(source_id)
    if active is None:
        return CanExtractResponse(
            can_extract=True,
            reason="No active extraction in progress",
        )
    return CanExtractResponse(
        can_extract=False,
        reason=f"Extraction already in progress (command {active.get('id')})",
    )


@router.post("/jobs/{source_id}/cancel", response_model=CancelResponse)
async def cancel_job(source_id: str) -> CancelResponse:
    """Cancel the active extraction for *source_id*.

    - 404 if no active command is found.
    - 409 if the command is already in a terminal state.
    """
    active = await _get_active_command_for_source(source_id)
    if active is None:
        # Check whether a command exists at all (to distinguish 404 vs 409)
        latest = await _get_latest_command_for_source(source_id)
        if latest is None:
            raise HTTPException(
                status_code=404,
                detail=f"No extraction commands found for source '{source_id}'",
            )
        # A command exists but is already in a terminal state
        raise HTTPException(
            status_code=409,
            detail=(
                f"Command '{latest.get('id')}' is already in terminal state "
                f"'{latest.get('status')}' and cannot be cancelled"
            ),
        )

    command_id = str(active["id"])
    current_status = str(active.get("status", ""))

    # Guard: should not reach here, but be defensive
    if current_status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Command '{command_id}' is already in terminal state '{current_status}'",
        )

    # Mark the command as canceled in the database
    try:
        await repo_query(
            "UPDATE type::thing($cmd_id) SET status = 'canceled';",
            {"cmd_id": command_id},
        )
        logger.info(f"Cancelled command {command_id} for source {source_id}")
    except Exception as exc:
        logger.error(f"Failed to cancel command {command_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel command: {exc}",
        ) from exc

    # Emit a cancel event on the pipeline event bus (non-fatal)
    try:
        bus = get_event_bus()
        cancel_event = V3PipelineEvent(
            type="job.cancelled",
            operation_id=command_id,
            data={"source_id": source_id, "command_id": command_id},
        )
        await bus.publish(cancel_event)
    except Exception as exc:
        logger.warning(f"Failed to emit cancel event for {command_id}: {exc}")

    return CancelResponse(cancelled=True, command_id=command_id)


@router.post("/jobs/{source_id}/restart", response_model=RestartResponse)
async def restart_job(source_id: str) -> RestartResponse:
    """Restart extraction for *source_id*.

    - 409 if an extraction is already in progress (duplicate guard).

    A new extraction command is submitted via the same mechanism used by
    ``POST /api/acm/extract``.
    """
    # Duplicate guard: reject if an active command already exists
    active = await _get_active_command_for_source(source_id)
    if active is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Extraction is already in progress for source '{source_id}' "
                f"(command {active.get('id')}). Cancel it before restarting."
            ),
        )

    # Register acm_commands so the command is available in the surreal-commands registry
    try:
        import commands.acm_commands  # noqa: F401
    except ImportError as exc:
        logger.error(f"Failed to import acm_commands: {exc}")
        raise HTTPException(
            status_code=500,
            detail="ACM command modules are unavailable",
        ) from exc

    # Submit a new extraction command
    try:
        new_command_id = await CommandService.submit_command_job(
            "open_notebook",
            "acm_extract",
            {"source_id": source_id, "force": False},
        )
        logger.info(
            f"Restarted extraction for source {source_id} — new command {new_command_id}"
        )
    except Exception as exc:
        logger.error(f"Failed to restart extraction for {source_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit restart command: {exc}",
        ) from exc

    return RestartResponse(command_id=new_command_id, restarted=True)
