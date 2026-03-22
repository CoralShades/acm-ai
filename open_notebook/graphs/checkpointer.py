"""Shared checkpointer for the unified agent graph.

Uses AsyncSqliteSaver for durable persistence — conversations survive
server restarts. The checkpointer is initialized during FastAPI lifespan
startup and closed during shutdown.

DB path: data/chat_checkpoints.db (configurable via CHAT_CHECKPOINT_DB env var)
"""

import os

from loguru import logger

_checkpointer = None
_checkpointer_cm = None


async def init_checkpointer():
    """Initialize the AsyncSqliteSaver checkpointer.

    Must be called once during app startup (inside FastAPI lifespan).
    Creates the SQLite DB file and tables if they don't exist.
    """
    global _checkpointer, _checkpointer_cm

    db_path = os.environ.get("CHAT_CHECKPOINT_DB", "data/chat_checkpoints.db")

    # Ensure the directory exists
    db_dir = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(db_dir, exist_ok=True)

    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        cm = AsyncSqliteSaver.from_conn_string(db_path)
        saver = await cm.__aenter__()
        await saver.setup()
        _checkpointer = saver
        _checkpointer_cm = cm
        logger.info(f"Chat checkpointer initialized: AsyncSqliteSaver at {db_path}")
    except Exception as e:
        logger.warning(
            f"AsyncSqliteSaver failed ({e}), falling back to MemorySaver. "
            "Chat history will not persist across restarts."
        )
        from langgraph.checkpoint.memory import MemorySaver

        _checkpointer = MemorySaver()


async def close_checkpointer():
    """Close the checkpointer. Call during app shutdown."""
    global _checkpointer, _checkpointer_cm

    if _checkpointer_cm is not None:
        try:
            await _checkpointer_cm.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing checkpointer: {e}")
    _checkpointer = None
    _checkpointer_cm = None
    logger.info("Chat checkpointer closed")


def get_checkpointer():
    """Get the initialized checkpointer.

    Falls back to MemorySaver if init_checkpointer() wasn't called
    (e.g., in tests or LangGraph Studio).
    """
    global _checkpointer

    if _checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver

        logger.debug(
            "Checkpointer not initialized, using MemorySaver fallback. "
            "Call init_checkpointer() during app startup for durable persistence."
        )
        _checkpointer = MemorySaver()

    return _checkpointer
