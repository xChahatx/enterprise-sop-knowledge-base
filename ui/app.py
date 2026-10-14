import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from streamlit_option_menu import option_menu

from home_page import show as home_page
from chat import show as chat_page
from upload import show as upload_page
from registry import show as registry_page
from versions import show as versions_page
from settings import show as settings_page
# ---------------------------------------------------
# Page Config
# ---------------------------------------------------

st.set_page_config(
    page_title="Enterprise SOP AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

with st.sidebar:

    st.title("🤖 SOP AI")

    st.caption("Enterprise Knowledge Assistant")

    st.divider()

    selected = option_menu(
        menu_title=None,
        options=[
            "Home",
            "Chat",
            "Upload",
            "Registry",
            "Versions",
            "Settings"
        ],
        icons=[
            "house",
            "chat-dots",
            "cloud-upload",
            "folder",
            "clock-history",
            "gear"
        ],
        default_index=0,
    )
# ---------------------------------------------------
# PAGE ROUTING
# ---------------------------------------------------

if selected == "Home":
    home_page()

elif selected == "Chat":
    chat_page()

elif selected == "Upload":
    upload_page()

elif selected == "Registry":
    registry_page()

elif selected == "Versions":
    versions_page()
elif selected == "Settings":
    settings_page()