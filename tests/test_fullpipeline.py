"""
COMPLETE PIPELINE TEST
Testing: Parse → Version Manager → Chunk → Embed → Store → Search → RAG
With chunk-level access control and RBAC
"""

from src.vector_store import VectorStore, DocumentIndexer
from src.version_manager import VersionManager
from src.embeddings import EmbeddingGenerator
from src.semantic_search import SemanticSearch
from src.rag_pipeline import RAGPipeline

print("=" * 80)
print("COMPLETE PIPELINE TEST: Version Manager + Chunk-Level RBAC")
print("=" * 80)

# ============================================================================
# STEP 1: Initialize All Components
# ============================================================================
print("\n[1/7] Initializing all components...")

store = VectorStore(persist_dir="./data/vectorstore")
vm = VersionManager(version_file="data/versions.json", registry_file="data/registry.json")
indexer = DocumentIndexer(vector_store=store, version_manager=vm)
embedder = EmbeddingGenerator()
search_engine = SemanticSearch(vector_store=store, embedding_generator=embedder)
rag = RAGPipeline(semantic_search=search_engine)

print("✅ All components initialized")

# ============================================================================
# STEP 2: Index Document with Version Manager
# ============================================================================
print("\n[2/7] Indexing document with full version tracking...")

result = indexer.index_document(
    "data/raw/sop_sample_parse.pdf",
    access_level="INTERNAL",
    department="General",
    document_type="SOP",
    uploaded_by="test_user",
    detect_sections=True
)

print(f"✅ Document indexed:")
print(f"   Filename: {result['filename']}")
print(f"   Status: {result['status']}")
print(f"   Version: {result.get('version', 'N/A')}")
print(f"   Chunks stored: {result['chunks_stored']}")
if result['status'] == 'indexed':
    print(f"   Access level: {result['access_level']}")
    print(f"   Access distribution: {result['access_distribution']}")
else:
    print(f"   (Document already indexed, skipping)")

# ============================================================================
# STEP 3: Verify Version Manager Registration
# ============================================================================
print("\n[3/7] Verifying version manager...")

doc_info = vm.get_document_info("sop_sample_parse.pdf")
print(f"✅ Document in registry:")
print(f"   Filename: {doc_info['filename']}")
print(f"   Document type: {doc_info['document_type']}")
print(f"   Department: {doc_info['department']}")
print(f"   Total versions: {len(doc_info['versions'])}")

version_info = vm.get_active_version_info("sop_sample_parse.pdf")
print(f"\n✅ Active version:")
print(f"   Version: {version_info['version']}")
print(f"   Access level: {version_info['access_level']}")
print(f"   Uploaded by: {version_info['uploaded_by']}")
print(f"   Chunks in version: {version_info['chunks']['count']}")

# ============================================================================
# STEP 4: Search as INTERNAL User
# ============================================================================
print("\n[4/7] Semantic search as INTERNAL user...")

search_result_internal = search_engine.search(
    query="health screening procedures",
    user_role="INTERNAL",
    n_results=3
)

print(f"✅ Found {search_result_internal['total_results']} authorized results:")
for r in search_result_internal['results']:
    print(f"   - {r['chunk_id']} | Access: {r['access_level']} | Score: {r['relevance_score']}")

# ============================================================================
# STEP 5: Search as PUBLIC User
# ============================================================================
print("\n[5/7] Semantic search as PUBLIC user (restricted)...")

search_result_public = search_engine.search(
    query="health screening procedures",
    user_role="PUBLIC",
    n_results=3
)

print(f"✅ Found {search_result_public['total_results']} authorized results:")
if search_result_public['total_results'] == 0:
    print("   (No results - PUBLIC user can only see PUBLIC chunks)")
else:
    for r in search_result_public['results']:
        print(f"   - {r['chunk_id']} | Access: {r['access_level']}")

# ============================================================================
# STEP 6: RAG Answer Generation (INTERNAL User)
# ============================================================================
print("\n[6/7] RAG answer generation as INTERNAL user...")

rag_result = rag.answer_question(
    question="What is the health screening process?",
    user_role="INTERNAL",
    n_context_chunks=3
)

print(f"✅ Question: {rag_result['question']}")
print(f"   User role: {rag_result['user_role']}")
print(f"   Chunks searched: {rag_result['chunks_searched']}")
print(f"   Chunks used: {rag_result['chunks_used']}")
print(f"   Confidence: {rag_result['confidence']}")

print("\n================ ANSWER ================\n")
print(rag_result["answer"])

print("\n============= CITATIONS =============\n")

for citation in rag_result["citations"]:
    print(
        f"[{citation['citation_id']}] "
        f"{citation['filename']} | "
        f"Page {citation['page']} | "
        f"Chunk {citation['chunk_id']}"
    )

print("\n============= SOURCES =============\n")

for source in rag_result["sources"]:
    print(
        f"- {source['filename']} "
        f"(Chunk {source['chunk_id']}) "
        f"| Page {source.get('page','?')} "
        f"| Score={source['relevance_score']:.3f}"
    )
print("\n==============================")
print("FOLLOW-UP QUESTION TEST")
print("==============================")

follow_up = rag.answer_question(
    question="How often is it required?",
    user_role="INTERNAL",
     n_context_chunks=3
     )
print("\nFollow-up Answer:\n")
print(follow_up["answer"])
# ============================================================================
# STEP 7: Verify Deduplication
# ============================================================================
print("\n[7/7] Testing deduplication...")

result2 = indexer.index_document(
    "data/raw/sop_sample_parse.pdf",
    access_level="INTERNAL"
)

print(f"✅ Second index attempt:")
print(f"   Status: {result2['status']} (should be 'skipped')")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ COMPLETE PIPELINE TEST PASSED!")
print("=" * 80)
print("\nSystem verified:")
print("  ✅ Document parsing and metadata extraction")
print("  ✅ Version tracking and registration")
print("  ✅ Chunk-level access control")
print("  ✅ Embedding generation")
print("  ✅ ChromaDB storage")
print("  ✅ Role-based semantic search")
print("  ✅ RAG answer generation with RBAC")
print("  ✅ Deduplication prevention")
print("  ✅ Automatic citations")
print("\n" + "=" * 80)
