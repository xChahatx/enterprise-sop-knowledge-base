# Enterprise SOP Knowledge Base

A RAG-based assistant that answers questions about company Standard Operating Procedures (SOPs). It combines hybrid retrieval, reranking, citations, and chunk-level access control, and runs locally with [Ollama](https://ollama.com).

<!-- Add a screenshot of the chat page here once you have one:
![Chat page](docs/screenshots/chat.png)
-->

## Features

- **Document ingestion**: parses PDF and DOCX files and splits them into token-aware chunks
- **Hybrid retrieval**: semantic search over a ChromaDB vector store, combined with BM25 keyword search
- **Reranking**: a cross-encoder (`ms-marco-MiniLM-L-6-v2`) reorders the retrieved chunks before answering
- **Citations**: answers point back to the source document and chunk
- **Access control**: documents are uploaded with a department and access level (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`), and sections under headings such as `# HR ONLY` or `# FINANCE ONLY` are restricted at the chunk level
- **Version management**: tracks document versions and keeps a registry of uploaded files
- **Conversation memory**: follow-up questions like "How many days?" are rewritten using the previous turn
- **Streamlit UI**: pages for upload, registry, versions, chat, and settings

## How it works

```
Upload  ->  doc_parser  ->  text_chunker  ->  embeddings  ->  vector_store (ChromaDB)

Question -> semantic_search + bm25_search -> reranker -> prompt_builder -> llm (Ollama) -> citation_builder
```

## Project structure

```
sop_vector_db/
├── config/
│   └── settings.py            # settings loaded from .env
├── data/                      # generated at runtime (not tracked)
├── sample_docs/               # demo SOPs with restricted sections
├── src/
│   ├── doc_parser.py
│   ├── text_chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── version_manager.py
│   ├── semantic_search.py
│   ├── bm25_search.py
│   ├── reranker.py
│   ├── citation_builder.py
│   ├── conversation_memory.py
│   ├── prompt_builder.py
│   ├── llm.py
│   └── rag_pipeline.py
├── tests/                     # test scripts for each module
├── ui/                        # Streamlit app
├── .env.example
├── requirements.txt
└── README.md
```

## Getting started

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.com) installed and running, with the default model pulled:

```bash
ollama pull llama3.2:3b
```

### Installation

```bash
git clone https://github.com/xChahatx/enterprise-sop-knowledge-base.git
cd enterprise-sop-knowledge-base

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

### Run the app

```bash
streamlit run ui/app.py
```

Some models (such as the reranker) are downloaded from Hugging Face the first time you run the app, so the first start can take a few minutes.

## Try it with the sample documents

1. Open the **Upload** page and upload the files in `sample_docs/`.
2. Open the **Chat** page and ask: *"How many days of annual leave do employees get?"*
3. Ask about leave encashment approval or the payroll bonus pool to see how the restricted `# HR ONLY` and `# FINANCE ONLY` sections are handled.

All sample content is fictional.

## Configuration

Settings live in `.env` (see `.env.example`):

| Variable | Purpose | Default |
| --- | --- | --- |
| `OLLAMA_HOST` | Ollama server address | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model used to generate answers | `llama3.2:3b` |
| `VECTOR_DB_PATH` | ChromaDB storage location | `./data/vectorstore` |
| `COLLECTION_NAME` | ChromaDB collection name | `sop_documents` |
| `TOP_K` | Chunks passed to the LLM | `3` |
| `TEMPERATURE` | LLM sampling temperature | `0.3` |
| `MAX_TOKENS` | Maximum answer length in tokens | `500` |
| `RERANK_MODEL` | Cross-encoder used for reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `DEPARTMENTS` | Departments available at upload | `General,HR,Finance,Engineering,Operations` |
| `ACCESS_LEVELS` | Access levels available at upload | `PUBLIC,INTERNAL,CONFIDENTIAL` |

## Tech stack

Python, Streamlit, ChromaDB, Ollama, sentence-transformers, rank-bm25, PyMuPDF, pdfplumber, python-docx, tiktoken, pandas

## Roadmap

- [ ] FastAPI REST layer for programmatic access

## Author

Chahat ([@xChahatx](https://github.com/xChahatx))
