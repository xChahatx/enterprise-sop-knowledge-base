from typing import Dict, Optional
import logging
import time

from src.prompt_builder import PromptBuilder
from src.llm import LLM
from src.reranker import CrossEncoderReranker
from src.citation_builder import CitationBuilder
from src.conversation_memory import ConversationMemory
from config.settings import (
    NO_INFORMATION_MESSAGE,
    ENABLE_PARTIAL_INFORMATION_NOTICE
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:

    def __init__(
        self,
        semantic_search,
        ollama_host="http://localhost:11434",
        model="llama3.2:3b",
        temperature=0.3,
        max_tokens=500
    ):

        self.semantic_search = semantic_search
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.prompt_builder = PromptBuilder()
        self.reranker = CrossEncoderReranker()
        self.citation_builder = CitationBuilder()
        self.memory = ConversationMemory()

        self.llm = LLM(
            model=model,
            base_url=ollama_host
        )

        self.model = model

        logger.info(
            f"RAGPipeline initialized | model={model}"
        )

    def answer_question(
        self,
        question: str,
        user_role: Optional[str] = None,
        n_context_chunks: int = 3
    ) -> Dict:

        start_time = time.time()

        logger.info(
            f"Question: '{question}' | Role: {user_role}"
        )

        question = self.memory.rewrite_question(question)

        logger.info(
            f"Rewritten Question: {question}"
        )

        search_results = self.semantic_search.search(
            query=question,
            n_results=n_context_chunks * 2,
            user_role=user_role
        )

        retrieved_chunks = search_results.get(
            "results",
            []
        )

        unique_chunks = {}

        for chunk in retrieved_chunks:
            unique_chunks[
                chunk["chunk_id"]
            ] = chunk

        retrieved_chunks = list(
            unique_chunks.values()
        )

        total_chunks = search_results.get(
            "total_results",
            len(retrieved_chunks)
        )

        filtered_chunks = search_results.get(
            "filtered_chunks",
            0
        )

        restricted = filtered_chunks > 0
        hidden_chunks = filtered_chunks
        partial_information = (
            ENABLE_PARTIAL_INFORMATION_NOTICE
            and hidden_chunks > 0
             and len(retrieved_chunks) > 0
        )
        access_warning = restricted

        logger.info(
            f"Retrieved {len(retrieved_chunks)} unique chunks"
        )

        if not retrieved_chunks:

            retrieval_time = round(
                time.time() - start_time,
                3
            )

            return {
                "question": question,
                "answer": NO_INFORMATION_MESSAGE,
                "sources": [],
                "citations": [],
                "chunks_used": 0,
                "chunks_searched": total_chunks,
                "confidence": 0.0,
                "restricted": restricted,
                "filtered_chunks": filtered_chunks,
                "hidden_chunks": hidden_chunks,
                "partial_information": partial_information,
                "access_warning": None,
                "retrieval_time": retrieval_time,
                "user_role": user_role,
                "model": self.model
            }

        selected_chunks = self.reranker.rerank(
            query=question,
            search_results=retrieved_chunks,
            top_k=n_context_chunks
        )

        citations = self.citation_builder.build_citations(
            selected_chunks
        )

        prompt = self.prompt_builder.build_prompt(
            question=question,
            search_results=selected_chunks
        )

        logger.info(
            "Generating LLM response..."
        )
        answer = self.llm.generate(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        sources = []

        similarities = []
        rerank_scores = []

        total_tokens = 0
        total_words = 0
        total_characters = 0

        for chunk in selected_chunks:

            score = chunk.get(
                "relevance_score",
                0
            )

            rerank = chunk.get(
                "rerank_score",
                0
            )

            similarities.append(score)
            rerank_scores.append(rerank)

            metadata = chunk.get(
                "metadata",
                {}
            )
            logger.info("=" * 60)
            logger.info(chunk)
            logger.info(metadata)
            logger.info("=" * 60)

            token_count = chunk.get(
                "token_count",
                0
            )
            word_count = chunk.get(
                "word_count",
                0
            )

            character_count = chunk.get(
                "character_count",
                0
            )

            total_tokens += token_count
            total_words += word_count
            total_characters += character_count

            sources.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "filename": chunk.get("filename"),
                    "page": metadata.get("page"),
                    "version": metadata.get("version"),
                    "heading": metadata.get("heading"),
                    "document_type": metadata.get("document_type"),
                    "access_level": chunk.get("access_level"),
                    "department": chunk.get("department"),
                    "token_count": token_count,
                    "word_count": word_count,
                    "character_count": character_count,
                    "relevance_score": score,
                    "rerank_score": rerank
                }
            )

        confidence = (
            round(
                (
                    sum(similarities) +
                    (sum(rerank_scores) / 10)
                ) /
                (
                    len(similarities) +
                    len(rerank_scores)
                ),
                3
            )
            if similarities else 0.0
        )

        retrieval_time = round(
            time.time() - start_time,
            3
        )

        self.memory.add_turn(
            question=question,
            answer=answer
        )
        average_rerank = (
            round(
                sum(rerank_scores) /
                len(rerank_scores),
                3
            )
            if rerank_scores else 0
        )

        logger.info("=" * 70)
        logger.info(f"Confidence: {confidence}")
        logger.info(f"Average Rerank Score: {average_rerank}")
        logger.info(f"Chunks Used: {len(selected_chunks)}")
        logger.info(f"Total Tokens: {total_tokens}")
        logger.info(f"Total Words: {total_words}")
        logger.info(f"Total Characters: {total_characters}")
        logger.info(f"Retrieval Time: {retrieval_time}s")
        logger.info("=" * 70)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "citations": citations,
            "confidence": confidence,
            "user_role": user_role,
            "chunks_searched": total_chunks,
            "chunks_used": len(selected_chunks),
            "restricted": restricted,
            "filtered_chunks": filtered_chunks,
            "hidden_chunks": hidden_chunks,
            "partial_information": partial_information,
            "access_warning": access_warning,
            "retrieval_time": retrieval_time,
            "model": self.model,
            "analytics": {
                "total_tokens": total_tokens,
                "total_words": total_words,
                "total_characters": total_characters,
                "average_rerank_score": average_rerank
            }
        }