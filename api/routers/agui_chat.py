"""AG-UI Chat Endpoint - Exposes the supervisor agent via AG-UI protocol.

Uses the ag-ui-langgraph adapter to expose the LangGraph supervisor agent
as an AG-UI compatible SSE endpoint. This endpoint is consumed by the
CopilotKit frontend.
"""

import json
import re

from ag_ui.core import (
    EventType,
    MessagesSnapshotEvent,
    RunAgentInput,
    RunErrorEvent,
    StateSnapshotEvent,
)
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from ag_ui_langgraph.utils import langchain_messages_to_agui, make_json_safe
from fastapi import APIRouter, Request
from langchain_core.messages import BaseMessage
from loguru import logger
from starlette.responses import StreamingResponse

from open_notebook.graphs.supervisor_agent import supervisor_graph

router = APIRouter()


def _sanitize_state_snapshot(event: StateSnapshotEvent) -> StateSnapshotEvent:
    """Convert any LangChain BaseMessage objects in a StateSnapshotEvent snapshot
    to AG-UI message dicts so pydantic can serialize them.

    execute_write_node (and other non-LLM graph nodes) return AIMessage objects
    directly into the state. The AG-UI EventEncoder calls model_dump_json() on
    the StateSnapshotEvent, which fails when the snapshot dict contains raw
    langchain BaseMessage instances.  This wrapper converts them first.
    """
    snapshot = event.snapshot
    if not isinstance(snapshot, dict):
        return event

    messages = snapshot.get("messages")
    if not messages:
        return event

    langchain_msgs = [m for m in messages if isinstance(m, BaseMessage)]
    if not langchain_msgs:
        return event

    try:
        agui_msgs = langchain_messages_to_agui(langchain_msgs)
        # Rebuild snapshot with serializable message dicts
        safe_msgs = [
            m.model_dump(by_alias=True, exclude_none=True) for m in agui_msgs
        ]
        non_lc_msgs = [m for m in messages if not isinstance(m, BaseMessage)]
        sanitized_snapshot = {
            **make_json_safe({k: v for k, v in snapshot.items() if k != "messages"}),
            "messages": non_lc_msgs + safe_msgs,
        }
        return event.model_copy(update={"snapshot": sanitized_snapshot})
    except Exception as exc:  # pragma: no cover
        logger.warning(
            f"agui_chat: could not sanitize StateSnapshotEvent messages: {exc}"
        )
        # Fallback: drop messages from snapshot rather than crash the stream
        fallback_snapshot = make_json_safe(
            {k: v for k, v in snapshot.items() if k != "messages"}
        )
        return event.model_copy(update={"snapshot": fallback_snapshot})


def _sanitize_messages_snapshot(
    event: MessagesSnapshotEvent,
) -> MessagesSnapshotEvent:
    """Re-convert any raw LangChain BaseMessage objects that leaked into a
    MessagesSnapshotEvent.

    The ag-ui-langgraph adapter calls langchain_messages_to_agui() internally
    before constructing the event, but if that call raises (e.g. unsupported
    message type) the exception kills the SSE stream.  This wrapper provides
    a second chance: it inspects the event's messages list, converts any stray
    BaseMessage objects, and returns a safe event.
    """
    msgs = event.messages
    if not msgs:
        return event

    has_raw = any(isinstance(m, BaseMessage) for m in msgs)
    if not has_raw:
        return event

    try:
        langchain_msgs = [m for m in msgs if isinstance(m, BaseMessage)]
        agui_msgs = langchain_messages_to_agui(langchain_msgs)
        non_lc = [m for m in msgs if not isinstance(m, BaseMessage)]
        return event.model_copy(update={"messages": non_lc + agui_msgs})
    except Exception as exc:
        logger.warning(
            f"agui_chat: could not sanitize MessagesSnapshotEvent: {exc}"
        )
        non_lc = [m for m in msgs if not isinstance(m, BaseMessage)]
        return event.model_copy(update={"messages": non_lc})


