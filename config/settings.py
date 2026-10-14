from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

VECTOR_DB_PATH = os.getenv(
    "VECTOR_DB_PATH",
    "./data/vectorstore"
)
VERSION_FILE = os.getenv(
    "VERSION_FILE",
    "./data/versions.json"
)
REGISTRY_FILE = os.getenv(
    "REGISTRY_FILE",
    "./data/registry.json"
)

COLLECTION_NAME = os.getenv("COLLECTION_NAME")

TOP_K = int(os.getenv("TOP_K"))

TEMPERATURE = float(os.getenv("TEMPERATURE"))

MAX_TOKENS = int(os.getenv("MAX_TOKENS"))

RERANK_MODEL = os.getenv("RERANK_MODEL")
# ---------------------------------------------------
# Upload Configuration
# ---------------------------------------------------


MAX_UPLOAD_SIZE_MB = int(
    os.getenv("MAX_UPLOAD_SIZE_MB", "100")
)

SUPPORTED_FILE_TYPES = [
    "pdf",
    "docx"
]
DEFAULT_UPLOADED_BY = os.getenv(
    "DEFAULT_UPLOADED_BY",
    "Admin"
)

DEFAULT_DOCUMENT_TYPE = os.getenv(
    "DEFAULT_DOCUMENT_TYPE",
    "SOP"
)

DEPARTMENTS = os.getenv(
    "DEPARTMENTS",
    "General,HR,Finance,Engineering,Operations"
).split(",")

ACCESS_LEVELS = os.getenv(
    "ACCESS_LEVELS",
    "PUBLIC,INTERNAL,CONFIDENTIAL"
).split(",")

DOCUMENT_TYPES = os.getenv(
    "DOCUMENT_TYPES",
    "SOP,Policy,Guideline,Manual"
).split(",")

DEFAULT_DEPARTMENT_OWNER = os.getenv(
    "DEFAULT_DEPARTMENT_OWNER",
    "Admin"
)

# ---------------------------------------------------
# RBAC Configuration
# ---------------------------------------------------

ROLE_HIERARCHY = {
    "PUBLIC": 1,
    "INTERNAL": 2,
    "CONFIDENTIAL": 3
}

# ---------------------------------------------------
# Chat Messages
# ---------------------------------------------------

PARTIAL_INFORMATION_MESSAGE = os.getenv(
    "PARTIAL_INFORMATION_MESSAGE",
    (
        "📌 This answer is based only on documents you are authorized to access. "
        "Additional relevant information may exist but cannot be displayed because of your current permissions."
    )
)

ACCESS_DENIED_MESSAGE = os.getenv(
    "ACCESS_DENIED_MESSAGE",
    (
        "🔒 Some relevant information could not be included because your current access level does not permit viewing it."
    )
)

NO_INFORMATION_MESSAGE = os.getenv(
    "NO_INFORMATION_MESSAGE",
    (
        "I couldn't find any accessible information that answers your question."
    )
)
FILTERED_CHUNKS_MESSAGE = (
    "{} relevant chunk(s) were excluded because "
    "your current role does not have permission "
    "to access them."
)
NO_SOURCES_MESSAGE = (
    "No source chunks available."
)
SIDEBAR_DESCRIPTION = """
This chatbot answers questions using your indexed SOP documents.

Responses are generated only from document chunks that your role is authorized to access.
"""

CHAT_TITLE = "💬 Enterprise SOP Chat Assistant"

CHAT_CAPTION = (
    "Ask questions about your organization's SOP documents."
)
CHAT_INPUT_PLACEHOLDER = "Ask a question about your SOP documents..."

SETTINGS_TITLE = "⚙ Settings"

SEARCHING_MESSAGE = "Searching enterprise knowledge base..."

SEARCH_ANALYTICS_TITLE = "📊 Search Analytics"

RETRIEVED_SOURCES_TITLE = "Retrieved Sources"
# ---------------------------------------------------
# RBAC Behaviour
# ---------------------------------------------------

ENABLE_ACCESS_WARNING = True

ENABLE_PARTIAL_INFORMATION_NOTICE = True

# ---------------------------------------------------
# UI Configuration
# ---------------------------------------------------

DISPLAY_CONFIDENCE_AS_PERCENTAGE = True