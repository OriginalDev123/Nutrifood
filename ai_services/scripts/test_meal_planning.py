"""
Test meal planning with correct parameters
"""
import httpx

BASE_URL = "http://localhost:8001"

# Test with correct parameters
test_cases = [
    {
        "name": "Meal plan 2000 cal",
        "payload": {
            "daily_calorie_target": 2000,
            "days": 3,
            "prompt": "Tạo kế hoạch ăn uống cho người bình thường"
        }
    },
    {
        "name": "Meal plan weight loss",
        "payload": {
            "daily_calorie_target": 1500,
            "days": 1,
            "goal": "weight_loss"
        }
    },
    {
        "name": "Meal plan muscle gain",
        "payload": {
            "daily_calorie_target": 2500,
            "days": 1,
            "goal": "muscle_gain"
        }
    }
]

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"TEST: {test['name']}")
    print('='*60)
    
    try:
        response = httpx.post(
            f"{BASE_URL}/meal-planning/generate",
            json=test["payload"],
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Keys: {list(data.keys())}")
            
            # Check for meal_plan content
            if "meal_plan" in data:
                mp = data["meal_plan"]
                print(f"Meal plan type: {type(mp)}")
                if isinstance(mp, dict):
                    print(f"Meal plan keys: {list(mp.keys())}")
                    # Show preview
                    print(f"\nPreview: {str(mp)[:500]}")
                elif isinstance(mp, str):
                    print(f"\nMeal plan content (first 500 chars):\n{mp[:500]}")
            else:
                print(f"\nFull response:\n{str(data)[:500]}")
        else:
            print(f"ERROR: {response.text[:300]}")
            
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
