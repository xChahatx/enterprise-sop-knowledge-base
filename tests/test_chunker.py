"""
Test script for Text Chunker
"""

from src.doc_parser import DocumentParser
from src.text_chunker import TextChunker

# Initialize parser and chunker
parser = DocumentParser()
chunker = TextChunker(chunk_size=300, overlap=50)

# Parse PDF
text, metadata = parser.parse('data/raw/sop_sample_parse.pdf')

print(f"Extracted text length: {len(text)} characters")
print(f"File: {metadata['filename']}\n")

# Chunk the text
chunks = chunker.chunk_text(text, metadata)

print(f"Number of chunks created: {len(chunks)}")
print("="*60)

# Show first 3 chunks as preview
for i, chunk in enumerate(chunks[:3]):
    print(f"\nChunk {i+1}:")
    print(f"  Chunk ID: {chunk['chunk_id']}")
    print(f"  Tokens: {chunk['token_count']}")
    print(f"  Text preview (first 150 chars):")
    print(f"  {chunk['text'][:150]}...\n")

print("="*60)
print(f"✅ All {len(chunks)} chunks created successfully!")