def _safe_encode(encoder: EventEncoder, event) -> str:
    """Encode an AG-UI event to SSE, falling back to make_json_safe on failure.

    model_dump_json() can raise PydanticSerializationError when the event
    contains Python objects (e.g. LangChain BaseMessage) that Pydantic's
    JSON serializer cannot handle.  This wrapper catches such errors and
    retries with a fully-sanitized copy of the event.
    """
    try:
        return encoder.encode(event)
    except Exception as first_err:
        logger.warning(
            f"agui_chat: encoder.encode failed ({type(first_err).__name__}: "
            f"{first_err}), retrying with make_json_safe"
        )
        try:
            safe_data = make_json_safe(
                event.model_dump(by_alias=True, exclude_none=True)
            )
            return f"data: {json.dumps(safe_data)}\n\n"
        except Exception as second_err:
            logger.error(
                f"agui_chat: fallback encode also failed: {second_err}"
            )
            error_payload = {
                "type": "error",
                "message": f"Event encoding error: {first_err}",
            }
            return f"data: {json.dumps(error_payload)}\n\n"


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
            # Also set thread_id for session persistence (per-source conversation)
            if source_id:
                state = dict(input_data.state) if input_data.state else {}
                state["source_id"] = source_id
                thread_id = f"crud_{source_id.replace(':', '_')}"
                input_data = input_data.model_copy(
                    update={
                        "state": state,
                        "thread_id": thread_id,
                    }
                )
                logger.info(
                    f"CRUD endpoint injected source_id={source_id}, thread_id={thread_id}"
                )
            else:
                logger.warning(
                    "CRUD endpoint: no source_id found in state, context, or messages"
                )

            # Set recursion limit high enough for multi-step tool chains
            if not input_data.config:
                input_data = input_data.model_copy(
                    update={"config": {"recursion_limit": 50}}
                )
            elif isinstance(input_data.config, dict):
                input_data.config.setdefault("recursion_limit", 50)

            accept_header = request.headers.get("accept")
            encoder = EventEncoder(accept=accept_header)

            async def event_generator():
                try:
                    async for event in crud_agent.run(input_data):
                        # Sanitize StateSnapshotEvents: execute_write_node
                        # emits AIMessage objects into state.  The encoder
                        # calls model_dump_json() on the snapshot, which
                        # crashes on raw langchain BaseMessage instances.
                        if (
                            hasattr(event, "type")
                            and event.type == EventType.STATE_SNAPSHOT
                            and isinstance(event, StateSnapshotEvent)
                        ):
                            event = _sanitize_state_snapshot(event)
                        elif (
                            hasattr(event, "type")
                            and event.type == EventType.MESSAGES_SNAPSHOT
                            and isinstance(event, MessagesSnapshotEvent)
                        ):
                            event = _sanitize_messages_snapshot(event)

                        yield _safe_encode(encoder, event)
                except Exception as exc:
                    err_msg = str(exc)
                    # Stale thread recovery: if the thread state is corrupted
                    # (e.g., from a previous recursion error), retry without
                    # thread_id to start a fresh conversation.
                    if "Message ID not found" in err_msg or "not found in history" in err_msg:
                        logger.warning(
                            f"agui_chat: CRUD stale thread detected, retrying without thread_id"
                        )
                        try:
                            fresh_input = input_data.model_copy(
                                update={"thread_id": None}
                            )
                            async for event in crud_agent.run(fresh_input):
                                if (
                                    hasattr(event, "type")
                                    and event.type == EventType.STATE_SNAPSHOT
                                    and isinstance(event, StateSnapshotEvent)
                                ):
                                    event = _sanitize_state_snapshot(event)
                                elif (
                                    hasattr(event, "type")
                                    and event.type == EventType.MESSAGES_SNAPSHOT
                                    and isinstance(event, MessagesSnapshotEvent)
                                ):
                                    event = _sanitize_messages_snapshot(event)
                                yield _safe_encode(encoder, event)
                            return  # Success on retry
                        except Exception as retry_exc:
                            logger.error(
                                f"agui_chat: CRUD retry also failed: {retry_exc}"
                            )
                            err_msg = str(retry_exc)

                    # BUG-4 defense: emit a clean error event instead of killing the SSE stream.
                    logger.error(
                        f"agui_chat: CRUD event stream error: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    try:
                        err_event = RunErrorEvent(
                            type=EventType.RUN_ERROR,
                            message=f"Stream error: {exc}",
                        )
                        yield encoder.encode(err_event)
                    except Exception:
                        yield f'data: {{"type":"error","message":"Internal stream error"}}\n\n'

            return StreamingResponse(
                event_generator(),
                media_type=encoder.get_content_type(),
            )

        logger.info(
            "AG-UI CRUD chat endpoint registered at /api/agui/crud-chat (custom)"
        )
    except Exception as e:
        logger.error(f"Failed to register CRUD AG-UI endpoint: {e}")
