"""Shared checkpointer for the unified agent graph.

Uses SqliteSaver for durable session persistence across restarts.
The checkpoint DB lives in data/sqlite-db/ alongside the legacy checkpoints.
"""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE

# Separate file for unified chat to avoid conflicts with legacy graphs
_UNIFIED_CHECKPOINT_FILE = LANGGRAPH_CHECKPOINT_FILE.replace(
    "checkpoints.sqlite", "unified_chat_checkpoints.sqlite"
)

_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    """Get or create the shared SqliteSaver checkpointer.

    Uses a singleton pattern to avoid opening multiple connections.
    check_same_thread=False is required for async LangGraph usage.
    """
    global _checkpointer
    if _checkpointer is None:
        conn = sqlite3.connect(_UNIFIED_CHECKPOINT_FILE, check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
    return _checkpointer
