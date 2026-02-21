"""ACM Analyst Agent - Specialized agent for structured ACM data queries.

Uses a ReAct agent loop with ACM tools to query structured data from SurrealDB.
Exposes itself as an A2A-compatible agent via agent card.
"""

import asyncio
import sqlite3
from typing import Annotated, List, Optional

from ai_prompter import Prompter
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
from open_notebook.graphs.chat_tools import get_acm_tools
from open_notebook.graphs.chat_tools.acm_tools import set_tool_context
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class ACMAnalystState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    notebook_id: Optional[str]
    context: Optional[str]


# Get the tools
acm_tools = get_acm_tools()


def call_acm_analyst(state: ACMAnalystState, config: RunnableConfig) -> dict:
    """ACM Analyst node - calls model with ACM tools bound."""
    source_id = state.get("source_id")
    notebook_id = state.get("notebook_id")

    # Set tool context so tools know their scope
    set_tool_context(source_id=source_id, notebook_id=notebook_id)

    # Build system prompt
    prompt_data = {
        "source": {"id": source_id} if source_id else None,
        "context": state.get("context"),
    }
    system_prompt = Prompter(prompt_template="acm_analyst").render(data=prompt_data)
    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    # Provision model with tools
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
                    tools=acm_tools,
                    max_tokens=8192,
                )
            )
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    try:
        asyncio.get_running_loop()
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            model = future.result()
    except RuntimeError:
        model = asyncio.run(
            provision_langchain_model_with_tools(
                str(payload),
                model_id,
                "chat",
                tools=acm_tools,
                max_tokens=8192,
            )
        )

    ai_message = model.invoke(payload)
    return {"messages": [ai_message]}


def should_continue(state: ACMAnalystState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# Build the graph
tool_node = ToolNode(acm_tools)

acm_analyst_graph_builder = StateGraph(ACMAnalystState)
acm_analyst_graph_builder.add_node("analyst", call_acm_analyst)
acm_analyst_graph_builder.add_node("tools", tool_node)
acm_analyst_graph_builder.add_edge(START, "analyst")
acm_analyst_graph_builder.add_conditional_edges(
    "analyst", should_continue, {"tools": "tools", END: END}
)
acm_analyst_graph_builder.add_edge("tools", "analyst")  # Loop back after tool execution

# Compile with checkpointer
conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE, check_same_thread=False)
acm_analyst_memory = SqliteSaver(conn)
acm_analyst_graph = acm_analyst_graph_builder.compile(checkpointer=acm_analyst_memory)
