"""
Embeddings Module
Converts text chunks into vectors using Ollama (nomic-embed-text)
"""

import os
from typing import List, Dict
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Ollama's nomic-embed-text model"""

    def __init__(
        self,
        model: str = None,
        ollama_host: str = None
    ):
        self.model = model or os.environ.get(
            "OLLAMA_EMBED_MODEL", "nomic-embed-text"
        )
        self.ollama_host = (
            ollama_host
            or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")

    def _extract_embedding(self, result: dict) -> List[float]:
        if "embeddings" in result and result["embeddings"]:
            return result["embeddings"][0]

        if "embedding" in result and result["embedding"]:
            return result["embedding"]

        raise ValueError(f"Unexpected Ollama embed response: {list(result.keys())}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text chunk.
        """
        try:
            response = requests.post(
                f"{self.ollama_host}/api/embed",
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=120
            )

            if response.status_code == 404:
                response = requests.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=120
                )

            response.raise_for_status()
            embedding = self._extract_embedding(response.json())

            logger.info(
                f"Generated embedding ({len(embedding)} dimensions)"
            )

            return embedding

        except requests.ConnectionError as e:
            msg = (
                f"Cannot connect to Ollama at {self.ollama_host}. "
                "Make sure Ollama is running (ollama serve)."
            )
            logger.error(msg)
            raise ConnectionError(msg) from e

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for every chunk while preserving metadata.
        """

        embedded_chunks = []
        total = len(chunks)

        for i, chunk in enumerate(chunks):

            logger.info(
                f"Embedding {i+1}/{total} : {chunk['chunk_id']}"
            )

            try:
                embedding = self.embed_text(chunk["text"])

                embedded_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "token_count": chunk["token_count"],
                    "embedding": embedding,
                    "metadata": chunk.get("metadata", {})
                })

            except Exception as e:
                logger.warning(
                    f"Skipped chunk {chunk['chunk_id']}: {e}"
                )

        logger.info(
            f"Embedded {len(embedded_chunks)}/{total} chunks successfully."
        )

        if total > 0 and len(embedded_chunks) == 0:
            raise RuntimeError(
                "Failed to embed any chunks. Check that Ollama is running and "
                f"model '{self.model}' is installed (ollama pull {self.model})."
            )

        return embedded_chunks
