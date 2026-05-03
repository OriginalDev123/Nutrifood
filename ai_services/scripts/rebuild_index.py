import httpx

# Check Qdrant version to understand available endpoints
r = httpx.get('http://qdrant:6333/')
print(f"Qdrant version info: {r.json()}")

# Check current index status
r2 = httpx.get('http://qdrant:6333/collections/nutriai_knowledge')
data = r2.json()
result = data.get('result', {})
print(f'\nCollection status:')
print(f'  Points: {result.get("points_count", 0)}')
print(f'  Indexed vectors: {result.get("indexed_vectors_count", 0)}')
print(f'  Optimizer status: {result.get("optimizer_status", "N/A")}')
print(f'  Status: {result.get("status", "N/A")}')

# The issue is that points exist but vectors are not indexed
# Let's try to recreate the collection
print('\n\nTo fix this, we need to recreate the collection with indexing.')
print('Run: docker-compose down -v && docker-compose up -d')
print('\nOr we can try to use the optimize endpoint...')
