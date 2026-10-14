import streamlit as st

from src.version_manager import VersionManager
from config.settings import *


@st.cache_resource
def get_version_manager():
    return VersionManager(
        version_file=VERSION_FILE,
        registry_file=REGISTRY_FILE
    )


def show():
    st.title("📚 Document Registry")

    vm = get_version_manager()

    docs = vm.list_all_documents()

    if not docs:
        st.info("No documents indexed yet.")
        return

    for doc in docs:
        with st.expander(f"{doc['filename']} (v{doc['version']})"):

            departments = doc.get("departments", [])
            if departments is None:
                departments = []
            elif isinstance(departments, str):
                departments = [departments]
            st.write(f"**Current Version:** v{doc['version']} (Latest)")

            if doc.get("has_previous_versions"):
                st.info(
                    f"This document has {doc['total_versions'] - 1} archived version(s)."
                )
            st.write(f"**Departments:** {', '.join(departments)}")
            st.write(f"**Department Owner:** {doc['department_owner']}")
            st.write(f"**Access Level:** {doc['access_level']}")
            st.write(f"**Document Type:** {doc['document_type']}")
            st.write(f"**Created:** {doc['created_at']}")
            st.write(f"**Chunks:** {doc['chunk_count']}")
            history = vm.get_version_history(doc["filename"])
            with st.expander("📜 Version History"):
                for version in sorted(
                    history,
                    key=lambda x: x["version"],
                    reverse=True
                ):
                    status = version["status"]
                    if status == "active":
                        st.success(f"Version {version['version']} (Latest)")
                    else:
                        st.warning(f"Version {version['version']} (Archived)")
                    st.write(f"Uploaded by: {version.get('uploaded_by','Unknown')}")
                    st.write(f"Created: {version['created_at']}")
                    st.write(f"Access Level: {version['access_level']}")
                    st.write(f"Language: {version.get('language','-')}")
                    st.divider()