"""
Test AI respects health profile constraints
"""
import httpx
import json

AI_URL = "http://ai_service:8001"

print("=" * 70)
print("TESTING AI RESPECTS HEALTH PROFILE CONSTRAINTS")
print("=" * 70)

# Test 1: Low Carb + No Seafood
print("\n[Test 1] Low Carb + No Seafood:")
print("-" * 50)
payload = {
    "daily_calorie_target": 2000,
    "days": 2,
    "goal_type": "weight_loss",
    "language": "vi",
    "health_profile": {
        "health_conditions": ["tiểu đường type 2"],
        "food_allergies": ["hải sản", "tôm", "cá", "đậu phộng"],
        "dietary_preferences": ["low carb", "eat clean"]
    }
}

try:
    response = httpx.post(f"{AI_URL}/meal-planning/generate", json=payload, timeout=120)
    if response.status_code == 200:
        data = response.json()
        print("Generated meals:")
        violations = []
        allergen_keywords = ["tôm", "cá", "hải sản", "cua", "mực", "đậu phộng", "lạc", "rice", "bánh", "mì"]
        preference_keywords = ["rice", "cơm", "bún", "phở", "bánh mì", "xôi"]
        
        for day in data.get('days', [])[:2]:
            for meal in day.get('meals', []):
                name = meal.get('food_name', '').lower()
                meal_type = meal.get('meal_type')
                
                # Check for allergen violations
                for allergen in allergen_keywords:
                    if allergen in name:
                        violations.append(f"  ⚠️ {meal_type}: '{meal.get('food_name')}' contains '{allergen}'")
                
                # For low carb, rice/carbs should be minimized
                if 'low carb' in [p.lower() for p in payload['health_profile']['dietary_preferences']]:
                    for carb in preference_keywords:
                        if carb in name:
                            violations.append(f"  ⚠️ {meal_type}: '{meal.get('food_name')}' contains carb '{carb}' (low carb)")
                
                print(f"  - {meal_type}: {meal.get('food_name')[:50]}")
                print(f"    Calories: {meal.get('calories')}, Carbs: {meal.get('carbs_g')}g, is_custom: {meal.get('is_custom')}")
        
        if violations:
            print("\n⚠️ CONSTRAINT VIOLATIONS FOUND:")
            for v in violations:
                print(v)
        else:
            print("\n✅ No constraint violations detected!")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Vegetarian
print("\n[Test 2] Vegetarian (No meat):")
print("-" * 50)
payload2 = {
    "daily_calorie_target": 1800,
    "days": 1,
    "goal_type": "maintain",
    "language": "vi",
    "health_profile": {
        "health_conditions": [],
        "food_allergies": [],
        "dietary_preferences": ["vegetarian"]
    }
}

try:
    response = httpx.post(f"{AI_URL}/meal-planning/generate", json=payload2, timeout=120)
    if response.status_code == 200:
        data = response.json()
        print("Generated meals:")
        meat_keywords = ["thịt bò", "thịt heo", "thịt gà", "bò", "heo", "gà", "cá", "tôm", "thăn", "sườn"]
        violations = []
        
        for meal in data.get('days', [])[0].get('meals', []):
            name = meal.get('food_name', '').lower()
            meal_type = meal.get('meal_type')
            
            for meat in meat_keywords:
                if meat in name:
                    violations.append(f"  ⚠️ {meal_type}: '{meal.get('food_name')}' contains '{meat}'")
            
            print(f"  - {meal_type}: {meal.get('food_name')[:50]}")
        
        if violations:
            print("\n⚠️ VIOLATIONS:")
            for v in violations:
                print(v)
        else:
            print("\n✅ No meat detected - vegetarian constraint respected!")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
