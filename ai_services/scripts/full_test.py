"""
Comprehensive test of AI Service
Tests both chatbot and meal planning endpoints
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8001"

def test_chat_endpoint():
    """Test chat/ask endpoint"""
    print("\n" + "="*60)
    print("TESTING CHAT ENDPOINT (/chat/ask)")
    print("="*60)
    
    test_cases = [
        {
            "name": "Gợi ý bữa sáng",
            "question": "Gợi ý bữa ăn sáng"
        },
        {
            "name": "Hỏi về thịt bò",
            "question": "Thịt bò có bao nhiêu calories?"
        },
        {
            "name": "Món giảm cân",
            "question": "Món ăn nào tốt cho giảm cân?"
        },
        {
            "name": "Nấu với thịt bò",
            "question": "Nấu món gì với thịt bò?"
        },
        {
            "name": "Hỏi về rau muống",
            "question": "Rau muống có chất gì?"
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n--- Test: {test['name']} ---")
        print(f"Question: {test['question']}")
        
        try:
            start = time.time()
            response = httpx.post(
                f"{BASE_URL}/chat/ask",
                json={
                    "question": test["question"],
                    "top_k": 3,
                    "score_threshold": 0.20
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed*1000:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                retrieved = data.get("retrieved_docs", 0)
                
                print(f"Retrieved docs: {retrieved}")
                print(f"Sources count: {len(sources)}")
                if sources:
                    print(f"  Sources: {[s.get('title', '') for s in sources[:3]]}")
                print(f"Answer (first 300 chars): {answer[:300]}")
                
                # Check if answer is meaningful
                if "không có đủ thông tin" in answer.lower() or "tôi không có" in answer.lower():
                    print("⚠️ WARNING: Answer says no information available")
                elif len(answer) < 20:
                    print("⚠️ WARNING: Answer is too short")
                    
                results.append({
                    "name": test["name"],
                    "question": test["question"],
                    "status": "OK",
                    "retrieved": retrieved,
                    "answer_length": len(answer)
                })
            else:
                print(f"❌ ERROR: {response.text}")
                results.append({
                    "name": test["name"],
                    "question": test["question"],
                    "status": "ERROR",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({
                "name": test["name"],
                "question": test["question"],
                "status": "EXCEPTION",
                "error": str(e)
            })
    
    return results

def test_meal_planning_endpoint():
    """Test meal planning endpoint"""
    print("\n" + "="*60)
    print("TESTING MEAL PLANNING ENDPOINT (/meal-planning)")
    print("="*60)
    
    # Check if endpoint exists
    try:
        # Try to get meal planning health/info
        response = httpx.get(f"{BASE_URL}/meal-planning/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {str(e)}")
    
    # Test meal planning generation
    print("\n--- Test: Generate Meal Plan ---")
    test_prompts = [
        "Tạo kế hoạch ăn uống cho 1 ngày với 2000 calories",
        "Gợi ý thực đơn giảm cân 7 ngày",
        "Lên kế hoạch ăn uống cho người tập gym"
    ]
    
    results = []
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        
        try:
            start = time.time()
            response = httpx.post(
                f"{BASE_URL}/meal-planning/generate",
                json={
                    "prompt": prompt,
                    "days": 3
                },
                timeout=60
            )
            elapsed = time.time() - start
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed*1000:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                if "meal_plan" in data:
                    print(f"Meal plan generated: {type(data['meal_plan'])}")
                    if isinstance(data['meal_plan'], dict):
                        print(f"  Keys: {list(data['meal_plan'].keys())}")
                print(f"Response preview: {str(data)[:500]}")
                results.append({
                    "prompt": prompt,
                    "status": "OK",
                    "has_data": bool(data.get('meal_plan'))
                })
            else:
                print(f"❌ ERROR: {response.text[:500]}")
                results.append({
                    "prompt": prompt,
                    "status": "ERROR",
                    "error": response.text[:200]
                })
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({
                "prompt": prompt,
                "status": "EXCEPTION",
                "error": str(e)
            })
    
    return results

def main():
    print("="*60)
    print("COMPREHENSIVE AI SERVICE TEST")
    print("="*60)
    
    # Check service health
    print("\nChecking service health...")
    try:
        health = httpx.get(f"{BASE_URL}/health", timeout=10)
        print(f"Health status: {health.status_code}")
        if health.status_code == 200:
            print(json.dumps(health.json(), indent=2))
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        print("Service may not be running!")
        return
    
    # Run tests
    chat_results = test_chat_endpoint()
    meal_results = test_meal_planning_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    print("\nChat Tests:")
    for r in chat_results:
        status_icon = "✅" if r["status"] == "OK" else "❌"
        print(f"  {status_icon} {r['name']}: {r['status']}")
        if r["status"] == "OK":
            print(f"      Retrieved: {r['retrieved']}, Answer length: {r['answer_length']}")
    
    print("\nMeal Planning Tests:")
    for r in meal_results:
        status_icon = "✅" if r.get("has_data") else "❌"
        print(f"  {status_icon} {r['prompt'][:50]}...")
        print(f"      Status: {r['status']}")

if __name__ == "__main__":
    main()
