"""LangGraph Studio entrypoint for Supervisor graph.

Studio provides its own persistence, so we compile without a checkpointer here.
The production graph in supervisor_agent.py uses MemorySaver for runtime use.
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

from open_notebook.graphs.supervisor_agent import (
    END,
    START,
    StateGraph,
    SupervisorState,
    ToolNode,
    _get_supervisor_tools,
    call_supervisor,
    should_continue,
)

# Rebuild graph without checkpointer for Studio compatibility
_tools = _get_supervisor_tools(include_acm=True)
_tool_node = ToolNode(_tools)

_graph_builder = StateGraph(SupervisorState)
_graph_builder.add_node("supervisor", call_supervisor)
_graph_builder.add_node("tools", _tool_node)
_graph_builder.add_edge(START, "supervisor")
_graph_builder.add_conditional_edges(
    "supervisor", should_continue, {"tools": "tools", END: END}
)
_graph_builder.add_edge("tools", "supervisor")

graph = _graph_builder.compile()
