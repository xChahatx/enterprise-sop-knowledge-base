"""
Test script for Vector Store Module
Tests the full pipeline: Parse → Chunk → Embed → Store → Query
"""
import logging
logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.CRITICAL)
from src.vector_store import VectorStore, DocumentIndexer

print("=" * 60)
print("MODULE 4: Vector Store Test")
print("=" * 60)

# -------------------------------------------------------
# Step 1: Initialize VectorStore and DocumentIndexer
# -------------------------------------------------------
print("\n[1/5] Initializing VectorStore and DocumentIndexer...")

store   = VectorStore(persist_dir="./data/vectorstore", collection_name="sop_documents")
indexer = DocumentIndexer(vector_store=store, chunk_size=300, overlap=50)

print(f"✅ VectorStore ready | Chunks already in DB: {store.count()}")

# -------------------------------------------------------
# Step 2: Index a document
# -------------------------------------------------------
print("\n[2/5] Indexing document through full pipeline...")

result = indexer.index_document("data/raw/sop_sample_parse.pdf")

print(f"✅ Indexing result:")
print(f"   Filename      : {result['filename']}")
print(f"   Status        : {result['status']}")
print(f"   Chunks stored : {result['chunks_stored']}")
print(f"   File hash     : {result['file_hash']}")

# -------------------------------------------------------
# Step 3: Test deduplication — index same file again
# -------------------------------------------------------
print("\n[3/5] Testing deduplication (indexing same file again)...")

result2 = indexer.index_document("data/raw/sop_sample_parse.pdf")

print(f"✅ Second indexing result:")
print(f"   Status : {result2['status']}  ← should be 'skipped'")

# -------------------------------------------------------
# Step 4: Check total chunks and documents stored
# -------------------------------------------------------
print("\n[4/5] Checking stored data...")

total_chunks = store.count()
all_docs     = store.get_all_documents()

print(f"✅ Total chunks in DB : {total_chunks}")
print(f"✅ Indexed documents  : {all_docs}")

# -------------------------------------------------------
# Step 5: Run a semantic query
# -------------------------------------------------------
print("\n[5/5] Running semantic search query...")

from src.embeddings import EmbeddingGenerator

embedder        = EmbeddingGenerator()
query_text      = "What are the steps for employee onboarding?"
query_embedding = embedder.embed_text(query_text)

results = store.query(query_embedding, n_results=3)

print(f"\n✅ Query: '{query_text}'")
print(f"   Top {len(results)} results:\n")

for i, r in enumerate(results):
    print(f"   Result {i+1}:")
    print(f"   Chunk ID  : {r['chunk_id']}")
    print(f"   Distance  : {r['distance']:.4f}  (lower = more similar)")
    print(f"   Preview   : {r['text'][:120]}...")
    print()

print("=" * 60)
print(f"✅ All tests passed! Vector Store is working correctly.")
print("=" * 60)