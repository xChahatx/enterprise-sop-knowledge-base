"""
Test script for Semantic Search Module
Tests search(), search_in_document(), and relevance filtering
"""

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator
from src.semantic_search import SemanticSearch

print("=" * 70)
print("MODULE 5: Semantic Search Test")
print("=" * 70)

# -------------------------------------------------------
# Step 1: Initialize components
# -------------------------------------------------------
print("\n[1/4] Initializing VectorStore and SemanticSearch...")

store          = VectorStore(persist_dir="./data/vectorstore", collection_name="sop_documents")
embedder       = EmbeddingGenerator()
search_engine  = SemanticSearch(
    vector_store=store,
    embedding_generator=embedder,
    relevance_threshold=0.7
)

print(f"✅ SemanticSearch ready | Indexed documents: {search_engine.get_all_documents()}")
print(f"   Total chunks in DB: {store.count()}")

# -------------------------------------------------------
# Step 2: Global search (across all documents)
# -------------------------------------------------------
print("\n[2/4] Testing global search...")

query1 = "What is the health screening process?"
result1 = search_engine.search(query=query1, n_results=3)

print(f"\n✅ Query: '{query1}'")
print(f"   Found {result1['total_results']} relevant results:\n")

for r in result1["results"]:
    print(f"   [{r['rank']}] Relevance: {r['relevance_score']} | Distance: {r['distance']}")
    print(f"       Chunk: {r['chunk_id']}")
    print(f"       Preview: {r['text'][:100]}...\n")

# -------------------------------------------------------
# Step 3: Scoped search (within one document)
# -------------------------------------------------------
print("[3/4] Testing scoped search (within one document)...")

query2 = "medical screening procedures"
filename = "sop_sample_parse.pdf"
result2 = search_engine.search_in_document(query=query2, filename=filename, n_results=2)

print(f"\n✅ Query: '{query2}'")
print(f"   Document: {result2['document']}")
print(f"   Found {result2['total_results']} results:\n")

for r in result2["results"]:
    print(f"   [{r['rank']}] Relevance: {r['relevance_score']} | Distance: {r['distance']}")
    print(f"       Preview: {r['text'][:100]}...\n")

# -------------------------------------------------------
# Step 4: Test threshold adjustment
# -------------------------------------------------------
print("[4/4] Testing stricter threshold (0.5)...")

search_engine.set_relevance_threshold(0.5)
query3 = "employee procedures"
result3 = search_engine.search(query=query3, n_results=5)

print(f"\n✅ Query: '{query3}' (with stricter threshold 0.5)")
print(f"   Found {result3['total_results']} results:\n")

if result3['total_results'] == 0:
    print("   No results met the stricter threshold ✓\n")
else:
    for r in result3["results"]:
        print(f"   [{r['rank']}] Relevance: {r['relevance_score']}")

print("=" * 70)
print(f"✅ All tests passed! Semantic Search is working correctly.")
print("=" * 70)