"""Unified chat session management endpoints.

Provides CRUD for chat sessions tied to sources (jobs), integrated with
the unified LangGraph agent's SqliteSaver checkpointer.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import ChatSession

router = APIRouter(prefix="/api/sources", tags=["unified-sessions"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


@router.get("/{source_id}/unified-sessions", response_model=SessionListResponse)
async def list_sessions(source_id: str):
    """List all unified chat sessions for a source/job."""
    try:
        sid = ensure_record_id(source_id)
        rows = await repo_query(
            "SELECT <-refers_to<-chat_session.* as sessions FROM $sid",
            {"sid": sid},
        )

        sessions = []
        if rows and isinstance(rows, list) and rows[0]:
            raw_sessions = rows[0].get("sessions", [])
            if isinstance(raw_sessions, list):
                # Flatten nested lists
                flat = []
                for item in raw_sessions:
                    if isinstance(item, list):
                        flat.extend(item)
                    elif isinstance(item, dict):
                        flat.append(item)
                for s in flat:
                    if isinstance(s, dict):
                        sessions.append(
                            SessionResponse(
                                id=str(s.get("id", "")),
                                title=s.get("title"),
                                created=str(s.get("created", ""))
                                if s.get("created")
                                else None,
                                updated=str(s.get("updated", ""))
                                if s.get("updated")
                                else None,
                            )
                        )

        return SessionListResponse(sessions=sessions, total=len(sessions))
    except Exception as e:
        logger.error(f"Failed to list sessions for {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/unified-sessions", response_model=SessionResponse)
async def create_session(source_id: str, body: CreateSessionRequest):
    """Create a new unified chat session for a source/job."""
    try:
        session = ChatSession(
            title=body.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )
        await session.save()

        if not session.id:
            raise HTTPException(status_code=500, detail="Failed to save session")

        await session.relate_to_source(source_id)

        return SessionResponse(
            id=str(session.id),
            title=session.title,
            created=str(session.created) if hasattr(session, "created") else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session for {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{source_id}/unified-sessions/{session_id}", response_model=SessionResponse
)
async def update_session(source_id: str, session_id: str, body: UpdateSessionRequest):
    """Update a session's title."""
    try:
        sid = ensure_record_id(session_id)
        if body.title is not None:
            await repo_query(
                "UPDATE $sid SET title = $title",
                {"sid": sid, "title": body.title},
            )

        rows = await repo_query("SELECT * FROM $sid", {"sid": sid})
        if not rows:
            raise HTTPException(status_code=404, detail="Session not found")

        s = rows[0]
        return SessionResponse(
            id=str(s.get("id", "")),
            title=s.get("title"),
            updated=str(s.get("updated", "")) if s.get("updated") else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}/unified-sessions/{session_id}")
async def delete_session(source_id: str, session_id: str):
    """Delete a session and its relations."""
    try:
        sid = ensure_record_id(session_id)

        # Delete the refers_to relation
        await repo_query(
            "DELETE refers_to WHERE in = $sid",
            {"sid": sid},
        )

        # Delete the session itself
        await repo_query("DELETE $sid", {"sid": sid})

        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
