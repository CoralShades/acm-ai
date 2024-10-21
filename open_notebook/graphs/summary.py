import os
from typing import List, Literal

from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.graphs.tools import get_current_timestamp
from open_notebook.prompter import Prompter
from open_notebook.utils import split_text

tools = [get_current_timestamp]
tool_node = ToolNode(tools)


class SummaryResponse(BaseModel):
    """Respond to the user with this"""

    summary: str = Field(description="The summary of the content")
    topics: List[str] = Field(description="List of 4-7 topics related to this content")
    title: str = Field(description="The title of the content")


class SummaryState(TypedDict):
    chunks: List[str]
    content: str
    summary: SummaryResponse


def build_chunks(state: SummaryState) -> dict:
    """
    Split the input text into chunks.
    """
    return {
        "chunks": split_text(
            state["content"],
            chunk=int(os.environ.get("SUMMARY_CHUNK_SIZE", 200000)),
            overlap=int(os.environ.get("SUMMARY_CHUNK_OVERLAP", 1000)),
        )
    }


def setup_next_chunk(state: SummaryState) -> dict:
    """
    Move the next item in the chunk to the processing area
    """
    state["content"] = state["chunks"].pop(0)
    return {"chunks": state["chunks"], "content": state["content"]}


def chunk_condition(state: SummaryState) -> Literal["get_chunk", END]:  # type: ignore
    """
    Checks whether there are more chunks to process.
    """
    if len(state["chunks"]) > 0:
        return "get_chunk"
    return END


# todo: build a helper method for LLM communication on all graphs
def call_model_with_messages(state: SummaryState, config: RunnableConfig) -> dict:
    model = (
        ChatOpenAI(
            model=os.environ.get("SUMMARIZATION_MODEL", os.environ["DEFAULT_MODEL"]),
            temperature=0,
        )
        .bind_tools(tools)
        .with_structured_output(SummaryResponse)
    )

    system_prompt = Prompter(prompt_template="summarize").render(data=state)
    ai_message = model.invoke(system_prompt)
    return {"summary": ai_message}


agent_state = StateGraph(SummaryState)
agent_state.add_node("setup_chunk", build_chunks)
agent_state.add_edge(START, "setup_chunk")
agent_state.add_conditional_edges(
    "setup_chunk",
    chunk_condition,
)
agent_state.add_node("get_chunk", setup_next_chunk)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_edge("get_chunk", "agent")
agent_state.add_conditional_edges(
    "agent",
    chunk_condition,
)

graph = agent_state.compile()
