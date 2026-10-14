import streamlit as st


def show():

    st.title("Enterprise SOP AI Assistant")

    st.markdown("""
Welcome to your enterprise document intelligence platform.

This assistant can:

- 💬 Answer SOP questions
- 📄 Upload new SOPs
- 📚 Manage document versions
- 🔒 Enforce Role-Based Access Control (RBAC)
- 🧠 Search using Semantic Embeddings
- 📑 Show citations and confidence
""")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Indexed Documents", "--")

    with col2:
        st.metric("Stored Chunks", "--")

    with col3:
        st.metric("Current Model", "llama3.2:1b")

    st.divider()

    st.info(
        "Select a page from the sidebar to start using the assistant."
    )