"""
Test complete flow: Frontend -> Backend -> AI Service
"""
import httpx
import json

BACKEND_URL = "http://backend:8000"
AI_URL = "http://ai_service:8001"

print("=" * 70)
print("TESTING COMPLETE MEAL PLANNING FLOW WITH AI")
print("=" * 70)

# 1. First, register a test user (if not exists)
print("\n[1] Registering test user...")
register_payload = {
    "email": "ai_test@example.com",
    "password": "Test123456",
    "full_name": "AI Test User"
}

try:
    response = httpx.post(f"{BACKEND_URL}/auth/register", json=register_payload, timeout=10)
    if response.status_code == 201:
        print("User registered successfully")
    elif response.status_code == 409:
        print("User already exists, proceeding to login...")
    else:
        print(f"Register response: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"Register error: {e}")

# 2. Login to get token
print("\n[2] Logging in...")
login_payload = {
    "email": "ai_test@example.com",
    "password": "Test123456"
}

try:
    response = httpx.post(f"{BACKEND_URL}/auth/login", json=login_payload, timeout=10)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"Got token: {token[:50]}...")
    else:
        print(f"Login failed: {response.text[:200]}")
        token = None
except Exception as e:
    print(f"Login error: {e}")
    token = None

if not token:
    print("\n[ERROR] Cannot proceed without token")
else:
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test AI service directly first
    print("\n[3] Testing AI service directly...")
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
                    "food_allergies": ["hải sản", "tôm"],
                    "dietary_preferences": ["low carb", "eat clean"]
                }
            },
            timeout=60
        )
        print(f"AI Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"AI generated {len(data.get('days', []))} days")
            print("Sample meals:")
            for meal in data['days'][0].get('meals', [])[:3]:
                print(f"  - {meal.get('meal_type')}: {meal.get('food_name', 'N/A')[:45]}")
                print(f"    is_custom: {meal.get('is_custom')}, calories: {meal.get('calories')}")
    except Exception as e:
        print(f"AI direct test error: {e}")
    
    # 4. Test backend meal plan generation
    print("\n[4] Testing backend meal plan generation with AI...")
    meal_plan_payload = {
        "plan_name": "Test AI Plan - Diabetic Low Carb",
        "days": 3,
        "health_profile": {
            "health_conditions": ["tiểu đường type 2"],
            "food_allergies": ["hải sản", "tôm", "đậu phộng"],
            "dietary_preferences": ["low carb", "eat clean"]
        }
    }
    
    print(f"Payload: {json.dumps(meal_plan_payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = httpx.post(
            f"{BACKEND_URL}/meal-plans/generate",
            json=meal_plan_payload,
            headers=headers,
            timeout=180
        )
        print(f"\nMeal plan status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"SUCCESS! Created meal plan: {data.get('plan_name', 'N/A')}")
            print(f"Days: {len(data.get('days', []))}")
            
            # Count unique meals
            unique_meals = set()
            custom_count = 0
            total_count = 0
            for day in data.get('days', []):
                for item in day.get('items', []):
                    total_count += 1
                    name = item.get('recipe_name') or item.get('notes', '') or 'Unknown'
                    unique_meals.add(name)
                    if 'Custom:' in str(item.get('notes', '')):
                        custom_count += 1
            
            print(f"Total meals: {total_count}")
            print(f"Unique meals: {len(unique_meals)}")
            print(f"Custom dishes: {custom_count}")
            
            print("\nSample meals from first day:")
            if data.get('days'):
                for item in data['days'][0].get('items', [])[:4]:
                    notes = item.get('notes', '')
                    meal_type = item.get('meal_type')
                    print(f"  - {meal_type}: {notes[:60] if notes else 'N/A'}")
        else:
            print(f"ERROR: {response.text[:500]}")
    except Exception as e:
        print(f"Meal plan error: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
