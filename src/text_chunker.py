"""
Semantic Text Chunker (Enterprise Version)

Features
--------
✓ Semantic chunking
✓ Table-aware chunking
✓ RBAC compatible
✓ Heading detection
✓ Metadata preservation
✓ Page mapping
✓ Token analytics
✓ Storage analytics
✓ Multi-PDF compatible
"""

import re
import logging
from typing import List, Dict, Optional

import tiktoken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """
    Enterprise semantic chunker.
    """

    def __init__(
        self,
        chunk_size: int = 300,
        overlap: int = 50
    ):

        self.chunk_size = chunk_size
        self.overlap = overlap

        self.encoding = tiktoken.get_encoding(
            "cl100k_base"
        )

        self.public_section_pattern = re.compile(
            r"^#+\s*(?:PUBLIC|GENERAL|EXTERNAL)",
            re.IGNORECASE | re.MULTILINE
        )

        self.internal_section_pattern = re.compile(
            r"^#+\s*(?:INTERNAL|RESTRICTED)",
            re.IGNORECASE | re.MULTILINE
        )

        self.confidential_section_pattern = re.compile(
            r"^#+\s*(?:CONFIDENTIAL|SECRET|HR ONLY|FINANCE ONLY)",
            re.IGNORECASE | re.MULTILINE
        )

        logger.info("TextChunker initialized")

    # --------------------------------------------------
    # TOKEN UTILITIES
    # --------------------------------------------------

    def count_tokens(
        self,
        text: str
    ) -> int:

        return len(
            self.encoding.encode(text)
        )

    # --------------------------------------------------
    # SENTENCE SPLITTING
    # --------------------------------------------------

    def split_into_sentences(
        self,
        text: str
    ) -> List[str]:

        if text.startswith("TABLE_START"):
            return [text]

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        return [

            sentence.strip()

            for sentence in sentences

            if sentence.strip()

        ]

    # --------------------------------------------------
    # ACCESS LEVEL DETECTION
    # --------------------------------------------------

    def _detect_section_access_level(
        self,
        text: str
    ) -> Optional[str]:

        if self.confidential_section_pattern.search(text):
            return "CONFIDENTIAL"

        if self.internal_section_pattern.search(text):
            return "INTERNAL"

        if self.public_section_pattern.search(text):
            return "PUBLIC"

        return None

    # --------------------------------------------------
    # PAGE LOOKUP
    # --------------------------------------------------

    def _find_page(
        self,
        chunk_text: str,
        metadata: Dict
    ) -> Optional[int]:

        page_map = metadata.get(
            "page_map",
            []
        )

        snippet = chunk_text[:200]

        for page in page_map:

            if snippet in page.get(
                "text",
                ""
            ):

                return page.get("page")

        return None

    # --------------------------------------------------
    # PARAGRAPH EXTRACTION
    # --------------------------------------------------

    def _extract_paragraphs(
        self,
        text: str
    ) -> List[str]:

        paragraphs = []

        buffer = []

        inside_table = False

        for line in text.splitlines():

            line = line.rstrip()

            if line == "TABLE_START":

                if buffer:

                    paragraphs.append(
                        "\n".join(buffer).strip()
                    )

                    buffer = []

                inside_table = True

                buffer.append(line)

                continue

            if line == "TABLE_END":

                buffer.append(line)

                paragraphs.append(
                    "\n".join(buffer).strip()
                )

                buffer = []

                inside_table = False

                continue

            if inside_table:

                buffer.append(line)

                continue

            if line.strip() == "":

                if buffer:

                    paragraphs.append(
                        "\n".join(buffer).strip()
                    )

                    buffer = []

            else:

                buffer.append(line)

        if buffer:

            paragraphs.append(
                "\n".join(buffer).strip()
            )

        return paragraphs

    # --------------------------------------------------
    # MAIN CHUNKING FUNCTION
    # --------------------------------------------------

    def chunk_text(
        self,
        text: str,
        metadata: Dict,
        detect_sections: bool = True,
        chunk_overrides: Optional[Dict[int, str]] = None
    ) -> List[Dict]:
        paragraphs = self._extract_paragraphs(text)

        chunks = []

        current_chunk = []

        current_tokens = 0

        chunk_number = 0

        default_access_level = metadata.get(
            "access_level",
            "INTERNAL"
        )

        total_document_tokens = 0

        total_document_words = 0

        total_document_characters = len(text)

        # --------------------------------------------------
        # BUILD CHUNKS
        # --------------------------------------------------

        for paragraph in paragraphs:

            sentences = self.split_into_sentences(
                paragraph
            )

            for sentence in sentences:

                sentence_tokens = self.count_tokens(
                    sentence
                )

                total_document_tokens += sentence_tokens

                total_document_words += len(
                    sentence.split()
                )

                if (
                    current_tokens + sentence_tokens >
                    self.chunk_size
                    and current_chunk
                ):

                    chunk_text = "\n".join(
                        current_chunk
                    )

                    access_level = default_access_level

                    if detect_sections:

                        detected = self._detect_section_access_level(
                            chunk_text
                        )

                        if detected:

                            access_level = detected

                    if (
                        chunk_overrides
                        and chunk_number in chunk_overrides
                    ):

                        access_level = chunk_overrides[
                            chunk_number
                        ]

                    page_number = self._find_page(
                        chunk_text,
                        metadata
                    )

                    chunk_metadata = {

                        **metadata,

                        "chunk_number":
                            chunk_number,

                        "page":
                            page_number,

                        "access_level":
                            access_level,

                        "content_type":
                            "table"
                            if chunk_text.startswith(
                                "TABLE_START"
                            )
                            else "text",

                        "token_count":
                            current_tokens,

                        "word_count":
                            len(
                                chunk_text.split()
                            ),

                        "character_count":
                            len(
                                chunk_text
                            )

                    }

                    chunks.append(

                        {

                            "chunk_id":
                                f"{metadata['filename']}_{chunk_number}",

                            "text":
                                chunk_text,

                            "token_count":
                                current_tokens,

                            "metadata":
                                chunk_metadata

                        }

                    )

                    chunk_number += 1

                    current_chunk = []

                    current_tokens = 0

                current_chunk.append(
                    sentence
                )

                current_tokens += sentence_tokens

        # --------------------------------------------------
        # FINAL CHUNK
        # --------------------------------------------------

        if current_chunk:

            chunk_text = "\n".join(
                current_chunk
            )

            access_level = default_access_level

            if detect_sections:

                detected = self._detect_section_access_level(
                    chunk_text
                )

                if detected:

                    access_level = detected

            if (
                chunk_overrides
                and chunk_number in chunk_overrides
            ):

                access_level = chunk_overrides[
                    chunk_number
                ]

            page_number = self._find_page(
                chunk_text,
                metadata
            )

            chunk_metadata = {

                **metadata,

                "chunk_number":
                    chunk_number,

                "page":
                    page_number,

                "access_level":
                    access_level,

                "content_type":
                    "table"
                    if chunk_text.startswith(
                        "TABLE_START"
                    )
                    else "text",

                "token_count":
                    current_tokens,

                "word_count":
                    len(
                        chunk_text.split()
                    ),

                "character_count":
                    len(
                        chunk_text
                    )

            }

            chunks.append(

                {

                    "chunk_id":
                        f"{metadata['filename']}_{chunk_number}",

                    "text":
                        chunk_text,

                    "token_count":
                        current_tokens,

                    "metadata":
                        chunk_metadata

                }

            )

        # --------------------------------------------------
        # ANALYTICS
        # --------------------------------------------------

        total_chunks = len(chunks)

        average_tokens = (
            total_document_tokens / total_chunks
            if total_chunks
            else 0
        )

        average_words = (
            total_document_words / total_chunks
            if total_chunks
            else 0
        )

        estimated_storage_bytes = sum(

            len(
                chunk["text"].encode(
                    "utf-8"
                )
            )

            for chunk in chunks

        )

        estimated_storage_kb = (
            estimated_storage_bytes / 1024
        )

        estimated_storage_mb = (
            estimated_storage_kb / 1024
        )
        metadata["analytics"] = {

            "total_chunks":
                total_chunks,

            "total_tokens":
                total_document_tokens,

            "total_words":
                total_document_words,

            "total_characters":
                total_document_characters,

            "average_tokens_per_chunk":
                round(
                    average_tokens,
                    2
                ),

            "average_words_per_chunk":
                round(
                    average_words,
                    2
                ),

            "estimated_storage_kb":
                round(
                    estimated_storage_kb,
                    2
                ),

            "estimated_storage_mb":
                round(
                    estimated_storage_mb,
                    4
                )

        }

        # --------------------------------------------------
        # ACCESS DISTRIBUTION
        # --------------------------------------------------

        access_distribution = {}

        for chunk in chunks:

            level = chunk["metadata"].get(
                "access_level",
                "UNKNOWN"
            )

            access_distribution[level] = (
                access_distribution.get(
                    level,
                    0
                ) + 1
            )

        # --------------------------------------------------
        # LOGGING
        # --------------------------------------------------

        logger.info("=" * 70)

        logger.info(
            f"Document : {metadata.get('filename')}"
        )

        logger.info(
            f"Created {total_chunks} chunks"
        )

        logger.info(
            f"Total Tokens : {total_document_tokens}"
        )

        logger.info(
            f"Total Words : {total_document_words}"
        )

        logger.info(
            f"Total Characters : {total_document_characters}"
        )

        logger.info(
            f"Average Tokens/Chunk : {average_tokens:.2f}"
        )

        logger.info(
            f"Average Words/Chunk : {average_words:.2f}"
        )

        logger.info(
            f"Estimated Storage : "
            f"{estimated_storage_kb:.2f} KB "
            f"({estimated_storage_mb:.4f} MB)"
        )

        logger.info(
            f"Access Distribution : "
            f"{access_distribution}"
        )

        logger.info("=" * 70)

        return chunks

    # --------------------------------------------------
    # UTILITY METHODS
    # --------------------------------------------------

    def get_chunks_by_access_level(
        self,
        chunks: List[Dict],
        access_level: str
    ) -> List[Dict]:

        return [

            chunk

            for chunk in chunks

            if chunk["metadata"].get(
                "access_level"
            ) == access_level

        ]

    def get_access_level_summary(
        self,
        chunks: List[Dict]
    ) -> Dict[str, int]:

        summary = {}

        for chunk in chunks:

            level = chunk["metadata"].get(
                "access_level",
                "UNKNOWN"
            )

            summary[level] = (
                summary.get(
                    level,
                    0
                ) + 1
            )

        return summary