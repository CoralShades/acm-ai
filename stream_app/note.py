import streamlit as st
from humanize import naturaltime
from loguru import logger
from streamlit_monaco import st_monaco  # type: ignore

from open_notebook.domain import Note

from .consts import context_icons


@st.dialog("Write a Note", width="large")
def add_note(session_id):
    note_title = st.text_input("Title")
    note_content = st.text_area("Content")
    if st.button("Save", key="add_note"):
        logger.debug("Adding note")
        note = Note(title=note_title, content=note_content, note_type="human")
        note.save()
        note.add_to_notebook(st.session_state[session_id]["notebook"].id)
        st.rerun()


@st.dialog("Add a Source", width="large")
def note_panel(session_id=None, note_id=None):
    if note_id:
        note: Note = Note.get(note_id)
    else:
        note: Note = Note()

    t_preview, t_edit = st.tabs(["Preview", "Edit"])
    with t_preview:
        st.subheader(note.title)
        st.markdown(note.content)
    with t_edit:
        note.title = st.text_input("Title", value=note.title)
        note.content = st_monaco(
            value=note.content, height="600px", language="markdown"
        )
        if st.button("Save", key=f"edit_note_{note_id}"):
            logger.debug("Editing note")
            note.save()
            if not note.id:
                note.add_to_notebook(st.session_state[session_id]["notebook"].id)
            st.rerun()
    if st.button("Delete", key=f"delete_note_{note_id}"):
        logger.debug("Deleting note")
        note.delete()
        st.rerun()


def note_card(session_id, note):
    if note.note_type == "human":
        icon = "🤵"
    else:
        icon = "🤖"

    context_state = st.selectbox(
        "Context",
        label_visibility="collapsed",
        options=context_icons,
        index=0,
        key=f"note_{note.id}",
    )
    with st.expander(f"{icon} **{note.title}** {naturaltime(note.updated)}"):
        st.write(note.content)
        with st.popover("Actions"):
            if st.button("Edit Note", icon="📝", key=f"edit_note_{note.id}"):
                note_panel(session_id, note.id)
            if st.button("Delete", icon="🗑️", key=f"delete_options_{note.id}"):
                note.delete()
                st.rerun()

    st.session_state[session_id]["context_config"][note.id] = context_state


def note_list_item(note_id, score=None):
    logger.debug(note_id)
    note: Note = Note.get(note_id)
    if note.note_type == "human":
        icon = "🤵"
    else:
        icon = "🤖"

    with st.expander(
        f"{icon} [{score:.2f}] **{note.title}** {naturaltime(note.updated)}"
    ):
        st.write(note.content)
        if st.button("Edit Note", icon="📝", key=f"x_edit_note_{note.id}"):
            note_panel(note_id=note.id)
