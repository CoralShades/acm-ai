"""LangGraph Studio entrypoint for Unified Agent graph.

Studio provides its own persistence, so we compile without a checkpointer here.
The production graph in unified_agent.py uses SqliteSaver for runtime use.
"""

import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=False)

required = [
    "SURREAL_URL",
    "SURREAL_USER",
    "SURREAL_PASSWORD",
    "SURREAL_NAMESPACE",
    "SURREAL_DATABASE",
]
missing = [name for name in required if not os.getenv(name)]
if missing:
    logger.warning(
        "LangGraph Studio loaded without full SurrealDB configuration "
        f"(missing: {', '.join(missing)}). "
        "Visualization mode still works; runtime execution may fail without DB."
    )

from open_notebook.graphs.unified_agent import (
    END,
    START,
    StateGraph,
    ToolNode,
    UnifiedAgentState,
    _get_unified_tools,
    approval_node,
    call_unified_agent,
    check_pending_and_route,
    legacy_execute_write_node,
    route_entry,
    should_continue,
)

# Rebuild graph without checkpointer for Studio compatibility
_tools = _get_unified_tools(include_acm=True)
_tool_node = ToolNode(_tools)

_builder = StateGraph(UnifiedAgentState)
_builder.add_node("agent", call_unified_agent)
_builder.add_node("tools", _tool_node)
_builder.add_node("approval", approval_node)
_builder.add_node("legacy_execute", legacy_execute_write_node)
_builder.add_conditional_edges(
    START, route_entry, {"agent": "agent", "legacy_execute": "legacy_execute"}
)
_builder.add_conditional_edges(
    "agent", should_continue, {"tools": "tools", END: END}
)
_builder.add_conditional_edges(
    "tools", check_pending_and_route, {"approval": "approval", "agent": "agent"}
)
_builder.add_edge("approval", "agent")
_builder.add_edge("legacy_execute", END)

graph = _builder.compile()
