"""
BM25 Keyword Search

Performs lexical keyword search over all indexed chunks.

Useful for:
- SOP IDs
- Section numbers
- Policy numbers
- Exact keywords
"""

import re
import logging

from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BM25Search:

    def __init__(self):

        self.documents = []
        self.chunk_metadata = []

        self.bm25 = None

    ##############################################################

    def _tokenize(self, text):

        text = text.lower()

        tokens = re.findall(r"\w+", text)

        return tokens

    ##############################################################

    def build_index(self, chunks):

        """
        chunks = list of chunk dictionaries
        """

        self.documents = []
        self.chunk_metadata = []

        tokenized = []

        for chunk in chunks:

            tokens = self._tokenize(chunk["text"])

            tokenized.append(tokens)

            self.documents.append(chunk["text"])

            self.chunk_metadata.append(chunk)

        self.bm25 = BM25Okapi(tokenized)

        logger.info(
            f"BM25 index built with {len(chunks)} chunks."
        )

    ##############################################################

    def search(
        self,
        query,
        top_k=5
    ):

        if self.bm25 is None:

            raise RuntimeError(
                "BM25 index not built."
            )

        query_tokens = self._tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(

            zip(scores, self.chunk_metadata),

            reverse=True,

            key=lambda x: x[0]

        )

        results = []

        for score, chunk in ranked[:top_k]:

            item = chunk.copy()

            item["bm25_score"] = float(score)

            results.append(item)

        return results