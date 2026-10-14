from typing import List, Dict, Optional
import logging
import time

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator
from config.settings import ROLE_HIERARCHY
from collections import defaultdict
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticSearch:

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        version_manager,
        relevance_threshold: float = 0.7
    ):

        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.version_manager = version_manager
        self.relevance_threshold = relevance_threshold

        self.role_hierarchy = ROLE_HIERARCHY

        logger.info(
            f"SemanticSearch initialized | threshold={relevance_threshold}"
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        relevance_threshold: Optional[float] = None,
        user_role: Optional[str] = "PUBLIC",
        metadata_filter: Optional[Dict] = None
    ) -> Dict:

        start = time.time()

        threshold = (
            relevance_threshold
            if relevance_threshold is not None
            else self.relevance_threshold
        )

        query_lower = query.lower()
        document_queries = [
            "sop",
            "standard operating procedure",
            "guideline",
            "guidelines",
            "policy",
            "manual",
            "protocol",

        ]
        if any(term in query_lower for term in document_queries):
            n_results = max(n_results, 10)
        elif len(query.split()) > 10:
            n_results = max(n_results, 8)

        query_embedding = self.embedding_generator.embed_text(
            query
        )

        raw_results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results * 3,
            where=metadata_filter
        )

        filtered_results, filtered_chunks = (
            self._filter_by_access_and_relevance(
                raw_results=raw_results,
                user_role=user_role,
                threshold=threshold
            )
        )

        unique_results = []
        seen = set()

        for chunk in filtered_results:

            key = (
                chunk.get("filename"),
                chunk.get("page"),
                chunk.get("chunk_id")
            )

            if key in seen:
                continue

            seen.add(key)
            unique_results.append(chunk)

        final_results = unique_results[:n_results]

        retrieval_time = round(
            time.time() - start,
            3
        )

        average_score = 0.0

        if final_results:

            average_score = round(
                sum(
                    item["relevance_score"]
                    for item in final_results
                ) / len(final_results),
                3
            )

        logger.info("=" * 60)
        logger.info(f"Query : {query}")
        logger.info(f"Retrieved : {len(raw_results)}")
        logger.info(f"Authorized : {len(filtered_results)}")
        logger.info(f"Returned : {len(final_results)}")
        logger.info(f"Average Score : {average_score}")
        logger.info(f"Retrieval Time : {retrieval_time}s")
        logger.info("=" * 60)

        return {
            "query": query,
            "results": final_results,
            "user_role": user_role,
            "authorized_chunks": len(filtered_results),
            "filtered_chunks": filtered_chunks,
            "total_results": len(raw_results),
            "average_relevance": average_score,
            "retrieval_time": retrieval_time
        }
    def search_in_document(
        self,
        query: str,
        filename: str,
        n_results: int = 5,
        relevance_threshold: Optional[float] = None,
        user_role: Optional[str] = "PUBLIC"
    ) -> Dict:

        threshold = (
            relevance_threshold
            if relevance_threshold is not None
            else self.relevance_threshold
        )

        query_embedding = self.embedding_generator.embed_text(
            query
        )

        raw_results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results * 3,
            where={
                "filename": filename
            }
        )

        filtered_results, filtered_chunks = (
            self._filter_by_access_and_relevance(
                raw_results=raw_results,
                user_role=user_role,
                threshold=threshold
            )
        )

        unique_results = []
        seen = set()

        for chunk in filtered_results:

            key = (
                chunk.get("filename"),
                chunk.get("page"),
                chunk.get("chunk_id")
            )

            if key in seen:
                continue

            seen.add(key)
            unique_results.append(chunk)

        final_results = unique_results[:n_results]

        average_score = 0.0

        if final_results:

            average_score = round(
                sum(
                    item["relevance_score"]
                    for item in final_results
                ) / len(final_results),
                3
            )

        return {
            "query": query,
            "document": filename,
            "results": final_results,
            "user_role": user_role,
            "authorized_chunks": len(filtered_results),
            "filtered_chunks": filtered_chunks,
            "total_results": len(raw_results),
            "average_relevance": average_score
        }

    def _filter_by_access_and_relevance(
        self,
        raw_results: List[Dict],
        user_role: Optional[str],
        threshold: float
    ):

        formatted = []

        filtered_chunks = 0

        for result in raw_results:

            distance = result.get("distance", 1)

            if distance > threshold:
                continue

            metadata = result.get("metadata", {})

            filename = metadata.get("filename")

            version = metadata.get("version")
            if (
                filename is None
                or version is None
                or not self.version_manager.is_latest_active_version(
                    filename,
                    version
                )
            ):
                continue
            chunk_access_level = metadata.get(
                "access_level",
                "PUBLIC"
            ).upper()
            


            if not self._user_can_access(
                chunk_access_level,
                user_role
            ):
                filtered_chunks += 1
                continue

            relevance_score = round(
                max(0.0, 1 - distance),
                4
            )

            formatted.append(
                {
                    "rank": len(formatted) + 1,
                    "chunk_id": result.get("chunk_id"),
                    "text": result.get("text"),
                    "metadata": metadata,
                    "filename": metadata.get("filename"),
                    "page": metadata.get("page"),
                    "version": metadata.get("version"),
                    "department": metadata.get("department"),
                    "access_level": chunk_access_level,
                    "distance": round(distance, 4),
                    "relevance_score": relevance_score,
                    "token_count": metadata.get(
                        "token_count",
                        0
                    ),
                    "word_count": metadata.get(
                        "word_count",
                        0
                    ),
                    "character_count": metadata.get(
                        "character_count",
                        0
                    )
                }
            )

        documents = defaultdict(list)
        for chunk in formatted:
            documents[chunk["filename"]].append(chunk)
        document_scores = []
        for filename, chunks in documents.items():
            avg_score = sum(
                c["relevance_score"] for c in chunks
            ) / len(chunks)
            document_scores.append((filename, avg_score,chunks))
        document_scores.sort(
            key=lambda x: x[1],
            reverse=True
        )
        final_chunks = []
        for _, _, chunks in document_scores:
            chunks.sort(
                key=lambda x: x["relevance_score"],
                reverse=True
            )
            final_chunks.extend(chunks)
        return final_chunks, filtered_chunks
    
    def _user_can_access(
        self,
        chunk_access_level: str,
        user_role: Optional[str]
    ) -> bool:

        if user_role is None:
            return True
        
        return (
            self.role_hierarchy.get(user_role, 0)
            >=
            self.role_hierarchy.get(chunk_access_level, 0)
        )


    def get_statistics(self) -> Dict:

        try:

            collection = self.vector_store.collection

            count = collection.count()

            return {
                "indexed_chunks": count,
                "relevance_threshold": self.relevance_threshold,
                "roles_supported": list(
                    self.role_hierarchy.keys()
                )
            }

        except Exception as e:

            logger.warning(
                f"Unable to fetch statistics: {e}"
            )

            return {
                "indexed_chunks": 0,
                "relevance_threshold": self.relevance_threshold,
                "roles_supported": list(
                    self.role_hierarchy.keys()
                )
            }

    def search_statistics(
        self,
        search_results: Dict
    ) -> Dict:

        results = search_results.get(
            "results",
            []
        )

        if not results:

            return {
                "chunks": 0,
                "avg_relevance": 0,
                "avg_tokens": 0,
                "avg_words": 0,
                "avg_characters": 0
            }

        avg_tokens = round(
            sum(
                r.get(
                    "token_count",
                    0
                )
                for r in results
            ) / len(results),
            2
        )

        avg_words = round(
            sum(
                r.get(
                    "word_count",
                    0
                )
                for r in results
            ) / len(results),
            2
        )

        avg_characters = round(
            sum(
                r.get(
                    "character_count",
                    0
                )
                for r in results
            ) / len(results),
            2
        )

        return {

            "chunks": len(results),

            "avg_relevance":
                search_results.get(
                    "average_relevance",
                    0
                ),

            "avg_tokens":
                avg_tokens,

            "avg_words":
                avg_words,

            "avg_characters":
                avg_characters,

            "retrieval_time":
                search_results.get(
                    "retrieval_time",
                    0
                ),

            "filtered_chunks":
                search_results.get(
                    "filtered_chunks",
                    0
                ),

            "authorized_chunks":
                search_results.get(
                    "authorized_chunks",
                    0
                )
        }