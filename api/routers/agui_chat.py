"""AG-UI Chat Endpoint — Unified agent via AG-UI protocol for CopilotKit.

Creates a fresh LangGraphAgent per request to avoid concurrency issues —
the agent's active_run and messages_in_process are instance variables that
would be corrupted by concurrent requests if shared.

Source_id is bridged from the CopilotKit context array (useCopilotReadable)
into the graph state here, since useCoAgent only serializes messages to state.
"""

import json

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger

router = APIRouter()

# Detect which agent class is available at import time
_AgentClass = None
_agent_class_name = "unknown"


def _make_resume_safe_agent_class(base_class):
    """Wrap an agent class to fix the ag_ui_langgraph message-count bug.

    ag_ui_langgraph's prepare_stream checks whether the graph's stored message
    list is longer than the messages CopilotKit sent in the current request.
    When true it assumes time-travel regeneration is needed and calls
    prepare_regenerate_stream — but this same condition fires on every resume
    request (Approve/Reject HITL), because the graph accumulated tool-call
    messages that CopilotKit does not re-send verbatim.  The result: the
    approve click silently re-runs the whole turn instead of resuming from
    the interrupt checkpoint.

    Fix: skip the regenerate path whenever forwarded_props.command.resume is
    set.  We do this by subclassing and delegating to a patched prepare_stream
    that performs the resume_input check first.
    """

    class ResumeSafeLangGraphAgent(base_class):  # type: ignore[valid-type]
        async def prepare_stream(self, input, agent_state, config):  # noqa: A002
            forwarded_props = input.forwarded_props or {}
            resume_input = forwarded_props.get("command", {}).get("resume", None)
            if resume_input:
                # Skip the message-count check entirely for resume requests.
                # Temporarily patch agent_state so the parent sees equal counts,
                # preventing the regenerate branch from triggering.
                from ag_ui_langgraph.utils import agui_messages_to_langchain
                from langchain_core.messages import SystemMessage

                messages = input.messages or []
                langchain_messages = agui_messages_to_langchain(messages)
                non_system = [m for m in langchain_messages if not isinstance(m, SystemMessage)]
                graph_messages = agent_state.values.get("messages", [])

                if len(graph_messages) > len(non_system):
                    # Clone state with the message list trimmed to input length so
                    # the parent's count guard evaluates to False (equal counts).
                    class _PatchedState:
                        def __init__(self, original, patched_values):
                            for attr in dir(original):
                                if not attr.startswith("_"):
                                    try:
                                        setattr(self, attr, getattr(original, attr))
                                    except (AttributeError, TypeError):
                                        pass
                            self.values = patched_values
                            self.tasks = original.tasks
                            self.next = original.next
                            self.metadata = original.metadata
                            self.created_at = original.created_at
                            self.config = original.config
                            self.parent_config = original.parent_config

                    patched_values = dict(agent_state.values)
                    patched_values["messages"] = graph_messages[:len(non_system)]
                    patched_state = _PatchedState(agent_state, patched_values)
                    logger.info(
                        f"[ResumeSafe] Resume detected — bypassing regenerate path "
                        f"(graph_msgs={len(graph_messages)}, ck_msgs={len(non_system)})"
                    )
                    return await super().prepare_stream(input, patched_state, config)

            return await super().prepare_stream(input, agent_state, config)

    ResumeSafeLangGraphAgent.__name__ = f"ResumeSafe_{base_class.__name__}"
    return ResumeSafeLangGraphAgent


def _inject_source_id_from_context(input_data: RunAgentInput) -> RunAgentInput:
    """Bridge sourceId from CopilotKit context array into graph state.

    CopilotKit's useCopilotReadable() injects values into the `context` list,
    not into `state`. The graph's _resolve_source_id() checks state first, so
    we parse context items here and copy sourceId into state before the agent runs.
    """
    state = input_data.state or {}
    # Only inject if source_id not already present in state
    if isinstance(state, dict) and not state.get("source_id"):
        for ctx in input_data.context or []:
            try:
                value = json.loads(ctx.value) if isinstance(ctx.value, str) else ctx.value
                if isinstance(value, dict) and value.get("sourceId"):
                    state = dict(state)
                    state["source_id"] = value["sourceId"]
                    if value.get("notebookId"):
                        state["notebook_id"] = value["notebookId"]
                    logger.info(
                        f"Injected source_id={state['source_id']} from context into state"
                    )
                    break
            except (json.JSONDecodeError, TypeError):
                continue
        # Return a new RunAgentInput with updated state (RunAgentInput is a pydantic model)
        input_data = input_data.model_copy(update={"state": state})
    return input_data


def _init_agent_class():
    global _AgentClass, _agent_class_name
    try:
        from copilotkit import LangGraphAGUIAgent

        _AgentClass = _make_resume_safe_agent_class(LangGraphAGUIAgent)
        _agent_class_name = "ResumeSafe_LangGraphAGUIAgent (CopilotKit SDK)"
    except ImportError:
        from ag_ui_langgraph import LangGraphAgent

        _AgentClass = _make_resume_safe_agent_class(LangGraphAgent)
        _agent_class_name = "ResumeSafe_LangGraphAgent (ag-ui-langgraph)"
    logger.info(f"AG-UI agent class: {_agent_class_name}")


def register_agui_endpoints(app) -> None:
    """Register the unified AG-UI chat endpoint on the FastAPI app.

    Creates a fresh agent instance per request to prevent concurrent request
    corruption (active_run, messages_in_process are instance-level state).
    The compiled graph is shared — it's stateless and thread-safe.
    """
    try:
        from open_notebook.graphs.unified_agent import get_unified_graph

        graph = get_unified_graph()
        _init_agent_class()

        @app.post("/api/agui/chat")
        async def agui_chat_endpoint(input_data: RunAgentInput, request: Request):
            # Bridge source_id from CopilotKit context array into graph state.
            # useCopilotReadable() puts values in context (not state), so we
            # extract sourceId here and inject it into state before the agent runs.
            input_data = _inject_source_id_from_context(input_data)

            # Fresh agent per request — avoids active_run/messages_in_process
            # corruption when multiple users send messages concurrently.
            agent = _AgentClass(
                name="acm_agent",
                graph=graph,
                description="ACM-AI unified agent for queries and record modification",
            )

            accept_header = request.headers.get("accept")
            encoder = EventEncoder(accept=accept_header)

            async def event_generator():
                async for event in agent.run(input_data):
                    yield encoder.encode(event)

            return StreamingResponse(
                event_generator(),
                media_type=encoder.get_content_type(),
            )

        @app.get("/api/agui/chat/health")
        def agui_health():
            return {"status": "ok", "agent": {"name": "acm_agent", "class": _agent_class_name}}

        logger.info("AG-UI unified chat endpoint registered at /api/agui/chat (per-request agent)")
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
