"""AG-UI Chat Endpoint - Exposes the supervisor agent via AG-UI protocol.

Uses the ag-ui-langgraph adapter to expose the LangGraph supervisor agent
as an AG-UI compatible SSE endpoint. This endpoint is consumed by the
CopilotKit frontend.
"""

import json
import re

from ag_ui.core import RunAgentInput
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import APIRouter, Request
from loguru import logger
from starlette.responses import StreamingResponse

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


def register_crud_agui_endpoint(app) -> None:
    """Register a custom CRUD agent AG-UI endpoint with source_id injection.

    The standard `add_langgraph_fastapi_endpoint` doesn't propagate
    `useCopilotReadable` context into LangGraph state. This custom endpoint
    intercepts the request, extracts source_id from CopilotKit's context
    array, and injects it into the AG-UI state before delegating to
    `LangGraphAgent.run()`.
    """
    try:
        from open_notebook.graphs.crud_agent import crud_graph

        crud_agent = LangGraphAgent(
            name="crud_agent",
            graph=crud_graph,
            description="ACM-AI CRUD agent for job-scoped record modification",
        )

        @app.post("/api/agui/crud-chat")
        async def crud_chat_endpoint(request: Request):
            body = await request.body()
            input_data = RunAgentInput.model_validate_json(body)

            # --- Extract source_id from multiple fallback locations ---
            source_id = None

            # 1. From AG-UI state (useCoAgent initialState)
            if input_data.state and isinstance(input_data.state, dict):
                source_id = input_data.state.get("source_id")

            # 2. From CopilotKit context (useCopilotReadable)
            if not source_id and input_data.context:
                for ctx in input_data.context:
                    val = ctx.value if hasattr(ctx, "value") else None
                    if not val:
                        continue
                    # value is a JSON string from useCopilotReadable
                    if isinstance(val, str):
                        try:
                            parsed = json.loads(val)
                            if isinstance(parsed, dict) and parsed.get("source_id"):
                                source_id = parsed["source_id"]
                                break
                        except (json.JSONDecodeError, TypeError):
                            pass
                        # Fallback: raw string containing source:xxx
                        match = re.search(r"(source:[a-z0-9]+)", val)
                        if match:
                            source_id = match.group(1)
                            break

            # 3. From messages (makeSystemMessage content)
            if not source_id and input_data.messages:
                for msg in input_data.messages:
                    content = getattr(msg, "content", "")
                    if isinstance(content, str) and "source:" in content:
                        match = re.search(r"(source:[a-z0-9]+)", content)
                        if match:
                            source_id = match.group(1)
                            break

            # Inject source_id into state so LangGraph receives it
            if source_id:
                state = dict(input_data.state) if input_data.state else {}
                state["source_id"] = source_id
                input_data = input_data.model_copy(update={"state": state})
                logger.info(f"CRUD endpoint injected source_id={source_id}")
            else:
                logger.warning("CRUD endpoint: no source_id found in state, context, or messages")

            return StreamingResponse(
                crud_agent.run(input_data),
                media_type="text/event-stream",
            )

        logger.info("AG-UI CRUD chat endpoint registered at /api/agui/crud-chat (custom)")
    except Exception as e:
        logger.error(f"Failed to register CRUD AG-UI endpoint: {e}")
