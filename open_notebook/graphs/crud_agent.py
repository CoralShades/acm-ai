"""CRUD Agent — conversational CRUD chat for job-scoped ACM data (E19-S8).

Provides read + write operations on ACM records, scoped to a specific job
(source_id). All writes use the preview_write -> confirm_write protocol.
"""

import asyncio
import concurrent.futures
from typing import Annotated, Optional

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.crud_tools import (
    confirm_write,
    preview_write,
    query_job_records,
    set_crud_context,
)
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class CRUDAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]


crud_tools = [query_job_records, preview_write, confirm_write]

SYSTEM_PROMPT = """You are an ACM (Asbestos Containing Material) data assistant with the ability to read and write records for the current job.

IMPORTANT RULES:
1. You are scoped to ONE JOB ONLY. Never modify records from other jobs.
2. ALWAYS call preview_write before any UPDATE, DELETE, or INSERT operation.
3. NEVER execute a write until the user explicitly confirms with "confirm {operation_id}".
4. All field values must match the ACM register schema (e.g., friable must be "Friable" or "Non-friable").
5. For sample_result, valid values are: "Positive", "Negative", "Not Sampled", "No Access".
6. Be helpful — explain what you're doing in plain English.

You have these tools:
- query_job_records: Read records, count, filter
- preview_write: Preview an update/delete before executing
- confirm_write: Execute a confirmed operation

When a user asks to update something, ALWAYS preview first, then wait for confirmation."""


def call_crud_agent(state: CRUDAgentState, config: RunnableConfig) -> dict:
    """CRUD agent node — calls model with CRUD tools bound."""
    source_id = state.get("source_id")
    if source_id:
        set_crud_context(source_id)

    payload = [SystemMessage(content=SYSTEM_PROMPT)] + state.get("messages", [])

    model_id = config.get("configurable", {}).get("model_id")

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


# Build the graph
_tool_node = ToolNode(crud_tools)

_builder = StateGraph(CRUDAgentState)
_builder.add_node("agent", call_crud_agent)
_builder.add_node("tools", _tool_node)
_builder.add_edge(START, "agent")
_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
_builder.add_edge("tools", "agent")

crud_graph = _builder.compile()
