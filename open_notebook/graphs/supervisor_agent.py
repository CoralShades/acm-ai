"""Supervisor Agent - Orchestrates ACM Analyst and Document Search agents.

The supervisor receives user messages, decides which specialist agent(s)
to delegate to, and synthesizes their responses. It uses a ReAct loop
where its "tools" are the sub-agent invocations.
"""

import asyncio
import json
from typing import Annotated, List, Optional

from ai_prompter import Prompter
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.graphs.chat_tools import get_acm_tools, get_search_tools
from open_notebook.graphs.chat_tools.acm_tools import set_tool_context
from open_notebook.graphs.utils import provision_langchain_model_with_tools


class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    source_id: Optional[str]
    notebook_id: Optional[str]
    include_acm_context: Optional[bool]
    active_agents: Optional[List[str]]
    acm_results: Optional[dict]
    search_results: Optional[dict]


def _get_supervisor_tools(include_acm: bool = True):
    """Get the tools available to the supervisor.

    The supervisor has ALL tools directly (both ACM and search),
    rather than delegating through sub-agents. This is simpler
    and avoids A2A overhead for same-process agents.
    """
    tools = get_search_tools()
    if include_acm:
        tools = get_acm_tools() + tools
    return tools


def call_supervisor(state: SupervisorState, config: RunnableConfig) -> dict:
    """Supervisor node - routes to tools or responds directly."""
    source_id = state.get("source_id")
    notebook_id = state.get("notebook_id")
    include_acm = state.get("include_acm_context", True)

    # Set tool context for scoping
    set_tool_context(source_id=source_id, notebook_id=notebook_id)

    # Get tools based on ACM context toggle
    tools = _get_supervisor_tools(include_acm=include_acm)

    # Build system prompt
    prompt_data = {
        "source_id": source_id,
        "notebook_id": notebook_id,
        "include_acm_context": include_acm,
    }
    system_prompt = Prompter(prompt_template="supervisor").render(data=prompt_data)
    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    # Provision model with tools
    model_id = config.get("configurable", {}).get("model_id")

    # TODO: Use Model.get(model_id).get_max_output_tokens() for dynamic lookup
    # when the sync-to-async bridge pattern here allows it without deadlocks.
    # 8192 is a safe cross-model default (Haiku limit; larger models handle more).
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
                tools=tools,
                max_tokens=8192,
            )
        )

    ai_message = model.invoke(payload)
    return {"messages": [ai_message]}


def should_continue(state: SupervisorState) -> str:
    """Check if the last message has tool calls that need execution."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_supervisor_graph(include_acm: bool = True):
    """Build and compile the supervisor graph.

    Args:
        include_acm: Whether to include ACM tools (default True)

    Returns:
        Compiled StateGraph
    """
    tools = _get_supervisor_tools(include_acm=include_acm)
    tool_node = ToolNode(tools)

    graph_builder = StateGraph(SupervisorState)
    graph_builder.add_node("supervisor", call_supervisor)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_conditional_edges(
        "supervisor", should_continue, {"tools": "tools", END: END}
    )
    graph_builder.add_edge("tools", "supervisor")  # Loop back after tool execution

    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)


# Default supervisor graph with all tools
supervisor_graph = build_supervisor_graph(include_acm=True)
