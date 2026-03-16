"""CRUD Agent — conversational CRUD chat for job-scoped ACM data (E19-S8).

Provides read + write operations on ACM records, scoped to a specific job
(source_id). All writes use the preview_write → interrupt → approve/reject
protocol via LangGraph's interrupt() for CopilotKit HITL integration.
"""

import asyncio
import concurrent.futures
import json
from typing import Annotated, Optional

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.crud_tools import (
    execute_pending_write,
    preview_write,
    query_job_records,
    set_crud_context,
)
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class CRUDAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    model_id: Optional[str]


# Only read + preview tools — writes are executed via interrupt approval
crud_tools = [query_job_records, preview_write]

SYSTEM_PROMPT = """You are an ACM (Asbestos Containing Material) data assistant with the ability to read and write records for the current job.

IMPORTANT RULES:
1. You are scoped to ONE JOB ONLY. Never modify records from other jobs.
2. ALWAYS call preview_write before any UPDATE, DELETE, or INSERT operation.
3. The system will automatically show a confirmation dialog to the user after preview_write.
4. Do NOT ask the user to type "confirm" — the UI handles approval automatically.
5. All field values must match the ACM register schema (e.g., friable must be "Friable" or "Non-friable").
6. For sample_result, valid values are: "Positive", "Negative", "Not Sampled", "No Access".
7. Be helpful — explain what you're doing in plain English.

You have these tools:
- query_job_records: Read records, count, filter
- preview_write: Preview an update/delete before executing (triggers approval dialog)

When a user asks to update something, call preview_write. The system will present an approval dialog to the user and handle execution automatically."""


def _extract_source_id_from_messages(messages: list) -> Optional[str]:
    """Fallback: extract source_id from CopilotKit system messages."""
    import re
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
    # Fallback: CopilotKit may not sync useCoAgent state before first message.
    # Extract source_id from CopilotKit's makeSystemMessage if not in state.
    if not source_id:
        source_id = _extract_source_id_from_messages(state.get("messages", []))
    if source_id:
        set_crud_context(source_id)

    # Include source_id in the system prompt so the LLM knows the scope
    system_prompt = SYSTEM_PROMPT
    if source_id:
        system_prompt += f"\n\nCurrent job source: {source_id}. All queries and writes are scoped to this job."

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


def check_write_approval(state: CRUDAgentState) -> dict:
    """Check if the last tool result was a preview_write and interrupt for approval.

    This node runs after tool execution. If a preview_write was generated,
    it uses LangGraph's interrupt() to pause and wait for user approval via
    CopilotKit's useLangGraphInterrupt hook. On resume:
    - If approved: executes the write and returns a success message
    - If rejected: returns a cancellation message
    """
    messages = state.get("messages", [])
    source_id = state.get("source_id")

    # Walk backwards through messages to find the most recent ToolMessage
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            continue
        try:
            data = json.loads(msg.content)
        except (json.JSONDecodeError, TypeError):
            break

        if data.get("type") != "preview_write":
            break

        operation_id = data.get("operation_id", "")

        # Pause execution — CopilotKit renders approval dialog via useLangGraphInterrupt
        decision = interrupt({
            "type": "write_approval",
            "preview": data,
        })

        # Handle both dict and JSON string from CopilotKit resolve()
        if isinstance(decision, str):
            try:
                decision = json.loads(decision)
            except (json.JSONDecodeError, TypeError):
                decision = {}

        if isinstance(decision, dict) and decision.get("approved"):
            edits = decision.get("edits", {})
            result = execute_pending_write(
                operation_id,
                source_id=source_id,
                edits=edits,
            )
            return {"messages": [AIMessage(content=result)]}
        else:
            return {
                "messages": [
                    AIMessage(
                        content=f"Write operation #{operation_id} was cancelled."
                    )
                ]
            }

    # No preview_write found — pass through
    return state


def should_continue(state: CRUDAgentState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# Build the graph
_tool_node = ToolNode(crud_tools)

_builder = StateGraph(CRUDAgentState)
_builder.add_node("agent", call_crud_agent)
_builder.add_node("tools", _tool_node)
_builder.add_node("check_approval", check_write_approval)
_builder.add_edge(START, "agent")
_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
_builder.add_edge("tools", "check_approval")
_builder.add_edge("check_approval", "agent")

_memory = MemorySaver()
crud_graph = _builder.compile(checkpointer=_memory)
