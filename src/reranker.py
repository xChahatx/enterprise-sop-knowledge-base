"""
Cross Encoder Re-Ranker

Improves retrieval quality by re-ranking semantic search results.
"""

import logging
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class CrossEncoderReranker:

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        logger.info(f"Loading CrossEncoder: {model_name}")

        self.model = CrossEncoder(model_name)

        logger.info("CrossEncoder loaded successfully.")

    def rerank(
        self,
        query,
        search_results,
        top_k=3
    ):
        """
        Re-rank retrieved chunks.

        Parameters
        ----------
        query : str

        search_results : list

        top_k : int
        """

        if not search_results:
            return []

        pairs = [
            (query, result["text"])
            for result in search_results
        ]

        scores = self.model.predict(pairs)

        for result, score in zip(search_results, scores):
            result["rerank_score"] = float(score)

        ranked = sorted(
            search_results,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return ranked[:top_k]