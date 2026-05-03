"""
Test complete flow with goal setup
"""
import httpx
import json

BACKEND_URL = "http://backend:8000"
AI_URL = "http://ai_service:8001"

print("=" * 70)
print("TESTING COMPLETE MEAL PLANNING FLOW WITH GOAL SETUP")
print("=" * 70)

# 1. Login
print("\n[1] Logging in...")
login_payload = {
    "email": "ai_test@example.com",
    "password": "Test123456"
}

try:
    response = httpx.post(f"{BACKEND_URL}/auth/login", json=login_payload, timeout=10)
    if response.status_code == 200:
        token = response.json().get("access_token")
        user_id = response.json().get("user", {}).get("user_id")
        print(f"Login success! User ID: {user_id}")
    else:
        print(f"Login failed: {response.text[:200]}")
        token = None
        user_id = None
except Exception as e:
    print(f"Login error: {e}")
    token = None
    user_id = None

if not token:
    print("\n[ERROR] Cannot proceed without token")
else:
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Check existing goal
    print("\n[2] Checking existing goals...")
    try:
        response = httpx.get(f"{BACKEND_URL}/goals", headers=headers, timeout=10)
        print(f"Goals status: {response.status_code}")
        if response.status_code == 200:
            goals = response.json()
            print(f"Found {len(goals)} goals")
            for g in goals:
                print(f"  - {g.get('goal_type')}: {g.get('daily_calorie_target')} kcal")
    except Exception as e:
        print(f"Check goals error: {e}")
    
    # 3. Create goal if not exists
    print("\n[3] Creating user goal...")
    goal_payload = {
        "goal_type": "weight_loss",
        "daily_calorie_target": 1800,
        "current_weight_kg": 80,
        "target_weight_kg": 70
    }
    
    try:
        response = httpx.post(f"{BACKEND_URL}/goals", json=goal_payload, headers=headers, timeout=10)
        print(f"Create goal status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"Goal created: {response.json()}")
        elif response.status_code == 409:
            print("Goal already exists, proceeding...")
        else:
            print(f"Create goal response: {response.text[:200]}")
    except Exception as e:
        print(f"Create goal error: {e}")
    
    # 4. Now test meal plan generation with AI
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
            
            # Analyze meals
            custom_count = 0
            total_count = 0
            meal_names = []
            for day in data.get('days', []):
                for item in day.get('items', []):
                    total_count += 1
                    notes = item.get('notes', '') or ''
                    meal_names.append(notes)
                    if 'Custom:' in notes:
                        custom_count += 1
            
            print(f"Total meals: {total_count}")
            print(f"Custom dishes from AI: {custom_count}")
            print(f"Database recipes: {total_count - custom_count}")
            
            print("\nAll meals:")
            for i, name in enumerate(meal_names):
                prefix = "Custom:" if "Custom:" in name else "Recipe:"
                print(f"  {i+1}. {name[:70] if name else 'N/A'}")
        else:
            print(f"ERROR: {response.text[:500]}")
    except Exception as e:
        print(f"Meal plan error: {e}")

print("\n" + "=" * 70)
