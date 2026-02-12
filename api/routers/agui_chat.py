"""AG-UI Chat Endpoint - Exposes the supervisor agent via AG-UI protocol.

Uses the ag-ui-langgraph adapter to expose the LangGraph supervisor agent
as an AG-UI compatible SSE endpoint. This endpoint is consumed by the
CopilotKit frontend.
"""

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import APIRouter
from loguru import logger

from open_notebook.graphs.supervisor_agent import supervisor_graph

router = APIRouter()

# Add the AG-UI endpoint to this router's underlying FastAPI app
# This will be done in main.py after the app is created, since
# add_langgraph_fastapi_endpoint needs the app instance.
# See register_agui_endpoints() below.


def register_agui_endpoints(app):
    """Register AG-UI endpoints on the FastAPI app.

    Called from api/main.py after the app is created.
    This adds the AG-UI protocol endpoint that handles:
    - RunAgentInput → AG-UI SSE event stream
    - Automatic LangGraph → AG-UI event mapping
    - Tool call events (ToolCallStart, ToolCallArgs, ToolCallEnd, ToolCallResult)
    - Text streaming (TextMessageStart, TextMessageContent, TextMessageEnd)
    - State snapshots/deltas
    """
    try:
        agent = LangGraphAgent(
            name="supervisor",
            graph=supervisor_graph,
            description="ACM-AI supervisor agent for asbestos compliance queries",
        )
        add_langgraph_fastapi_endpoint(
            app,
            agent,
            "/api/agui/chat",
        )
        logger.info("AG-UI chat endpoint registered at /api/agui/chat")
    except Exception as e:
        logger.error(f"Failed to register AG-UI endpoint: {e}")
        logger.warning(
            "AG-UI chat will not be available. Falling back to existing chat endpoints."
        )
