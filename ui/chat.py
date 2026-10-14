import streamlit as st

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator
from src.semantic_search import SemanticSearch
from src.rag_pipeline import RAGPipeline
from config.settings import *
from src.version_manager import VersionManager
from collections import defaultdict
@st.cache_resource
def load_pipeline():

    store = VectorStore(
        persist_dir=VECTOR_DB_PATH
    )

    embedder = EmbeddingGenerator()
    version_manager = VersionManager(
        version_file=VERSION_FILE,
        registry_file=REGISTRY_FILE

    )

    search = SemanticSearch(
        vector_store=store,
        embedding_generator=embedder,
        version_manager=version_manager
    )

    rag = RAGPipeline(
        semantic_search=search,
        model=OLLAMA_MODEL,
        ollama_host=OLLAMA_HOST,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )

    return rag


def show():

    rag = load_pipeline()

    st.title(CHAT_TITLE)

    st.caption(
        CHAT_CAPTION
    )

    st.sidebar.title(SETTINGS_TITLE)

    role = st.sidebar.selectbox(
        "User Role",
        ACCESS_LEVELS
    )

    st.sidebar.success(
        f"Current Role: {role}"
    )

    st.sidebar.divider()

    st.sidebar.info(
        SIDEBAR_DESCRIPTION
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(
                message["content"]
            )

    question = st.chat_input(
        CHAT_INPUT_PLACEHOLDER
        
    )

    if not question:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            SEARCHING_MESSAGE
        ):

            result = rag.answer_question(
                question=question,
                user_role=role
            )

        answer = result["answer"]

        st.markdown(answer)
        if (
            ENABLE_PARTIAL_INFORMATION_NOTICE
            and result.get("partial_information")
        ):
            st.info(
                PARTIAL_INFORMATION_MESSAGE
            )
        if (
            ENABLE_ACCESS_WARNING
            and result.get("access_warning")
        ):
            st.warning(
                ACCESS_DENIED_MESSAGE
            )
        st.divider()
        st.subheader("📚 Sources")
        if result.get("citations"):
            grouped = defaultdict(list)
            for citation in result["citations"]:
                grouped[citation["filename"]].append(citation)
            for filename, citations in grouped.items():
                pages = sorted({
                    str(c["page"])
                    for c in citations
                    if c.get("page") is not None
                })
                version = citations[0].get("version", "-")
                preview = citations[0].get("text", "")
                with st.container(border=True):
                    st.markdown(f"**📄 {filename}**")
                    st.write(
                        f"**Page(s):** {', '.join(pages) if pages else 'Unknown'}"
                    )
                    st.write(
                        f"**Version:** v{version}"
                    )
                    if preview:
                        with st.expander("View Source"):
                            st.write(preview)
        else:
                st.info(NO_SOURCES_MESSAGE)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })