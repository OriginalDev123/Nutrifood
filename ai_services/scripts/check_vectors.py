import httpx

# Scroll through points to check if they have vectors
r = httpx.post('http://qdrant:6333/collections/nutriai_knowledge/points/scroll', json={
    'limit': 10,
    'with_vectors': True
})
data = r.json()
points = data.get('result', {}).get('points', [])
print(f'Checked {len(points)} points:')
for p in points:
    vector = p.get('vector', None)
    has_vector = vector is not None and len(vector) > 0
    print(f'  ID: {p.get("id")}')
    print(f'    Title: {p.get("payload", {}).get("title", "N/A")}')
    print(f'    Has vector: {has_vector}')
    if has_vector:
        print(f'    Vector length: {len(vector)}')
    print()
