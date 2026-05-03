import sys
sys.path.insert(0, '/app')

from app.services.retrieval_service import RetrievalService
from app.services.local_embedding_service import get_local_embedding_service

# Init
embedder = get_local_embedding_service()
retrieval = RetrievalService('http://qdrant:6333', embedder)

# Check what breakfast foods exist in database
test_queries = ['bánh mì', 'xôi', 'bún', 'cháo', 'mì', 'bánh bao', 'bánh cuốn']

for q in test_queries:
    results = retrieval.search(q, top_k=3, score_threshold=0.15)
    print(f'Query: "{q}" -> {len(results)} results')
    for r in results[:3]:
        print(f'  - {r.get("title", "")} (score: {r.get("score", 0):.3f})')
    print()
