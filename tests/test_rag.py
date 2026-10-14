from src.vector_store import VectorStore
from src.rag_pipeline import RAGPipeline

print("=" * 60)
print("RAG PIPELINE TEST")
print("=" * 60)

vector_store = VectorStore()

rag = RAGPipeline(vector_store)

while True:

    question = input("\nAsk a question (type exit to quit): ")

    if question.lower() == "exit":
        break

    response = rag.answer_question(
        question,
        user_access_level="internal"
    )

    print("\nANSWER\n")
    print(response["answer"])

    print("\nSources:")

    for source in response["sources"]:
        print("-", source)