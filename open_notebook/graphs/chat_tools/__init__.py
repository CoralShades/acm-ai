"""Chat tools for LangGraph agent tool-use.

This package provides LangChain tools that specialized agents can use
to query structured ACM data and search document content.
"""

from typing import List, Optional

from langchain_core.tools import BaseTool

from open_notebook.graphs.chat_tools.acm_tools import (
    get_acm_record_detail,
    get_acm_stats,
    search_acm_by_building,
    search_acm_by_material,
    search_acm_by_risk,
    search_acm_by_room,
    semantic_search_acm,
)
from open_notebook.graphs.chat_tools.search_tools import (
    search_documents,
    text_search_documents,
)


def get_acm_tools(
    source_id: Optional[str] = None,
    notebook_id: Optional[str] = None,
) -> List[BaseTool]:
    """Get all ACM-related tools, scoped to a source or notebook.

    When source_id is provided, tools query within that single source.
    When notebook_id is provided, tools query across all sources in the notebook.
    """
    # Bind the scope parameters into each tool via partial
    from functools import partial

    scope = {"source_id": source_id, "notebook_id": notebook_id}

    return [
        search_acm_by_risk,
        search_acm_by_building,
        search_acm_by_room,
        search_acm_by_material,
        get_acm_stats,
        get_acm_record_detail,
        semantic_search_acm,
    ]


def get_search_tools() -> List[BaseTool]:
    """Get document search tools (vector + text search)."""
    return [
        search_documents,
        text_search_documents,
    ]


def get_all_chat_tools(
    source_id: Optional[str] = None,
    notebook_id: Optional[str] = None,
) -> List[BaseTool]:
    """Get all chat tools (ACM + document search)."""
    return get_acm_tools(source_id, notebook_id) + get_search_tools()
