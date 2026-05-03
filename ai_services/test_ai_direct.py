"""
Test meal planning with full health profile
"""
import httpx
import json

BASE_URL = "http://localhost:8001"

# Test with comprehensive health profile
test_payload = {
    "daily_calorie_target": 2000,
    "days": 3,
    "goal_type": "maintain",
    "language": "vi",
    "health_profile": {
        "health_conditions": ["tiểu đường type 2"],
        "food_allergies": ["hải sản"],
        "dietary_preferences": ["low carb"]
    }
}

print("=" * 60)
print("TEST: Meal Planning with Full Health Profile")
print("=" * 60)
print(f"Payload: {json.dumps(test_payload, indent=2, ensure_ascii=False)}")
print()

try:
    response = httpx.post(
        f"{BASE_URL}/meal-planning/generate",
        json=test_payload,
        timeout=120
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS! Response received:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
        
        # Check for custom dishes
        custom_count = 0
        total_count = 0
        for day in data.get('days', []):
            for meal in day.get('meals', []):
                total_count += 1
                if meal.get('is_custom', False):
                    custom_count += 1
        
        print(f"\n--- Summary ---")
        print(f"Total meals: {total_count}")
        print(f"Custom dishes: {custom_count}")
        print(f"Database dishes: {total_count - custom_count}")
        
    else:
        print(f"ERROR: {response.text[:500]}")
        
except Exception as e:
    print(f"EXCEPTION: {str(e)}")
