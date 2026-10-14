from src.vector_store import VectorStore
from config.settings import *

db = VectorStore(
    persist_dir=VECTOR_DB_PATH,
    collection_name=COLLECTION_NAME
)

results = db.collection.get(include=["metadatas"])

print("Total chunks:", len(results["metadatas"]))

for i, meta in enumerate(results["metadatas"]):
    print(f"\nChunk {i+1}")
    print(meta)