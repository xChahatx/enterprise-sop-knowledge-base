import streamlit as st
from config.settings import *

def show():

    st.title("⚙ Settings")

    st.subheader("Current Configuration")

    st.write("Model:", OLLAMA_MODEL)
    st.write("Host:", OLLAMA_HOST)
    st.write("Collection:", COLLECTION_NAME)
    st.write("Vector DB:", VECTOR_DB_PATH)
    st.write("Top K:", TOP_K)
    st.write("Temperature:", TEMPERATURE)
    st.write("Max Tokens:", MAX_TOKENS)