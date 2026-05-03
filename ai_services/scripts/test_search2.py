import sys
sys.path.insert(0, '/app')

from app.services.retrieval_service import RetrievalService
from app.services.local_embedding_service import get_local_embedding_service

# Init
embedder = get_local_embedding_service()
retrieval = RetrievalService('http://qdrant:6333', embedder)

# Test search
test_queries = ['bánh mì', 'phở', 'thịt bò', 'protein']

for q in test_queries:
    results = retrieval.search(q, top_k=3, score_threshold=0.2)
    print(f'Query: "{q}" -> {len(results)} results')
    for r in results[:3]:
        print(f'  - {r.get("title", "")} (score: {r.get("score", 0):.3f})')
    print()
