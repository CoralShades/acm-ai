"""Shared checkpointer for the unified agent graph.

Uses MemorySaver for in-process persistence. Conversations persist within
a server session but are lost on restart. For durable persistence, a future
upgrade to PostgresSaver or a properly initialized AsyncSqliteSaver is needed.
"""

from langgraph.checkpoint.memory import MemorySaver

_checkpointer: MemorySaver | None = None


def get_checkpointer() -> MemorySaver:
    """Get or create the shared MemorySaver checkpointer.

    MemorySaver works with both sync and async graph execution,
    making it compatible with add_langgraph_fastapi_endpoint (async)
    and direct invoke (sync).
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer
