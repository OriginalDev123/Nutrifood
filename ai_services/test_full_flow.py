"""
Test full flow: Backend -> AI Service
"""
import httpx
import json

BACKEND_URL = "http://backend:8000"  # Docker internal URL
AI_URL = "http://localhost:8001"

print("=" * 70)
print("TESTING FULL MEAL PLANNING FLOW")
print("=" * 70)

# 1. Test AI Service directly
print("\n[1] Testing AI Service directly...")
try:
    response = httpx.post(
        f"{AI_URL}/meal-planning/generate",
        json={
            "daily_calorie_target": 2000,
            "days": 1,
            "goal_type": "maintain",
            "language": "vi",
            "health_profile": {
                "health_conditions": ["tiểu đường type 2"],
                "food_allergies": ["hải sản"],
                "dietary_preferences": ["low carb"]
            }
        },
        timeout=60
    )
    print(f"AI Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        custom_count = sum(
            1 for day in data.get('days', [])
            for meal in day.get('meals', [])
            if meal.get('is_custom', False)
        )
        print(f"AI Response: {len(data.get('days', []))} days, {custom_count} custom dishes")
        print(f"Sample meal: {data['days'][0]['meals'][0]['food_name'][:50] if data.get('days') else 'N/A'}")
except Exception as e:
    print(f"AI Error: {e}")

# 2. Test Backend health
print("\n[2] Testing Backend health...")
try:
    response = httpx.get(f"{BACKEND_URL}/health", timeout=10)
    print(f"Backend Status: {response.status_code}")
except Exception as e:
    print(f"Backend Error: {e}")

# 3. Check if there are any recipes in DB
print("\n[3] Checking database recipes...")
try:
    response = httpx.get(f"{BACKEND_URL}/api/recipes?limit=5", timeout=10)
    print(f"Recipes Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('items', []))} recipes (showing first 5)")
    elif response.status_code == 401:
        print("Need authentication to access recipes")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
