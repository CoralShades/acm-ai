"""CRUD Agent — conversational CRUD chat for job-scoped ACM data.

Provides read + write operations on ACM records, scoped to a specific job
(source_id). All writes use the preview_write → user approval → graph-routed
execution protocol with a structural HITL barrier.

Graph topology:
  START → route_entry → (HITL approval?) → execute_write → END
                      → (normal?) → agent → (tool_calls?) → tools → agent → ... → END
"""

import asyncio
import concurrent.futures
import json
import os
import re
from typing import Annotated, Optional

from jinja2 import Environment, FileSystemLoader
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.crud_tools import (
    ask_user_choice,
    execute_pending_write,
    get_crud_context,
    get_schema_info,
    preview_bulk_write,
    preview_write,
    set_crud_context,
    surreal_query,
    undo_last_write,
)
from open_notebook.graphs.guardrails import classify_intent
from open_notebook.graphs.utils import provision_langchain_model_with_tools

# --- Jinja2 prompt environment ---
_prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(_prompts_dir)),
    autoescape=False,
)


class CRUDAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    model_id: Optional[str]
    intent: Optional[str]


# Tool sets by intent
_read_tools = [surreal_query, get_schema_info, ask_user_choice]
_write_tools = [
    surreal_query,
    preview_write,
    preview_bulk_write,
    ask_user_choice,
    undo_last_write,
]
_all_tools = [
    surreal_query,
    preview_write,
    preview_bulk_write,
    get_schema_info,
    ask_user_choice,
    undo_last_write,
]


def _extract_source_id_from_messages(messages: list) -> Optional[str]:
    """Fallback: extract source_id from CopilotKit system messages."""
    for msg in messages:
        content = getattr(msg, "content", "")
        if isinstance(content, str) and "source:" in content:
            match = re.search(r"(source:[a-z0-9]+)", content)
            if match:
                return match.group(1)
    return None


def _resolve_source_id(state: CRUDAgentState, config: RunnableConfig) -> Optional[str]:
    """Resolve source_id from state, messages, or config."""
    source_id = state.get("source_id")

    if not source_id:
        source_id = _extract_source_id_from_messages(state.get("messages", []))
        if source_id:
            logger.info(f"CRUD agent extracted source_id from messages: {source_id}")

    if not source_id:
        source_id = config.get("configurable", {}).get("source_id")
        if source_id:
            logger.info(f"CRUD agent got source_id from config: {source_id}")

    if source_id:
        set_crud_context(source_id)
    else:
        logger.warning("CRUD agent: No source_id found in state, messages, or config!")

    return source_id


def _build_system_prompt(source_id: Optional[str]) -> str:
    """Build the system prompt using the Jinja2 template."""
    try:
        template = _jinja_env.get_template("crud/crud_system.jinja")
        return template.render(source_id=source_id or "unknown")
    except Exception:
        # Fallback if template is missing
        prompt = (
            "You are an ACM data assistant. Use surreal_query for reads "
            "and preview_write for writes. Always preview before writing."
        )
        if source_id:
            prompt += f"\n\nCurrent job source: {source_id}."
        return prompt


def route_entry(state: CRUDAgentState) -> str:
    """Route at graph entry: intercept user approval messages for pending writes.

    This is the structural HITL barrier — approval messages are handled by the
    execute_write node directly, never reaching the LLM.

    For normal messages, classify intent and route appropriately.
    """
    messages = state.get("messages", [])
    if not messages:
        return "agent"

    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")

    # Check for HITL approval pattern (single and bulk operations)
    if isinstance(content, str) and re.search(
        r"Approved\.\s*Execute operation #\w+", content
    ):
        return "execute_write"

    return "agent"


def call_crud_agent(state: CRUDAgentState, config: RunnableConfig) -> dict:
    """CRUD agent node — classifies intent, selects tools, calls model."""
    source_id = _resolve_source_id(state, config)

    # Classify intent from last user message
    messages = state.get("messages", [])
    last_user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = getattr(msg, "content", "")
            break
        elif isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    intent = classify_intent(last_user_msg) if last_user_msg else "general"
    logger.info(f"CRUD agent classified intent: {intent} for: {last_user_msg[:80]}")

    # Select tools based on intent
    if intent == "write":
        tools = _write_tools
    elif intent in ("read", "analytics"):
        tools = _read_tools
    else:
        tools = _all_tools

    system_prompt = _build_system_prompt(source_id)
    payload = [SystemMessage(content=system_prompt)] + messages

    model_id = state.get("model_id") or config.get("configurable", {}).get("model_id")

    def run_in_new_loop():
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(
                provision_langchain_model_with_tools(
                    str(payload),
                    model_id,
                    "chat",
                    tools=tools,
                    max_tokens=4096,
                )
            )
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            model = executor.submit(run_in_new_loop).result()
    except RuntimeError:
        model = asyncio.run(
            provision_langchain_model_with_tools(
                str(payload),
                model_id,
                "chat",
                tools=tools,
                max_tokens=4096,
            )
        )

    response = model.invoke(payload)
    logger.debug(f"CRUD agent response type: {type(response).__name__}")
    return {"messages": [response], "intent": intent}


def should_continue(state: CRUDAgentState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def execute_write_node(state: CRUDAgentState) -> dict:
    """Execute an approved write operation.

    Called by the graph router when user approval is detected, never by the LLM.
    This ensures the LLM cannot self-approve write operations.
    """
    messages = state.get("messages", [])
    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")

    # Ensure source context is set
    source_id = state.get("source_id")
    if not source_id:
        source_id = _extract_source_id_from_messages(messages)
    if not source_id:
        source_id = get_crud_context()
    if source_id:
        set_crud_context(source_id)

    match = re.search(r"Execute operation #(\w+)", content)
    if not match:
        return {
            "messages": [
                AIMessage(content="Could not parse operation ID from approval.")
            ]
        }

    operation_id = match.group(1)

    # Extract optional user edits from approval message
    edits = None
    edits_match = re.search(r"with edits:\s*(\{.*\})", content)
    if edits_match:
        try:
            edits = json.loads(edits_match.group(1))
        except json.JSONDecodeError:
            pass

    try:
        result = execute_pending_write.invoke(
            {
                "operation_id": operation_id,
                "source_id": source_id,
                "edits": edits,
            }
        )
    except Exception as e:
        logger.error(f"Error in execute_write_node: {e}")
        result = f"Error executing write: {str(e)}"

    return {"messages": [AIMessage(content=result)]}


# Build the graph
_tool_node = ToolNode(_all_tools)

_builder = StateGraph(CRUDAgentState)
_builder.add_node("agent", call_crud_agent)
_builder.add_node("tools", _tool_node)
_builder.add_node("execute_write", execute_write_node)
_builder.add_conditional_edges(
    START, route_entry, {"agent": "agent", "execute_write": "execute_write"}
)
_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
_builder.add_edge("tools", "agent")
_builder.add_edge("execute_write", END)

_memory = MemorySaver()
crud_graph = _builder.compile(checkpointer=_memory)
