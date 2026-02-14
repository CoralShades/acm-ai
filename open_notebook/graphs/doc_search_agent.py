"""Document Search Agent - Specialized agent for PDF/document content search.

Uses a ReAct agent loop with vector and text search tools to find
information in source documents, embeddings, and insights.
"""

import asyncio
import sqlite3
from typing import Annotated, Optional

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
from open_notebook.graphs.chat_tools import get_search_tools
from open_notebook.graphs.chat_tools.acm_tools import set_tool_context
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class DocSearchState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    notebook_id: Optional[str]
    context: Optional[str]


# Get the tools
search_tools = get_search_tools()


def call_doc_search(state: DocSearchState, config: RunnableConfig) -> dict:
    """Document Search node - calls model with search tools bound."""
    source_id = state.get("source_id")
    notebook_id = state.get("notebook_id")

    # Set tool context so tools know their scope
    set_tool_context(source_id=source_id, notebook_id=notebook_id)

    # Build system prompt
    prompt_data = {"context": state.get("context")}
    system_prompt = Prompter(prompt_template="doc_search").render(data=prompt_data)
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
                    tools=search_tools,
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
                tools=search_tools,
                max_tokens=8192,
            )
        )

    ai_message = model.invoke(payload)
    return {"messages": [ai_message]}


def should_continue(state: DocSearchState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# Build the graph
tool_node = ToolNode(search_tools)

doc_search_graph_builder = StateGraph(DocSearchState)
doc_search_graph_builder.add_node("searcher", call_doc_search)
doc_search_graph_builder.add_node("tools", tool_node)
doc_search_graph_builder.add_edge(START, "searcher")
doc_search_graph_builder.add_conditional_edges(
    "searcher", should_continue, {"tools": "tools", END: END}
)
doc_search_graph_builder.add_edge("tools", "searcher")  # Loop back after tool execution

# Compile with checkpointer
conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE, check_same_thread=False)
doc_search_memory = SqliteSaver(conn)
doc_search_graph = doc_search_graph_builder.compile(checkpointer=doc_search_memory)
