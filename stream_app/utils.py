import streamlit as st

from open_notebook.graphs.chat import ThreadState, graph


def setup_stream_state(session_id) -> None:
    """
    Sets the value of the current session_id for langgraph thread state.
    If there is no existing thread state for this session_id, it creates a new one.
    """
    existing_state = graph.get_state({"configurable": {"thread_id": session_id}}).values
    if len(existing_state.keys()) == 0:
        st.session_state[session_id] = ThreadState(
            messages=[], context=None, notebook=None, context_config={}, response=None
        )
    else:
        st.session_state[session_id] = existing_state
    st.session_state["active_session"] = session_id
