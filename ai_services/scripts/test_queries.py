import httpx
import json

# Test câu hỏi khác
queries = [
    'Thịt bò có bao nhiêu calories?',
    'Món giàu protein là gì?',
    'Rau muống có chất gì?'
]

for q in queries:
    encoded_q = q.replace(' ', '%20')
    response = httpx.post(f'http://localhost:8001/chat/rag?question={encoded_q}', timeout=30)
    data = response.json()
    print(f'Q: {q}')
    print(f'A: {data.get("answer", "")[:200]}...')
    sources = [s.get("title", "") for s in data.get("sources", [])[:2]]
    print(f'Sources: {sources}')
    print()
