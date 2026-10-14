from src.vector_store import VectorStore

vs = VectorStore()

results = vs.collection.query(
    query_texts=["standard operating procedure"],
    n_results=5
)

print(results)