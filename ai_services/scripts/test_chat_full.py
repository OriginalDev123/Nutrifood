"""
Test chat with FULL answer output
"""
import httpx
import json

BASE_URL = "http://localhost:8001"

test_cases = [
    "Gợi ý bữa ăn sáng",
    "Thịt bò có bao nhiêu calories?",
    "Món ăn nào tốt cho giảm cân?",
    "Nấu món gì với thịt bò?"
]

for question in test_cases:
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print('='*60)
    
    response = httpx.post(
        f"{BASE_URL}/chat/ask",
        json={"question": question, "top_k": 3, "score_threshold": 0.20},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nANSWER:\n{data.get('answer', '')}")
        print(f"\nSOURCES: {data.get('sources', [])}")
        print(f"RETRIEVED: {data.get('retrieved_docs', 0)}")
    else:
        print(f"ERROR: {response.text}")
