import chromadb
from pathlib import Path
from typing import List, Dict, Optional
import logging
import time

from config.settings import DEFAULT_DEPARTMENT_OWNER
from src.doc_parser import DocumentParser
from src.text_chunker import TextChunker
from src.embeddings import EmbeddingGenerator
from src.version_manager import VersionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:

    def __init__(
        self,
        persist_dir: str = "./data/vectorstore",
        collection_name: str = "sop_documents"
    ):

        self.client = chromadb.PersistentClient(
            path=persist_dir
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine"
            }
        )

        self.collection_name = collection_name

        logger.info(
            f"VectorStore initialized | {collection_name}"
        )

        logger.info(
            f"Collection contains {self.collection.count()} chunks"
        )

    def add_chunks(
        self,
        embedded_chunks: List[Dict]
    ):

        if not embedded_chunks:

            logger.warning(
                "No chunks received."
            )

            return

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        total_tokens = 0
        total_words = 0
        total_characters = 0

        for chunk in embedded_chunks:

            ids.append(
                chunk["chunk_id"]
            )

            embeddings.append(
                chunk["embedding"]
            )

            documents.append(
                chunk["text"]
            )

            metadata = self._flatten_metadata(
                chunk["metadata"]
            )

            metadata["chunk_id"] = chunk["chunk_id"]

            metadata["chunk_number"] = chunk.get(
                "chunk_number",
                0
            )

            metadata["total_chunks"] = chunk.get(
                "total_chunks",
                0
            )

            metadata["page"] = chunk.get(
                "page",
                metadata.get("page", 1)
            )

            metadata["heading"] = chunk.get(
                "heading",
                ""
            )

            metadata["is_table"] = chunk.get(
                "is_table",
                False
            )

            metadata["token_count"] = chunk.get(
                "token_count",
                0
            )

            metadata["word_count"] = chunk["metadata"].get(
                "word_count",
                0
            )

            metadata["character_count"] = chunk["metadata"].get(
                "character_count",
                0
            )

            total_tokens += metadata["token_count"]
            total_words += metadata["word_count"]
            total_characters += metadata["character_count"]

            metadatas.append(
                metadata
            )

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.info("=" * 70)
        logger.info(f"Stored {len(ids)} chunks")
        logger.info(f"Total Tokens : {total_tokens}")
        logger.info(f"Total Words : {total_words}")
        logger.info(f"Total Characters : {total_characters}")
        logger.info("=" * 70)

    def query(
        self,
        query_embedding,
        n_results=5,
        where=None
    ):

        start = time.time()

        query_args = {

            "query_embeddings": [query_embedding],

            "n_results": n_results,

            "include": [

                "documents",

                "metadatas",

                "distances"

            ]
        }

        if where:

            query_args["where"] = where

        results = self.collection.query(
            **query_args
        )

        output = []

        if len(results["ids"]) == 0:

            return output

        for i in range(
            len(results["ids"][0])
        ):

            metadata = results["metadatas"][0][i]

            output.append({

                "chunk_id":
                    results["ids"][0][i],

                "text":
                    results["documents"][0][i],

                "metadata":
                    metadata,

                "distance":
                    results["distances"][0][i],

                "filename":
                    metadata.get("filename"),

                "version":
                    metadata.get("version"),

                "page":
                    metadata.get("page"),

                "departments":
                    metadata.get("departments"),

                "access_level":
                    metadata.get("access_level"),

                "heading":
                    metadata.get("heading"),

                "is_table":
                    metadata.get(
                        "is_table",
                        False
                    ),

                "token_count":
                    metadata.get(
                        "token_count",
                        0
                    ),

                "word_count":
                    metadata.get(
                        "word_count",
                        0
                    ),

                "character_count":
                    metadata.get(
                        "character_count",
                        0
                    )
            })

        logger.info(
            f"Retrieved {len(output)} chunks "
            f"in {round(time.time()-start,3)} sec"
        )

        return output
    def delete_document(
        self,
        filename: str
    ):

        self.collection.delete(
            where={
                "filename": filename
            }
        )

        logger.info(
            f"Deleted chunks for {filename}"
        )

    def get_all_documents(
        self
    ):

        results = self.collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in results["metadatas"]:

            if metadata is None:
                continue

            filename = metadata.get(
                "filename"
            )

            if not filename:
                continue

            if filename not in documents:

                documents[filename] = {

                    "filename":
                        filename,

                    "version":
                        metadata.get(
                            "version"
                        ),

                    "departments":
                        metadata.get(
                            "departments"
                        ),

                    "access_level":
                        metadata.get(
                            "access_level"
                        ),

                    "chunks":
                        0,

                    "tokens":
                        0,

                    "words":
                        0,

                    "characters":
                        0
                }

            documents[filename]["chunks"] += 1

            documents[filename]["tokens"] += metadata.get(
                "token_count",
                0
            )

            documents[filename]["words"] += metadata.get(
                "word_count",
                0
            )

            documents[filename]["characters"] += metadata.get(
                "character_count",
                0
            )

        return list(
            documents.values()
        )

    def count(
        self
    ):

        return self.collection.count()

    def get_collection_statistics(
        self
    ):

        docs = self.get_all_documents()

        total_documents = len(docs)

        total_chunks = self.count()

        total_tokens = sum(
            d["tokens"]
            for d in docs
        )

        total_words = sum(
            d["words"]
            for d in docs
        )

        total_characters = sum(
            d["characters"]
            for d in docs
        )

        estimated_storage_bytes = (
            total_characters * 2
        )

        estimated_storage_mb = round(
            estimated_storage_bytes /
            (1024 * 1024),
            4
        )

        return {

            "documents":
                total_documents,

            "chunks":
                total_chunks,

            "tokens":
                total_tokens,

            "words":
                total_words,

            "characters":
                total_characters,

            "estimated_storage_mb":
                estimated_storage_mb
        }

    def _flatten_metadata(
        self,
        metadata: Dict
    ):

        flat = {}

        for key, value in metadata.items():

            if isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool
                )
            ):

                flat[key] = value

            elif value is None:

                flat[key] = ""

            else:

                flat[key] = str(value)

        return flat
