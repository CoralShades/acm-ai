import os
import sqlite3
from typing import Annotated, List, Optional

from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from loguru import logger
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.domain import Notebook
from open_notebook.graphs.tools import ask_the_document, get_current_timestamp
from open_notebook.prompter import Prompter

tools = [get_current_timestamp, ask_the_document]
tool_node = ToolNode(tools)


class ChatResponse(BaseModel):
    """Respond to the user with this"""

    title: Optional[str] = Field(
        description="A title to be used if your question would become a new note on the project"
    )
    message: str = Field(
        description="The actual message you'd like to reply to the user"
    )
    citations: Optional[List[str]] = Field(
        description="The ids for the documents you used to formulate your answer"
    )


class ThreadState(TypedDict):
    messages: Annotated[list, add_messages]
    notebook: Optional[Notebook]
    context: Optional[str]
    context_config: Optional[dict]
    response: Optional[ChatResponse]


def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    model = ChatOpenAI(model=os.environ["DEFAULT_MODEL"], temperature=0).bind_tools(
        tools
    )
    messages = state["messages"]
    system_prompt = Prompter(prompt_template="chat").render(data=state)
    logger.warning(f"System prompt: {system_prompt}")
    ai_message = model.invoke([system_prompt] + messages)
    return {"messages": ai_message}


conn = sqlite3.connect(
    os.environ.get("CHECKPOINT_DATA_PATH", "sqlite-db/checkpoints.sqlite"),
    check_same_thread=False,
)
memory = SqliteSaver(conn)

agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_node("tools", tool_node)
agent_state.add_edge(START, "agent")
agent_state.add_conditional_edges(
    "agent",
    tools_condition,
)
agent_state.add_edge("tools", "agent")

graph = agent_state.compile(checkpointer=memory)
