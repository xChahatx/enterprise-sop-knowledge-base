"""
Test script for Embeddings
"""

from src.doc_parser import DocumentParser
from src.text_chunker import TextChunker
from src.embeddings import EmbeddingGenerator

# Initialize all modules
parser = DocumentParser()
chunker = TextChunker(chunk_size=300, overlap=50)
embedding_gen = EmbeddingGenerator()

# Step 1: Parse PDF
text, metadata = parser.parse('data/raw/sop_sample_parse.pdf')
print(f"✅ Parsed: {metadata['filename']}\n")

# Step 2: Chunk text
chunks = chunker.chunk_text(text, metadata)
print(f"✅ Created {len(chunks)} chunks\n")

# Step 3: Generate embeddings
print("Generating embeddings (this may take a minute)...\n")
embedded_chunks = embedding_gen.embed_chunks(chunks)

print("="*60)
print(f"✅ Successfully embedded {len(embedded_chunks)} chunks!\n")

# Show first chunk details
first_chunk = embedded_chunks[0]
print(f"First chunk preview:")
print(f"  Chunk ID: {first_chunk['chunk_id']}")
print(f"  Text: {first_chunk['text'][:100]}...")
print(f"  Embedding size: {len(first_chunk['embedding'])} dimensions")
print(f"  First 5 embedding values: {first_chunk['embedding'][:5]}")