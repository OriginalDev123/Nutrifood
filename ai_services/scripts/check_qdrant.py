import httpx

# Get collection info
r = httpx.get('http://qdrant:6333/collections/nutriai_knowledge')
data = r.json()
print('Collection info:')
print(f'  Points count: {data.get("result", {}).get("points_count", 0)}')
print(f'  Vectors count: {data.get("result", {}).get("indexed_vectors_count", 0)}')

# Try to scroll through documents
r2 = httpx.post('http://qdrant:6333/collections/nutriai_knowledge/points/scroll', json={
    'limit': 30
})
data2 = r2.json()
points = data2.get('result', {}).get('points', [])
print(f'\nScrolled {len(points)} points:')
for p in points[:30]:
    payload = p.get('payload', {})
    title = payload.get('title', 'N/A')
    source = payload.get('source', 'N/A')
    print(f'  - {title} (source: {source})')
