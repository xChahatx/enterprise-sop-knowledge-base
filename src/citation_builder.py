"""
Citation Builder
Maps retrieved chunks back to PDF page numbers.
"""

import logging

logger = logging.getLogger(__name__)


class CitationBuilder:

    def __init__(self):
        logger.info("CitationBuilder initialized")

    def find_page(self, chunk_text: str, page_map: list):
        """
        Find which page contains the chunk.

        Returns:
            int | None
        """

        if not page_map:
            return None

        # Compare beginning of chunk
        sample = chunk_text[:150].strip()

        for page in page_map:

            if sample in page["text"]:
                return page["page"]

        # fallback
        for page in page_map:

            if any(word in page["text"] for word in sample.split()[:15]):
                return page["page"]

        return None

    def build_citations(self, retrieved_chunks):
        """
        Build citations from retrieved chunks.

        Input:
            retrieved_chunks

        Returns:
            [
                {
                    "filename": "...",
                    "page": 3
                }
            ]
        """
        citations = []
        citation_number=1
        seen=set()

        for chunk in retrieved_chunks:

            metadata = chunk.get("metadata", {})

            filename = metadata.get(
                "filename",
                chunk.get("filename", "Unknown")
                )

            page = metadata.get("page", None)
            key = (filename, page)
            if key in seen:
                continue
            seen.add(key)


            citations.append({
                "citation_id": citation_number,
                "filename": filename,
                "page": page,
                "version": metadata.get("version"),
                "heading": metadata.get("heading"),
                "document_type": metadata.get("document_type"),
                "chunk_id": chunk.get("chunk_id"),
                "department": metadata.get("department"),
                "access_level": chunk.get("access_level"),
                "score": chunk.get(
                    "rerank_score",
                    chunk.get("relevance_score")
                ),
                "text": chunk.get("text", "")
            })
            citation_number += 1
        citations.sort(
            key=lambda x: (
                x["filename"],
                x["page"] if x["page"] is not None else 0
                )
                )
        return citations