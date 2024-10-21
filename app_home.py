import streamlit as st

from open_notebook.exceptions import InvalidDatabaseSchema
from open_notebook.repository import check_version, execute_migration

try:
    check_version()
except InvalidDatabaseSchema as e:
    st.error(e)
    if st.button("Execute Migration.."):
        try:
            execute_migration()
            st.success("Migration executed successfully")
            st.rerun()
        except Exception as e:
            st.error(e)
    st.stop()

st.switch_page("pages/2_📒_Notebooks.py")
