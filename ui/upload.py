import streamlit as st
import tempfile
import os

from src.vector_store import VectorStore, DocumentIndexer
from src.version_manager import VersionManager
from config.settings import *


# ---------------------------------------------------
# Initialize Backend
# ---------------------------------------------------

@st.cache_resource
def get_indexer():

    vector_store = VectorStore(
        persist_dir=VECTOR_DB_PATH,
        collection_name=COLLECTION_NAME
    )

    version_manager = VersionManager(
        version_file=VERSION_FILE,
        registry_file=REGISTRY_FILE
    )

    return DocumentIndexer(
        vector_store=vector_store,
        version_manager=version_manager
    )


# ---------------------------------------------------
# Upload Page
# ---------------------------------------------------

def show():

    st.title("📤 Upload SOP Documents")

    st.caption(
        "Upload one or more company documents into the knowledge base."
    )
    st.info(
        f"📌 Maximum upload size: {MAX_UPLOAD_SIZE_MB} MB per file."
    )

    indexer = get_indexer()

    # -------- CHANGED HERE --------

    uploaded_files = st.file_uploader(
        "Choose Company Documents",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True
    )

    departments = st.multiselect(
        "Department",
        DEPARTMENTS,
        default=["General"]
    )

    access_level = st.selectbox(
        "Access Level",
        ACCESS_LEVELS

    )
    document_type = st.selectbox(
        "Document Type",
        DOCUMENT_TYPES
    )

    if st.button("📥 Index Documents"):

        if not uploaded_files:
            st.warning("Please upload at least one Document.")
            return
        if not departments:
            st.warning("Please select a department.")
            return
        if not access_level:
            st.warning("Please select an access level.")
            return
        if not document_type:
            st.warning("Please select a document type.")
            return
        
        uploaded_by = DEFAULT_UPLOADED_BY
        department_owner = DEFAULT_DEPARTMENT_OWNER

        max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        oversized_files = []
        for file in uploaded_files:
            if file.size > max_size:
                oversized_files.append(file.name)
        if oversized_files:
            st.error(
                f"The following files exceed the {MAX_UPLOAD_SIZE_MB} MB upload limit:"
        )
            for file in oversized_files:
                st.write(f"• {file}")
            return

        progress = st.progress(0)

        success = 0
        failed = 0

        results = []

        for i, uploaded_file in enumerate(uploaded_files):

            temp_path = os.path.join(
                tempfile.gettempdir(),
                uploaded_file.name
            )

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            try:

                with st.spinner(f"Indexing {uploaded_file.name}..."):

                    result = indexer.index_document(
                        file_path=temp_path,
                        access_level=access_level,
                        departments=departments,
                        uploaded_by=uploaded_by,
                        department_owner=department_owner,
                        document_type=document_type
                    )

                success += 1

                results.append({
                    "file": uploaded_file.name,
                    "status": "Success",
                    "details": result
                })

            except Exception as e:

                failed += 1

                results.append({
                    "file": uploaded_file.name,
                    "status": "Failed",
                    "error": str(e)
                })
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            progress.progress((i + 1) / len(uploaded_files))

        st.success(
            f"Finished indexing.\n\n"
            f"✅ Success : {success}\n\n"
            f"❌ Failed : {failed}"
        )


        for item in results:

            with st.expander(item["file"], expanded=True):

                if item["status"] != "Success":

                    st.error(item["error"])
                    continue

                d = item["details"]

                st.success("Indexed Successfully")

                st.markdown(f"## 📄 {item['file']}")

                c1, c2 = st.columns(2)

                c1.write(f"Departments : {', '.join(d.get('departments', ['-']))}")
                c2.write(f"Access Level : {d.get('access_level', '-')}")

                c3, c4 = st.columns(2)

                c3.write(f"Document Type : {d.get('document_type', '-')}")
                c4.write(f"Uploaded By : {d.get('uploaded_by', '-')}")

                st.write(f"Uploaded At : {d.get('created_at', '-')}")
                st.write(f"Version : v{d.get('version', '-')}")
                st.write(f"Department Owner : {d.get('department_owner', '-')}")


                analytics = d.get("analytics", {})

                st.markdown("### 📊 Document Analytics")

                a1, a2, a3, a4 = st.columns(4)

                a1.metric(
                    "Tokens",
                    analytics.get("total_tokens", 0)
                )

                a2.metric(
                    "Words",
                    analytics.get("total_words", 0)
                )

                a3.metric(
                    "Characters",
                    analytics.get("total_characters", 0)
                )

                a4.metric(
                    "Storage",
                    f"{analytics.get('estimated_storage_kb',0)} KB"
                )

                b1, b2 = st.columns(2)

                b1.metric(
                    "Avg Tokens / Chunk",
                    analytics.get(
                        "average_tokens_per_chunk",
                        0
                    )
                )

                b2.metric(
                    "Avg Words / Chunk",
                    analytics.get(
                        "average_words_per_chunk",
                        0
                    )
                )


                dist = d.get("access_distribution")

                if dist:

                    import pandas as pd

                    df = pd.DataFrame(
                        list(dist.items()),
                        columns=["Role", "Chunks"]
                    )

                    st.bar_chart(
                        df.set_index("Role")
                    )

                st.json(d)
        get_indexer.clear()
        st.cache_resource.clear()
        st.rerun()