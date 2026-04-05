"""Unified chat session management endpoints.

Provides CRUD for chat sessions tied to sources (jobs), integrated with
the unified LangGraph agent's SqliteSaver checkpointer.
"""

import uuid as _uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from langchain_core.messages import messages_to_dict
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import ChatSession
from open_notebook.graphs.checkpointer import get_checkpointer

router = APIRouter(prefix="/api/sources", tags=["unified-sessions"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    thread_id: Optional[str] = None  # Option B: store CopilotKit's thread_id back


class SessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    thread_id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    role: str
    content: Any  # str or list[dict] for multi-part content
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None


class MessageHistoryResponse(BaseModel):
    messages: list[MessageResponse]
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
                                thread_id=s.get("thread_id"),
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
        thread_id = str(_uuid.uuid4())
        session = ChatSession(
            title=body.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            thread_id=thread_id,
        )
        await session.save()

        if not session.id:
            raise HTTPException(status_code=500, detail="Failed to save session")

        await session.relate_to_source(source_id)

        return SessionResponse(
            id=str(session.id),
            title=session.title,
            thread_id=session.thread_id,
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
    """Update a session's title and/or thread_id."""
    try:
        sid = ensure_record_id(session_id)
        if body.title is not None:
            await repo_query(
                "UPDATE $sid SET title = $title",
                {"sid": sid, "title": body.title},
            )
        if body.thread_id is not None:
            await repo_query(
                "UPDATE $sid SET thread_id = $thread_id",
                {"sid": sid, "thread_id": body.thread_id},
            )

        rows = await repo_query("SELECT * FROM $sid", {"sid": sid})
        if not rows:
            raise HTTPException(status_code=404, detail="Session not found")

        s = rows[0]
        return SessionResponse(
            id=str(s.get("id", "")),
            title=s.get("title"),
            thread_id=s.get("thread_id"),
            updated=str(s.get("updated", "")) if s.get("updated") else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{source_id}/unified-sessions/{session_id}/messages",
    response_model=MessageHistoryResponse,
)
async def get_session_messages(source_id: str, session_id: str):
    """Return the message history for a chat session from the LangGraph checkpointer.

    Reads the latest checkpoint for the session's thread_id from AsyncSqliteSaver
    (or MemorySaver fallback). Returns an empty list when no checkpoint exists.
    """
    try:
        sid = ensure_record_id(session_id)
        rows = await repo_query("SELECT thread_id FROM $sid", {"sid": sid})
        if not rows or not rows[0]:
            raise HTTPException(status_code=404, detail="Session not found")

        thread_id: Optional[str] = rows[0].get("thread_id")
        if not thread_id:
            # Session exists but has no thread_id yet (never used in a conversation)
            return MessageHistoryResponse(messages=[], total=0)

        checkpointer = get_checkpointer()
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await checkpointer.aget_tuple(config)

        if not checkpoint_tuple or not checkpoint_tuple.checkpoint:
            return MessageHistoryResponse(messages=[], total=0)

        raw_messages = (
            checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
        )

        if not raw_messages:
            return MessageHistoryResponse(messages=[], total=0)

        serialized = messages_to_dict(raw_messages)

        messages: list[MessageResponse] = []
        for msg in serialized:
            msg_data = msg.get("data", {})
            role = msg.get("type", "unknown")
            # LangChain type names map to role names used by the frontend
            role_map = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
                "tool": "tool",
                "function": "function",
            }
            role = role_map.get(role, role)

            content = msg_data.get("content", "")
            tool_calls = msg_data.get("tool_calls") or None
            tool_call_id = msg_data.get("tool_call_id") or None
            name = msg_data.get("name") or None

            messages.append(
                MessageResponse(
                    role=role,
                    content=content,
                    name=name,
                    tool_calls=tool_calls,
                    tool_call_id=tool_call_id,
                )
            )

        return MessageHistoryResponse(messages=messages, total=len(messages))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load messages for session {session_id}: {e}")
        # Graceful degradation: history load failure should not break the UI
        return MessageHistoryResponse(messages=[], total=0)


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
