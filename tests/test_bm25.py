from src.bm25_search import BM25Search

chunks = [

    {
        "chunk_id":"1",
        "text":"Medical screening policy for firefighters."
    },

    {
        "chunk_id":"2",
        "text":"Vacation leave policy."
    },

    {
        "chunk_id":"3",
        "text":"OSHA 1910.134 respiratory protection."
    }

]

bm = BM25Search()

bm.build_index(chunks)

results = bm.search(
    "OSHA 1910.134",
    top_k=3
)

for r in results:

    print(r["chunk_id"], r["bm25_score"])