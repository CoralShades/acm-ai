"""Unified Agent — single CopilotKit chat combining read + write + HITL.

Replaces both supervisor_agent.py (read-only) and crud_agent.py (CRUD + HITL).
Uses a single ReAct loop with all 16 tools, interrupt-based HITL for writes,
and MemorySaver for session persistence (upgrade to SqliteSaver planned).

All nodes are async — this ensures contextvars propagate correctly to tools
(no threadpool context loss).

Graph topology:
  START → agent_node (all tools bound)
    ├─ tool_calls? → tools_node → check_pending → approval_node (interrupt) → agent_node
    ├─ tool_calls? → tools_node → check_pending → agent_node (no pending)
    └─ no tool_calls → END
"""

import json
import os
import re
from typing import Annotated, Optional

from jinja2 import Environment, FileSystemLoader
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.chat_tools import get_acm_tools, get_search_tools
from open_notebook.graphs.checkpointer import get_checkpointer
from open_notebook.graphs.crud_tools import (
    ask_user_choice,
    execute_pending_write,
    get_schema_info,
    preview_bulk_write,
    preview_write,
    set_crud_context,
    surreal_query,
    undo_last_write,
)
from open_notebook.graphs.tool_context import set_tool_scope
from open_notebook.graphs.utils import provision_langchain_model_with_tools

try:
    from copilotkit.langgraph import copilotkit_emit_state

    _HAS_COPILOTKIT = True
except ImportError:
    _HAS_COPILOTKIT = False


# --- Jinja2 prompt environment ---
_prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(_prompts_dir)),
    autoescape=False,
)


class UnifiedAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    notebook_id: Optional[str]
    model_id: Optional[str]
    include_acm_context: Optional[bool]
    pending_operation: Optional[dict]


def _extract_source_id_from_messages(messages: list) -> Optional[str]:
    """Fallback: extract source_id from CopilotKit system messages."""
    for msg in messages:
        content = getattr(msg, "content", "")
        if isinstance(content, str) and "source:" in content:
            match = re.search(r"(source:[a-z0-9]+)", content)
            if match:
                return match.group(1)
    return None


def _resolve_source_id(
    state: UnifiedAgentState, config: RunnableConfig
) -> Optional[str]:
    """Resolve source_id from state, messages, or config."""
    source_id = state.get("source_id")

    if not source_id:
        source_id = _extract_source_id_from_messages(state.get("messages", []))
        if source_id:
            logger.info(f"Unified agent extracted source_id from messages: {source_id}")

    if not source_id:
        source_id = config.get("configurable", {}).get("source_id")

    return source_id


def _get_unified_tools(include_acm: bool = True):
    """Get all 15 LLM-facing tools (read + write, excluding execute_pending_write)."""
    tools = get_search_tools()
    if include_acm:
        tools = get_acm_tools() + tools

    # CRUD tools — note: execute_pending_write is NOT exposed to the LLM.
    # It runs internally inside the approval_node after interrupt() resume.
    tools.extend([
        surreal_query,
        preview_write,
        preview_bulk_write,
        get_schema_info,
        ask_user_choice,
        undo_last_write,
    ])
    return tools


def _build_system_prompt(
    source_id: Optional[str],
    notebook_id: Optional[str],
    include_acm: bool,
) -> str:
    """Build the unified system prompt using Jinja2 template."""
    try:
        template = _jinja_env.get_template("unified_agent.jinja")
        return template.render(
            source_id=source_id,
            notebook_id=notebook_id,
            include_acm_context=include_acm,
        )
    except Exception as e:
        logger.warning(f"Failed to render unified_agent.jinja: {e}")
        prompt = (
            "You are an ACM data assistant. Use search tools for reads "
            "and preview_write for writes. Always preview before writing."
        )
        if source_id:
            prompt += f"\n\nCurrent job source: {source_id}."
        return prompt


# --- Graph Nodes (all async) ---


async def call_unified_agent(state: UnifiedAgentState, config: RunnableConfig) -> dict:
    """Main agent node — sets context, provisions model with all tools, invokes LLM."""
    source_id = _resolve_source_id(state, config)
    notebook_id = state.get("notebook_id")
    include_acm = state.get("include_acm_context", True)

    # Set unified tool context for all tools (async context — propagates to tool calls)
    set_tool_scope(source_id=source_id, notebook_id=notebook_id)
    if source_id:
        set_crud_context(source_id)

    tools = _get_unified_tools(include_acm=include_acm)
    system_prompt = _build_system_prompt(source_id, notebook_id, include_acm)

    # LLM router: extract entities from last user message to enhance prompt
    messages = state.get("messages", [])
    try:
        from open_notebook.graphs.llm_router import (
            build_entity_hint,
            classify_with_entities,
        )

        last_user_msg = ""
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "human":
                last_user_msg = getattr(msg, "content", "")
                break
            elif hasattr(msg, "content") and not hasattr(msg, "tool_calls"):
                from langchain_core.messages import HumanMessage
                if isinstance(msg, HumanMessage):
                    last_user_msg = msg.content
                    break

        if last_user_msg:
            router_result = classify_with_entities(last_user_msg)
            entity_hint = build_entity_hint(router_result)
            if entity_hint:
                system_prompt += entity_hint
    except Exception:
        pass  # Router is optional — graceful degradation

    payload = [SystemMessage(content=system_prompt)] + messages

    model_id = state.get("model_id") or config.get("configurable", {}).get("model_id")

    model = await provision_langchain_model_with_tools(
        str(payload),
        model_id,
        "chat",
        tools=tools,
        max_tokens=8192,
    )

    # Pass config for streaming propagation — LangGraph intercepts model
    # callbacks and emits TEXT_MESSAGE_CONTENT events via AG-UI protocol
    ai_message = await model.ainvoke(payload, config=config)

    # Emit intermediate state for CopilotKit
    if _HAS_COPILOTKIT:
        try:
            await copilotkit_emit_state(
                config,
                {
                    "include_acm_context": include_acm,
                    "status": "responding",
                },
            )
        except Exception:
            pass  # Non-fatal

    return {"messages": [ai_message]}


