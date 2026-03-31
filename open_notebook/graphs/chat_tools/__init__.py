"""Chat tools for LangGraph agent tool-use.

This package provides LangChain tools that specialized agents can use
to query structured ACM data and search document content.
"""

from typing import List, Optional

from langchain_core.tools import BaseTool

from open_notebook.graphs.chat_tools.acm_tools import (
    get_acm_record_detail,
    get_acm_stats,
    get_source_metadata,
    list_acm_buildings,
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
    """Get all ACM-related tools.

    Scope (source_id/notebook_id) is set via contextvars by the graph node
    before tool execution, not via function partials.
    """
    return [
        search_acm_by_risk,
        search_acm_by_building,
        search_acm_by_room,
        search_acm_by_material,
        get_acm_stats,
        get_acm_record_detail,
        list_acm_buildings,
        get_source_metadata,
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
