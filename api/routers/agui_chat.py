"""AG-UI Chat Endpoint — Unified agent via AG-UI protocol for CopilotKit.

Uses the standard add_langgraph_fastapi_endpoint for proper AG-UI protocol
handling. Source_id extraction happens inside the unified agent graph itself
(via _resolve_source_id in unified_agent.py).
"""

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from fastapi import APIRouter
from loguru import logger

router = APIRouter()


def register_agui_endpoints(app) -> None:
    """Register the unified AG-UI chat endpoint on the FastAPI app.

    Uses the standard add_langgraph_fastapi_endpoint which handles:
    - RunAgentInput parsing (with proper camelCase alias handling)
    - AG-UI SSE event streaming
    - Tool call events, text streaming, state snapshots
    - Thread persistence via the graph's checkpointer

    Source_id extraction and tool context scoping happen inside the
    unified agent graph's call_unified_agent node.
    """
    try:
        from open_notebook.graphs.unified_agent import get_unified_graph

        graph = get_unified_graph()

        try:
            from copilotkit import LangGraphAGUIAgent

            agent = LangGraphAGUIAgent(
                name="acm_agent",
                graph=graph,
                description="ACM-AI unified agent for queries and record modification",
            )
            logger.info("Using LangGraphAGUIAgent (CopilotKit SDK)")
        except ImportError:
            from ag_ui_langgraph import LangGraphAgent

            agent = LangGraphAgent(
                name="acm_agent",
                graph=graph,
                description="ACM-AI unified agent for queries and record modification",
            )
            logger.info("Using LangGraphAgent (ag-ui-langgraph)")

        add_langgraph_fastapi_endpoint(
            app,
            agent,
            "/api/agui/chat",
        )
        logger.info("AG-UI unified chat endpoint registered at /api/agui/chat")
    except Exception as e:
        logger.error(f"Failed to register unified AG-UI endpoint: {e}")
        logger.warning(
            "AG-UI chat will not be available. Falling back to existing chat endpoints."
        )


def register_crud_agui_endpoint(app) -> None:
    """No-op — CRUD functionality is now handled by the unified endpoint."""
    logger.info(
        "register_crud_agui_endpoint called but is now a no-op. "
        "CRUD is handled by the unified /api/agui/chat endpoint."
    )
