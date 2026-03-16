"""CRUD Agent — conversational CRUD chat for job-scoped ACM data (E19-S8).

Provides read + write operations on ACM records, scoped to a specific job
(source_id). All writes use the preview_write → user approval → graph-routed
execution protocol with a structural HITL barrier.
"""

import asyncio
import concurrent.futures
import json
import re
from typing import Annotated, Optional

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.crud_tools import (
    execute_pending_write,
    get_crud_context,
    preview_write,
    query_job_records,
    set_crud_context,
)
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class CRUDAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    model_id: Optional[str]


# Read + preview tools only — the LLM cannot call execute_pending_write directly.
# Write execution is handled structurally by the graph's execute_write node
# after the user approves via the frontend HITL dialog.
crud_tools = [query_job_records, preview_write]

SYSTEM_PROMPT = """You are an ACM (Asbestos Containing Material) data assistant with the ability to read and write records for the current job.

IMPORTANT RULES:
1. You are scoped to ONE JOB ONLY. Never modify records from other jobs.
2. ALWAYS call preview_write before any UPDATE, DELETE, or INSERT operation.
3. After preview_write, the UI shows an approval dialog. The system handles execution automatically when the user clicks Approve.
4. When the user says "Rejected" or "Cancel", acknowledge and do NOT attempt further writes for that operation.
5. NEVER call execute_pending_write. The system handles execution automatically when the user clicks Approve.
6. All field values must match the ACM register schema (e.g., friable must be "Friable" or "Non-friable").
7. For sample_result, valid values are: "Positive", "Negative", "Not Sampled", "No Access".
8. Be helpful — explain what you're doing in plain English.

You have these tools:
- query_job_records: Read records, count, filter
- preview_write: Preview an update/delete before executing (shows approval dialog)

WORKFLOW: preview_write → user approves via UI → system executes automatically → confirm success."""


def _extract_source_id_from_messages(messages: list) -> Optional[str]:
    """Fallback: extract source_id from CopilotKit system messages."""
    for msg in messages:
        content = getattr(msg, "content", "")
        if isinstance(content, str) and "source:" in content:
            match = re.search(r"(source:[a-z0-9]+)", content)
            if match:
                return match.group(1)
    return None


def call_crud_agent(state: CRUDAgentState, config: RunnableConfig) -> dict:
    """CRUD agent node — calls model with CRUD tools bound."""
    source_id = state.get("source_id")
    logger.debug(f"CRUD agent state keys: {list(state.keys())}, source_id from state: {source_id}")

    # Fallback: CopilotKit may not sync useCoAgent state before first message.
    # Extract source_id from CopilotKit's makeSystemMessage if not in state.
    if not source_id:
        source_id = _extract_source_id_from_messages(state.get("messages", []))
        if source_id:
            logger.info(f"CRUD agent extracted source_id from messages: {source_id}")

    # Fallback 2: check config.configurable
    if not source_id:
        source_id = config.get("configurable", {}).get("source_id")
        if source_id:
            logger.info(f"CRUD agent got source_id from config: {source_id}")

    if source_id:
        set_crud_context(source_id)
        logger.info(f"CRUD context set to {source_id}")
    else:
        logger.warning("CRUD agent: No source_id found in state, messages, or config!")

    # Include source_id in the system prompt so the LLM knows the scope
    system_prompt = SYSTEM_PROMPT
    if source_id:
        system_prompt += f"\n\nCurrent job source: {source_id}. All queries and writes are scoped to this job. Always pass this source_id context when calling tools."

    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])

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
                    tools=crud_tools,
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
                tools=crud_tools,
                max_tokens=4096,
            )
        )

    response = model.invoke(payload)
    logger.debug(f"CRUD agent response: {response}")
    return {"messages": [response]}


def should_continue(state: CRUDAgentState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def route_entry(state: CRUDAgentState) -> str:
    """Route at graph entry: intercept user approval messages for pending writes.

    This is the structural HITL barrier — approval messages are handled by the
    execute_write node directly, never reaching the LLM.
    """
    messages = state.get("messages", [])
    if not messages:
        return "agent"
    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")
    if isinstance(content, str) and re.search(
        r"Approved\.\s*Execute operation #\w+", content
    ):
        return "execute_write"
    return "agent"


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


# Build the graph — structural HITL barrier:
# START → route_entry → agent (normal) or execute_write (user approval)
# agent → should_continue → tools/END
# tools → agent
# execute_write → END
_tool_node = ToolNode(crud_tools)

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
