"""
Test backend meal plan generation with health profile
"""
import httpx
import json

BACKEND_URL = "http://backend:8000"

print("=" * 70)
print("TESTING BACKEND MEAL PLAN GENERATION")
print("=" * 70)

# First, login to get token
print("\n[1] Login to get access token...")
login_payload = {
    "email": "test@example.com",
    "password": "test123"
}

try:
    response = httpx.post(f"{BACKEND_URL}/api/auth/login", json=login_payload, timeout=10)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Got token: {token[:50]}..." if token else "No token")
    else:
        print(f"Login failed: {response.text[:200]}")
        # Try another test account
        login_payload = {
            "email": "admin@nutriai.com",
            "password": "admin123"
        }
        response = httpx.post(f"{BACKEND_URL}/api/auth/login", json=login_payload, timeout=10)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"Got admin token: {token[:50]}..." if token else "No token")
        else:
            print(f"Admin login also failed: {response.text[:200]}")
            token = None
except Exception as e:
    print(f"Login error: {e}")
    token = None

if not token:
    print("\n[SKIP] Cannot get token, testing AI service directly...")
else:
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test generating meal plan with health profile
    print("\n[2] Generating meal plan with health profile...")
    meal_plan_payload = {
        "plan_name": "Test Plan with Health Profile",
        "days": 3,
        "health_profile": {
            "health_conditions": ["tiểu đường type 2"],
            "food_allergies": ["hải sản"],
            "dietary_preferences": ["low carb"]
        }
    }
    
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/meal-plans/generate",
            json=meal_plan_payload,
            headers=headers,
            timeout=120
        )
        print(f"Meal plan status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"SUCCESS! Created meal plan: {data.get('plan_name', 'N/A')}")
            print(f"Days: {len(data.get('days', []))}")
            
            # Count unique meals
            unique_meals = set()
            for day in data.get('days', []):
                for item in day.get('items', []):
                    name = item.get('recipe_name') or item.get('notes', '')
                    unique_meals.add(name)
            print(f"Unique meals: {len(unique_meals)}")
        else:
            print(f"ERROR: {response.text[:500]}")
    except Exception as e:
        print(f"Meal plan error: {e}")

# 3. Test AI service directly (bypassing backend)
print("\n[3] Testing AI service directly...")
try:
    response = httpx.post(
        "http://ai_service:8001/meal-planning/generate",
        json={
            "daily_calorie_target": 2000,
            "days": 2,
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
        print(f"AI generated {len(data.get('days', []))} days")
        
        # Check health profile was respected
        for day in data.get('days', [])[:1]:
            print("Sample meals:")
            for meal in day.get('meals', [])[:3]:
                print(f"  - {meal.get('meal_type')}: {meal.get('food_name', 'N/A')[:40]}")
                print(f"    Calories: {meal.get('calories')}, is_custom: {meal.get('is_custom')}")
except Exception as e:
    print(f"AI test error: {e}")

print("\n" + "=" * 70)
