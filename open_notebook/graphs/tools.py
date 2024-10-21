from datetime import datetime

from langchain.tools import tool


@tool
def get_current_timestamp() -> str:
    """
    Returns the current timestamp in the format YYYYMMDDHHmmss.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


@tool
def ask_the_document(doc_id: str, question: str):
    """
    Use this tool to ask a question to the document.
    Another LLM will ready the document and answer the question.
    Be specific and complete in your query given the LLM that will process it is very capable.
    """
    from open_notebook.graphs.ask_content import graph

    result = graph.invoke({"doc_id": doc_id, "question": question})
    return result["answer"]
