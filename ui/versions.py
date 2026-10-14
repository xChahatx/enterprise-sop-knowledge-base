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
    st.title("🕒 Version History")

    vm = get_version_manager()

    docs = vm.list_all_documents()

    if not docs:
        st.info("No documents available.")
        return

    filenames = [d["filename"] for d in docs]

    selected = st.selectbox(
        "Select Document",
        filenames
    )

    history = vm.get_version_history(selected)

    for version in history:
        st.markdown("---")
        st.write(f"### Version {version['version']}")
        st.write(f"Status: {version['status']}")
        st.write(f"Created: {version['created_at']}")
        st.write(f"Uploaded By: {version.get('uploaded_by','-')}")
        st.write(f"Access: {version.get('access_level','-')}")