def _detect_pending_operation(state: UnifiedAgentState) -> Optional[dict]:
    """Check if the last tool message contains a pending write preview."""
    messages = state.get("messages", [])
    if not messages:
        return None

    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")
    if not isinstance(content, str):
        return None

    try:
        data = json.loads(content)
        if isinstance(data, dict) and data.get("type") in (
            "preview_write",
            "preview_bulk_write",
        ):
            if data.get("operation_id") and not data.get("error"):
                return data
    except (json.JSONDecodeError, TypeError):
        pass

    return None


def check_pending_and_route(state: UnifiedAgentState) -> str:
    """After tools execute, check if a pending write was created.

    If so, route to the approval node for interrupt-based HITL.
    Otherwise, loop back to the agent.
    """
    pending = _detect_pending_operation(state)
    if pending:
        return "approval"
    return "agent"


async def approval_node(state: UnifiedAgentState) -> dict:
    """Pause for user approval of a write operation using LangGraph interrupt().

    The interrupt payload is surfaced to the frontend via AG-UI protocol.
    CopilotKit's useLangGraphInterrupt renders the approval dialog.
    On resume, the user's decision (approve/reject + optional edits) is returned.
    """
    pending = _detect_pending_operation(state)
    if not pending:
        return {"messages": [AIMessage(content="No pending operation to approve.")]}

    operation_id = pending.get("operation_id", "unknown")

    # Construct the HITL payload for the frontend
    hitl_payload = {
        "type": "write_approval",
        "operation_id": operation_id,
        "operation": pending.get("operation"),
        "record_id": pending.get("record_id"),
        "field": pending.get("field"),
        "new_value": pending.get("new_value"),
        "reason": pending.get("reason"),
        "affected_count": pending.get("affected_count"),
        "record_ids": pending.get("record_ids"),
    }

    # interrupt() pauses the graph — the payload goes to the frontend
    # The frontend calls Command(resume=...) with the user's decision
    decision_str = interrupt(hitl_payload)

    # Parse the decision (comes as a string from CopilotKit resolve())
    decision = {}
    if isinstance(decision_str, str):
        try:
            decision = json.loads(decision_str)
        except (json.JSONDecodeError, TypeError):
            decision = {"approved": decision_str.lower() in ("true", "yes", "approve")}
    elif isinstance(decision_str, dict):
        decision = decision_str

    if decision.get("approved"):
        edits = decision.get("edits")
        source_id = state.get("source_id")
        try:
            result = await execute_pending_write.ainvoke({
                "operation_id": operation_id,
                "source_id": source_id,
                "edits": edits,
            })
        except Exception as e:
            logger.error(f"Error executing approved write: {e}")
            result = f"Error executing write: {str(e)}"

        return {
            "messages": [AIMessage(content=result)],
            "pending_operation": None,
        }
    else:
        return {
            "messages": [
                AIMessage(content=f"Operation #{operation_id} cancelled by user.")
            ],
            "pending_operation": None,
        }


def should_continue(state: UnifiedAgentState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# --- Build the Graph ---


def build_unified_graph():
    """Build and compile the unified agent graph."""
    tools = _get_unified_tools(include_acm=True)
    tool_node = ToolNode(tools)

    builder = StateGraph(UnifiedAgentState)

    # Nodes
    builder.add_node("agent", call_unified_agent)
    builder.add_node("tools", tool_node)
    builder.add_node("approval", approval_node)

    # START → agent (direct, no legacy routing)
    builder.add_edge(START, "agent")

    # Agent decides: call tools or end
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )

    # After tools: check if a pending write was created → approval or back to agent
    builder.add_conditional_edges(
        "tools",
        check_pending_and_route,
        {"approval": "approval", "agent": "agent"},
    )

    # After approval, loop back to agent (to summarize result)
    builder.add_edge("approval", "agent")

    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


# Lazy graph instance — compiled on first access (after checkpointer init)
_unified_graph = None


def get_unified_graph():
    """Get the compiled unified graph. Lazy initialization.

    Must be called after init_checkpointer() for durable persistence.
    Falls back to MemorySaver if checkpointer not initialized.
    """
    global _unified_graph
    if _unified_graph is None:
        _unified_graph = build_unified_graph()
    return _unified_graph


# Backward-compat: module-level access for imports that use `unified_graph` directly.
# Prefer get_unified_graph() for new code.
unified_graph = None  # Set to None; callers should use get_unified_graph()
