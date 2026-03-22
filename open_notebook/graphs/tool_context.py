"""Unified tool context for all chat tools.

Uses contextvars for thread-safety instead of module-level dicts.
Both acm_tools.py and crud_tools.py delegate to this module.
"""

import contextvars
from typing import Optional, Tuple

_source_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "tool_source_id", default=None
)
_notebook_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "tool_notebook_id", default=None
)


def set_tool_scope(
    source_id: Optional[str] = None,
    notebook_id: Optional[str] = None,
) -> None:
    """Set the scope context for all chat tools.

    Called by the unified agent graph before tool execution.
    Thread-safe via contextvars.
    """
    _source_id_var.set(source_id)
    _notebook_id_var.set(notebook_id)


def get_tool_scope() -> Tuple[Optional[str], Optional[str]]:
    """Get current (source_id, notebook_id) from tool context."""
    return _source_id_var.get(), _notebook_id_var.get()


def get_source_id() -> Optional[str]:
    """Get current source_id from tool context."""
    return _source_id_var.get()


def get_notebook_id() -> Optional[str]:
    """Get current notebook_id from tool context."""
    return _notebook_id_var.get()