class DocumentIndexer:

    def __init__(
        self,
        vector_store: VectorStore,
        version_manager: VersionManager,
        chunk_size: int = 300,
        overlap: int = 50
    ):

        self.vector_store = vector_store
        self.version_manager = version_manager

        self.parser = DocumentParser()

        self.chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=overlap
        )

        self.embedder = EmbeddingGenerator()

        logger.info(
            "DocumentIndexer initialized."
        )

    def index_document(
        self,
        file_path: str,
        access_level: str = "INTERNAL",
        departments: List[str] = None,
        department_owner: str = "Admin",
        document_type: str = "SOP",
        uploaded_by: str = "System",
        detect_sections: bool = True,
        chunk_overrides=None,
        force=False
    ):

        start_time = time.time()
        if departments is None:
            departments = ["General"]

        file_path = Path(file_path)

        logger.info(
            f"Indexing {file_path.name}"
        )

        text, metadata = self.parser.parse(
            str(file_path)
        )

        file_hash = metadata["file_hash"]

        if (
            self.version_manager.document_exists(file_hash)
            and not force
        ):

            existing = self.version_manager.get_document_by_hash(
                file_hash
            )

            logger.info(
                "Duplicate document skipped."
            )

            return {

                "status":
                    "skipped",

                "filename":
                    metadata["filename"],

                "version":
                    existing["version"],

                "chunks_stored":
                    0,

                "file_hash":
                    file_hash
            }

        metadata = self.version_manager.register_document(

            metadata,

            access_level=access_level,

            departments=departments,

            department_owner=department_owner,

            document_type=document_type,

            uploaded_by=uploaded_by

        )

        chunks = self.chunker.chunk_text(

            text=text,

            metadata=metadata,

            detect_sections=detect_sections,

            chunk_overrides=chunk_overrides

        )

        total_chunks = len(chunks)

        page_map = metadata.get(
            "page_map",
            []
        )

        total_tokens = 0
        total_words = 0
        total_characters = 0

        for index, chunk in enumerate(chunks):

            chunk["chunk_number"] = index + 1

            chunk["total_chunks"] = total_chunks

            chunk["page"] = None

            chunk["heading"] = ""

            chunk["is_table"] = (
                "TABLE_START" in chunk["text"]
                and
                "TABLE_END" in chunk["text"]
            )

            for page in page_map:

                if chunk["text"][:150] in page["text"]:

                    chunk["page"] = page["page"]

                    break

            token_count = chunk.get(
                "token_count",
                0
            )

            word_count = len(
                chunk["text"].split()
            )

            character_count = len(
                chunk["text"]
            )

            chunk["metadata"]["word_count"] = word_count
            chunk["metadata"]["character_count"] = character_count

            total_tokens += token_count
            total_words += word_count
            total_characters += character_count

        logger.info(
            "=" * 70
        )

        logger.info(
            f"Prepared {total_chunks} chunks"
        )

        logger.info(
            f"Total Tokens : {total_tokens}"
        )

        logger.info(
            f"Total Words : {total_words}"
        )

        logger.info(
            f"Total Characters : {total_characters}"
        )

        logger.info(
            "=" * 70
        )

        embedded_chunks = self.embedder.embed_chunks(
            chunks
        )
        self.vector_store.add_chunks(
            embedded_chunks
        )

        self.version_manager.register_chunks_for_version(

            filename=metadata["filename"],

            version=metadata["version"],

            chunk_ids=[
                chunk["chunk_id"]
                for chunk in chunks
            ],

            chunk_count=total_chunks
        )

        access_distribution = {}

        for chunk in chunks:

            level = chunk["metadata"].get(
                "access_level",
                "UNKNOWN"
            )

            access_distribution[level] = (
                access_distribution.get(level, 0) + 1
            )

        indexing_time = round(
            time.time() - start_time,
            2
        )

        average_tokens = round(
            total_tokens / total_chunks,
            2
        ) if total_chunks else 0

        average_words = round(
            total_words / total_chunks,
            2
        ) if total_chunks else 0

        average_characters = round(
            total_characters / total_chunks,
            2
        ) if total_chunks else 0

        estimated_storage_kb = round(
            (total_characters * 2) / 1024,
            2
        )

        estimated_storage_mb = round(
            estimated_storage_kb / 1024,
            4
        )

        logger.info("=" * 70)

        logger.info(
            f"Finished indexing {metadata['filename']}"
        )

        logger.info(
            f"Chunks : {total_chunks}"
        )

        logger.info(
            f"Tokens : {total_tokens}"
        )

        logger.info(
            f"Words : {total_words}"
        )

        logger.info(
            f"Characters : {total_characters}"
        )

        logger.info(
            f"Average Tokens/Chunk : {average_tokens}"
        )

        logger.info(
            f"Average Words/Chunk : {average_words}"
        )

        logger.info(
            f"Average Characters/Chunk : {average_characters}"
        )

        logger.info(
            f"Estimated Storage : {estimated_storage_mb} MB"
        )

        logger.info(
            f"Indexing Time : {indexing_time} sec"
        )

        logger.info(
            f"Access Distribution : {access_distribution}"
        )

        logger.info("=" * 70)

        return {

            "status": "indexed",

            "filename": metadata["filename"],

            "version": metadata["version"],

            "chunks_stored": total_chunks,

            "departments": metadata["departments"],
            "department_owner": metadata["department_owner"],

            "access_level": metadata["access_level"],
            "document_type": metadata["document_type"],
            "uploaded_by": metadata["uploaded_by"],
            "created_at": metadata["created_at"],

            "file_hash": metadata["file_hash"],

            "tokens": total_tokens,

            "words": total_words,

            "characters": total_characters,

            "average_tokens": average_tokens,

            "average_words": average_words,

            "average_characters": average_characters,

            "estimated_storage_mb": estimated_storage_mb,

            "indexing_time": indexing_time,

            "access_distribution": access_distribution

        }

    def reindex_document(
        self,
        file_path: str,
        access_level: str = "INTERNAL",
        departments: List[str] = None,
        department_owner: str = DEFAULT_DEPARTMENT_OWNER,
        document_type: str = "SOP",
        uploaded_by: str = "System",
        detect_sections: bool = True,
        chunk_overrides=None
    ):

        file_path = Path(file_path)

        logger.info(
            f"Reindexing {file_path.name}"
        )

        self.vector_store.delete_document(
            file_path.name
        )

        result = self.index_document(
            file_path=str(file_path),
            access_level=access_level,
            departments=departments,
            department_owner=department_owner,
            document_type=document_type,
            uploaded_by=uploaded_by,
            detect_sections=detect_sections,
            chunk_overrides=chunk_overrides,
            force=True
        )

        result["status"] = "reindexed"

        logger.info(
            f"Reindexed {file_path.name} successfully."
        )

        return result
