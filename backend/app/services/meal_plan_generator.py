"""
Meal Plan Generator - AI-powered Meal Plan Generation
Handles intelligent meal plan creation with Gemini AI + fallback
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Optional, Set
from uuid import UUID, uuid4
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
import random
import httpx
import os
import re

from app.models.user import UserGoal
from app.models.recipe import Recipe, RecipeIngredient
from app.models.meal_plan import MealPlan, MealPlanItem
from app.models.food import Food


# ==========================================
# MOCK DATA - Chỉ dùng khi không có AI/DB
# ==========================================

MOCK_BREAKFAST = [
    {"name_vi": "Bánh mì trứng", "calories": 350, "protein": 15, "carbs": 40, "fat": 12, "tags": ["breakfast", "egg"]},
    {"name_vi": "Xôi gấc", "calories": 350, "protein": 8, "carbs": 55, "fat": 12, "tags": ["breakfast", "sticky_rice"]},
    {"name_vi": "Trứng chiên bánh mì", "calories": 320, "protein": 14, "carbs": 35, "fat": 14, "tags": ["breakfast", "egg", "bread"]},
    {"name_vi": "Cháo gà", "calories": 280, "protein": 18, "carbs": 35, "fat": 8, "tags": ["breakfast", "chicken", "porridge"]},
    {"name_vi": "Bánh đa cua", "calories": 380, "protein": 16, "carbs": 45, "fat": 14, "tags": ["breakfast", "crab", "seafood"]},
    {"name_vi": "Yến mạch cháo", "calories": 300, "protein": 10, "carbs": 50, "fat": 6, "tags": ["breakfast", "oatmeal", "healthy"]},
    {"name_vi": "Trái cây dầm sữa", "calories": 200, "protein": 5, "carbs": 40, "fat": 3, "tags": ["breakfast", "fruit", "milk"]},
    {"name_vi": "Bánh gai", "calories": 280, "protein": 8, "carbs": 45, "fat": 8, "tags": ["breakfast", "cake"]},
]

MOCK_LUNCH = [
    {"name_vi": "Cơm gà xối mỡ", "calories": 600, "protein": 30, "carbs": 70, "fat": 18, "tags": ["lunch", "chicken", "rice"]},
    {"name_vi": "Bún bò Huế", "calories": 550, "protein": 25, "carbs": 60, "fat": 20, "tags": ["lunch", "beef", "noodle"]},
    {"name_vi": "Mì Quảng", "calories": 580, "protein": 24, "carbs": 60, "fat": 22, "tags": ["lunch", "seafood", "noodle"]},
    {"name_vi": "Phở bò", "calories": 500, "protein": 22, "carbs": 55, "fat": 16, "tags": ["lunch", "beef", "noodle"]},
    {"name_vi": "Hủ tiếu Mỹ Tho", "calories": 450, "protein": 18, "carbs": 52, "fat": 16, "tags": ["lunch", "noodle"]},
    {"name_vi": "Cơm rang dưa cà", "calories": 450, "protein": 15, "carbs": 65, "fat": 14, "tags": ["lunch", "rice", "vegetable"]},
    {"name_vi": "Bún chả Hà Nội", "calories": 520, "protein": 25, "carbs": 55, "fat": 18, "tags": ["lunch", "pork", "noodle"]},
    {"name_vi": "Cơm tấm sườn bì chả", "calories": 580, "protein": 28, "carbs": 60, "fat": 20, "tags": ["lunch", "pork", "rice"]},
]

MOCK_DINNER = [
    {"name_vi": "Cá kho tộ", "calories": 380, "protein": 28, "carbs": 20, "fat": 18, "tags": ["dinner", "fish", "seafood"]},
    {"name_vi": "Thịt kho trứng", "calories": 400, "protein": 24, "carbs": 15, "fat": 25, "tags": ["dinner", "pork", "egg"]},
    {"name_vi": "Gà rang gừng", "calories": 380, "protein": 30, "carbs": 15, "fat": 20, "tags": ["dinner", "chicken"]},
    {"name_vi": "Canh chua cá lóc", "calories": 220, "protein": 25, "carbs": 12, "fat": 8, "tags": ["dinner", "fish", "soup"]},
    {"name_vi": "Rau muống xào tỏi + cơm", "calories": 280, "protein": 8, "carbs": 45, "fat": 6, "tags": ["dinner", "vegetable", "rice"]},
    {"name_vi": "Đậu phụ chiên giòn", "calories": 250, "protein": 15, "carbs": 10, "fat": 18, "tags": ["dinner", "tofu", "vegetarian"]},
    {"name_vi": "Salad rau trộn", "calories": 180, "protein": 5, "carbs": 15, "fat": 12, "tags": ["dinner", "salad", "healthy"]},
    {"name_vi": "Thịt bò xào rau", "calories": 350, "protein": 28, "carbs": 15, "fat": 20, "tags": ["dinner", "beef", "vegetable"]},
]

MOCK_SNACK = [
    {"name_vi": "Gỏi cuốn", "calories": 180, "protein": 12, "carbs": 20, "fat": 6, "tags": ["snack", "vegetable"]},
    {"name_vi": "Chả giò", "calories": 280, "protein": 15, "carbs": 25, "fat": 14, "tags": ["snack", "fried"]},
    {"name_vi": "Rau câu", "calories": 80, "protein": 2, "carbs": 18, "fat": 0, "tags": ["snack", "dessert"]},
    {"name_vi": "Trái cây", "calories": 100, "protein": 1, "carbs": 22, "fat": 0, "tags": ["snack", "fruit", "healthy"]},
    {"name_vi": "Sữa chua", "calories": 120, "protein": 8, "carbs": 15, "fat": 4, "tags": ["snack", "dairy"]},
    {"name_vi": "Hạt óc chó", "calories": 185, "protein": 4, "carbs": 4, "fat": 18, "tags": ["snack", "nuts", "healthy"]},
    {"name_vi": "Táo", "calories": 95, "protein": 0, "carbs": 25, "fat": 0, "tags": ["snack", "fruit", "healthy"]},
]

DEFAULT_DAILY_CALORIES = 2000
DEFAULT_MEAL_DISTRIBUTION = {
    "breakfast": Decimal("0.25"),
    "lunch": Decimal("0.35"),
    "dinner": Decimal("0.30"),
    "snack": Decimal("0.10"),
}


# ==========================================
# CONSTANTS
# ==========================================

# Goal-specific meal calorie distributions (as percentage of daily total)
MEAL_DISTRIBUTIONS = {
    "weight_loss": {
        "breakfast": Decimal("0.30"),
        "lunch": Decimal("0.35"),
        "dinner": Decimal("0.25"),
        "snack": Decimal("0.10")
    },
    "weight_gain": {
        "breakfast": Decimal("0.25"),
        "lunch": Decimal("0.30"),
        "dinner": Decimal("0.35"),
        "snack": Decimal("0.10")
    },
    "maintain": {
        "breakfast": Decimal("0.25"),
        "lunch": Decimal("0.35"),
        "dinner": Decimal("0.30"),
        "snack": Decimal("0.10")
    },
    "healthy_lifestyle": {
        "breakfast": Decimal("0.25"),
        "lunch": Decimal("0.35"),
        "dinner": Decimal("0.30"),
        "snack": Decimal("0.10")
    },
    "default": {
        "breakfast": Decimal("0.25"),
        "lunch": Decimal("0.35"),
        "dinner": Decimal("0.30"),
        "snack": Decimal("0.10")
    }
}

# Variety tracking constants
VARIETY_LOOKBACK_DAYS = 3

# Decimal constants
DECIMAL_0 = Decimal("0")
DECIMAL_100 = Decimal("100")


# ==========================================
# ALLERGEN SYNONYMS MAPPING
# ==========================================

# Map Vietnamese allergen names to English keywords and related terms
ALLERGEN_SYNONYMS = {
    "hải sản": ["seafood", "shrimp", "crab", "fish", "tôm", "cua", "cá", "mực", "ngao", "sò", "hàu", "tôm hùm", "tôm càng", " calamari", "squid"],
    "tôm": ["shrimp", "prawn", "tôm", "tôm rang", "tôm hấp", "tôm chiên", "tôm nướng", "tôm sú", "tôm thẻ"],
    "cua": ["crab", "cua", "cua biển", "cua đồng"],
    "cá": ["fish", "cá", "cá kho", "cá chiên", "canh cá", "cá lóc", "cá thu", "cá hồi", "cá ngừ", "cá basa"],
    "đậu phộng": ["peanut", "đậu phộng", "lạc", "đậu phộng rang", "peanuts"],
    "đậu nành": ["soy", "soybean", "đậu nành", "đậu", "sữa đậu nành", "tofu", "đậu phụ"],
    "gluten": ["gluten", "wheat", "bột mì", "mì", "bánh mì", "wheat flour", "bread", "noodle", "pasta"],
    "sữa": ["milk", "sữa", "cheese", "phô mai", "yogurt", "sữa chua", "dairy", "cream", "butter"],
    "trứng": ["egg", "trứng", "egg white", "trứng gà", "trứng vịt"],
    "đậu": ["bean", "đậu", "đậu xanh", "đậu đen", "đậu đỏ", "đậu nành", "bean sprout", "giá đậu"],
    "ngô": ["corn", "ngô", "bắp", "corn starch"],
    "hạt": ["nut", "nuts", "hạt", "hạt điều", "hạt dẻ", "hạt bí", "hạt hướng dương"],
    "óc chó": ["walnut", "óc chó", "walnuts"],
    "hạnh nhân": ["almond", "hạnh nhân", "almonds"],
    "bột mì": ["wheat flour", "bột mì", "flour", "bánh mì", "mì", "pasta", "bread"],
    "thịt bò": ["beef", "bò", "steak", "thịt bò", "bò bít tết", "bò viên"],
    "thịt gà": ["chicken", "gà", "thịt gà", "chicken breast", "gà rang", "gà xào", "gà hấp"],
    "thịt heo": ["pork", "heo", "thịt heo", "thịt lợn", "pork belly", "thịt xá xíu"],
}


# ==========================================
# HEALTH CONDITIONS → TAGS MAPPING
# ==========================================

HEALTH_CONDITION_TAGS = {
    "tiểu đường": ["low_sugar", "low_carb", "high_fiber", "diabetic_friendly"],
    "tiểu đường type 1": ["low_sugar", "low_carb", "high_fiber", "diabetic_friendly"],
    "tiểu đường type 2": ["low_sugar", "low_carb", "high_fiber", "diabetic_friendly"],
    "diabetes": ["low_sugar", "low_carb", "high_fiber", "diabetic_friendly"],
    "huyết áp cao": ["low_sodium", "heart_healthy", "dash"],
    "huyết áp thấp": ["normal_sodium", "heart_healthy"],
    "hypertension": ["low_sodium", "heart_healthy", "dash"],
    "bệnh tim mạch": ["heart_healthy", "low_fat", "low_cholesterol"],
    "tim mạch": ["heart_healthy", "low_fat", "low_cholesterol"],
    "heart": ["heart_healthy", "low_fat", "low_cholesterol"],
    "cholesterol cao": ["low_cholesterol", "low_fat"],
    "mỡ máu": ["low_cholesterol", "low_fat"],
    "cholesterol": ["low_cholesterol", "low_fat"],
    "gan nhiễm mỡ": ["low_fat", "detox", "low_sugar"],
    "fatty liver": ["low_fat", "detox", "low_sugar"],
    "viêm khớp": ["anti_inflammatory", "low_fat"],
    "arthritis": ["anti_inflammatory", "low_fat"],
    "loãng xương": ["high_calcium", "high_protein"],
    "osteoporosis": ["high_calcium", "high_protein"],
    "suy thận": ["low_sodium", "low_protein", "low_potassium"],
    "kidney": ["low_sodium", "low_protein", "low_potassium"],
    "hen suyễn": ["anti_inflammatory"],
    "asthma": ["anti_inflammatory"],
    "dị ứng": [],  # Generic - rely on specific allergies
}


# ==========================================
# DIETARY PREFERENCES → RULES MAPPING
# ==========================================

# Tags to AVOID for each preference
DIETARY_PREFERENCE_RESTRICTIONS = {
    "low carb": ["rice", "com", "bún", "bánh", "mì", "phở", "bánh mì", "xôi", "noodle", "bread", "sticky rice"],
    "keto": ["rice", "com", "bún", "bánh", "mì", "phở", "bánh mì", "xôi", "noodle", "bread", "sticky rice", "sugar", "đường"],
    "eat clean": ["fried", "chiên", "rán", "processed"],
    "vegetarian": ["chicken", "beef", "pork", "fish", "seafood", "thịt", "bò", "heo", "gà", "cá", "hải sản", "meat"],
    "vegan": ["chicken", "beef", "pork", "fish", "seafood", "egg", "milk", "dairy", "cheese", "honey", "thịt", "bò", "heo", "gà", "cá", "hải sản", "trứng", "sữa", "thịt", "meat"],
    "paleo": ["grain", "legume", "đậu", "bean", "rice", "bread", "bánh", "mì"],
    "mediterranean": [],  # Just preference, no hard restrictions
    "dash": ["low_sodium", "heart_healthy"],  # Already low sodium
    "low fat": ["fried", "chiên", "rán", "fat", "mỡ"],
    "low sodium": ["salted", "mắm", "muối", "đồ chế biến", "processed"],
    "high protein": ["high_protein"],  # Just preference
    "high fiber": ["high_fiber", "fiber"],  # Just preference
    "gluten free": ["wheat", "gluten", "bột mì", "bánh mì", "mì", "bread", "flour"],
    "sugar free": ["sugar", "đường", "dessert", "bánh", "kẹo"],
    "raw food": ["cooked", "nấu", "chiên", "fried", "grilled"],
}

# Tags to INCLUDE/PREFER for each preference
DIETARY_PREFERENCE_INCLUDES = {
    "low carb": ["vegetable", "salad", "meat", "fish", "egg"],
    "keto": ["vegetable", "meat", "fish", "egg", "fat", "avocado"],
    "eat clean": ["healthy", "vegetable", "fruit", "grilled", "steamed"],
    "vegetarian": ["vegetable", "tofu", "bean", "fruit"],
    "vegan": ["vegetable", "fruit", "tofu", "bean"],
    "mediterranean": ["olive oil", "fish", "vegetable", "whole grain"],
    "dash": ["vegetable", "fruit", "low_sodium"],
    "low fat": ["grilled", "steamed", "boiled", "vegetable"],
    "low sodium": ["fresh", "vegetable", "fruit", "homemade"],
    "high protein": ["chicken", "beef", "fish", "egg", "tofu"],
    "high fiber": ["vegetable", "fruit", "whole grain", "bean"],
    "gluten free": ["rice", "vegetable", "fruit", "tuber"],
    "sugar free": ["vegetable", "protein", "unsweetened"],
    "raw food": ["fruit", "vegetable", "salad", "raw"],
}


def round_2(value: Decimal) -> Decimal:
    """Round Decimal to 2 decimal places"""
    if value is None:
        return DECIMAL_0
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==========================================
# HEALTH PROFILE HELPER FUNCTIONS
# ==========================================

def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove accents)"""
    import unicodedata
    text = text.lower().strip()
    # Remove accents
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text


def _get_all_allergen_keywords(allergens: List[str]) -> Set[str]:
    """Get all keywords to check for allergens including synonyms"""
    keywords = set()
    normalized_allergens = [_normalize_text(a) for a in allergens]
    
    for allergen in normalized_allergens:
        keywords.add(allergen)
        # Check if this allergen has synonyms
        for key, synonyms in ALLERGEN_SYNONYMS.items():
            if key in allergen or allergen in key:
                keywords.update([_normalize_text(s) for s in synonyms])
    
    return keywords


def _check_allergen_in_recipe(recipe: Recipe, db: Session, allergens: List[str]) -> bool:
    """
    Check if recipe contains any of the specified allergens.
    Uses synonym expansion for better matching.
    Returns True if allergen is found, False otherwise.
    """
    if not allergens:
        return False
    
    # Get all keywords to check (including synonyms)
    allergen_keywords = _get_all_allergen_keywords(allergens)
    
    # Check recipe name
    recipe_name_normalized = _normalize_text(recipe.name_vi or "")
    for keyword in allergen_keywords:
        if keyword in recipe_name_normalized:
            print(f"   ⚠️ Allergen '{keyword}' found in recipe name: {recipe.name_vi}")
            return True
    
    # Check recipe tags
    if recipe.tags:
        for tag in recipe.tags:
            tag_normalized = _normalize_text(tag)
            for keyword in allergen_keywords:
                if keyword in tag_normalized:
                    print(f"   ⚠️ Allergen '{keyword}' found in recipe tag: {tag}")
                    return True
    
    # Check ingredients
    for ingredient in recipe.ingredients:
        ingredient_name_normalized = _normalize_text(ingredient.ingredient_name or "")
        for keyword in allergen_keywords:
            if keyword in ingredient_name_normalized:
                print(f"   ⚠️ Allergen '{keyword}' found in ingredient: {ingredient.ingredient_name}")
                return True
    
    return False


def _check_allergen_in_mock_dish(dish: Dict, allergens: List[str]) -> bool:
    """Check if mock dish contains any allergens"""
    if not allergens:
        return False
    
    allergen_keywords = _get_all_allergen_keywords(allergens)
    dish_name_normalized = _normalize_text(dish.get("name_vi", ""))
    
    for keyword in allergen_keywords:
        if keyword in dish_name_normalized:
            return True
    
    # Check tags
    dish_tags = dish.get("tags", [])
    for tag in dish_tags:
        tag_normalized = _normalize_text(tag)
        for keyword in allergen_keywords:
            if keyword in tag_normalized:
                return True
    
    return False


def _check_dietary_restrictions_in_recipe(recipe: Recipe, dietary_preferences: List[str]) -> bool:
    """
    Check if recipe violates dietary preferences.
    Returns True if recipe violates any restriction, False if OK.
    """
    if not dietary_preferences:
        return False
    
    normalized_prefs = [_normalize_text(p) for p in dietary_preferences]
    
    # Get all restricted keywords
    restricted_keywords = set()
    for pref in normalized_prefs:
        pref_key = pref.lower()
        if pref_key in DIETARY_PREFERENCE_RESTRICTIONS:
            restricted_keywords.update([_normalize_text(r) for r in DIETARY_PREFERENCE_RESTRICTIONS[pref_key]])
    
    if not restricted_keywords:
        return False
    
    # Check recipe name
    recipe_name_normalized = _normalize_text(recipe.name_vi or "")
    for keyword in restricted_keywords:
        if keyword in recipe_name_normalized:
            print(f"   ⚠️ Dietary restriction '{keyword}' found in recipe name: {recipe.name_vi}")
            return True
    
    # Check recipe tags
    if recipe.tags:
        for tag in recipe.tags:
            tag_normalized = _normalize_text(tag)
            for keyword in restricted_keywords:
                if keyword in tag_normalized:
                    print(f"   ⚠️ Dietary restriction '{keyword}' found in recipe tag: {tag}")
                    return True
    
    return False


def _check_dietary_restrictions_in_mock_dish(dish: Dict, dietary_preferences: List[str]) -> bool:
    """Check if mock dish violates dietary preferences"""
    if not dietary_preferences:
        return False
    
    normalized_prefs = [_normalize_text(p) for p in dietary_preferences]
    
    # Get all restricted keywords
    restricted_keywords = set()
    for pref in normalized_prefs:
        pref_key = pref.lower()
        if pref_key in DIETARY_PREFERENCE_RESTRICTIONS:
            restricted_keywords.update([_normalize_text(r) for r in DIETARY_PREFERENCE_RESTRICTIONS[pref_key]])
    
    if not restricted_keywords:
        return False
    
    # Check dish name
    dish_name_normalized = _normalize_text(dish.get("name_vi", ""))
    for keyword in restricted_keywords:
        if keyword in dish_name_normalized:
            return True
    
    # Check tags
    dish_tags = dish.get("tags", [])
    for tag in dish_tags:
        tag_normalized = _normalize_text(tag)
        for keyword in restricted_keywords:
            if keyword in tag_normalized:
                return True
    
    return False


def _suggest_tags_from_health_conditions(health_conditions: List[str]) -> List[str]:
    """
    Suggest additional dietary tags based on health conditions.
    """
    suggested_tags = set()
    
    for condition in health_conditions:
        condition_normalized = _normalize_text(condition)
        
        # Check all health conditions
        for key, tags in HEALTH_CONDITION_TAGS.items():
            if key in condition_normalized or condition_normalized in key:
                suggested_tags.update(tags)
    
    return list(suggested_tags)


def _score_recipe_for_preferences(recipe: Recipe, dietary_preferences: List[str], health_conditions: List[str] = None) -> float:
    """
    Score a recipe based on how well it matches dietary preferences and health conditions.
    Returns a score from 0 to 1, where 1 is the best match.
    Higher weight for strict dietary requirements.
    """
    score = 0.0
    max_score = 0.0
    
    # Combine dietary preferences and health condition tags
    all_preferences = list(dietary_preferences or [])
    if health_conditions:
        all_preferences.extend(_suggest_tags_from_health_conditions(health_conditions))
    
    if not all_preferences:
        return 0.5
    
    # Normalize preferences
    normalized_prefs = [_normalize_text(p) for p in all_preferences]
    
    # Check recipe tags for preference matches
    if recipe.tags:
        for pref in normalized_prefs:
            for tag in recipe.tags:
                tag_normalized = _normalize_text(tag)
                # Exact match gets higher score
                if pref == tag_normalized:
                    score += 3.0
                elif pref in tag_normalized or tag_normalized in pref:
                    score += 2.0
                max_score += 3.0
    
    # Check recipe name
    recipe_name = _normalize_text(recipe.name_vi or "")
    for pref in normalized_prefs:
        if pref == recipe_name:
            score += 2.0
        elif pref in recipe_name or recipe_name in pref:
            score += 1.0
        max_score += 2.0
    
    if max_score > 0:
        return min(1.0, score / max_score)
    
    return 0.5


# ==========================================
# MAIN GENERATION FUNCTION
# ==========================================

def _get_mock_meal_plan(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int,
    goal_type: str = "maintain",
    health_profile: Optional[Dict] = None
) -> MealPlan:
    """
    Tạo kế hoạch ăn từ dữ liệu mock - CÓ FILTER theo health profile.
    Mỗi ngày: 1 breakfast + 1 lunch + 1 dinner + có thể 1 snack
    """
    # Extract health profile data
    food_allergies = health_profile.get("food_allergies", []) if health_profile else []
    dietary_preferences = health_profile.get("dietary_preferences", []) if health_profile else []
    health_conditions = health_profile.get("health_conditions", []) if health_profile else []
    
    # Get suggested tags from health conditions
    suggested_tags = _suggest_tags_from_health_conditions(health_conditions)
    all_preferences = list(set(dietary_preferences + suggested_tags))
    
    if health_profile:
        print(f"🏥 Mock generation with health profile:")
        print(f"   - Allergies to avoid: {food_allergies}")
        print(f"   - Dietary preferences: {all_preferences}")
    
    # Filter mock data
    def is_valid_dish(dish: Dict) -> bool:
        # Check allergens
        if food_allergies and _check_allergen_in_mock_dish(dish, food_allergies):
            return False
        # Check dietary restrictions
        if all_preferences and _check_dietary_restrictions_in_mock_dish(dish, all_preferences):
            return False
        return True
    
    # Filter each meal category
    valid_breakfast = [d for d in MOCK_BREAKFAST if is_valid_dish(d)]
    valid_lunch = [d for d in MOCK_LUNCH if is_valid_dish(d)]
    valid_dinner = [d for d in MOCK_DINNER if is_valid_dish(d)]
    valid_snack = [d for d in MOCK_SNACK if is_valid_dish(d)]
    
    # Fallback to original if all filtered out
    if not valid_breakfast:
        valid_breakfast = MOCK_BREAKFAST
        print("⚠️ No valid breakfast after filtering, using all")
    if not valid_lunch:
        valid_lunch = MOCK_LUNCH
        print("⚠️ No valid lunch after filtering, using all")
    if not valid_dinner:
        valid_dinner = MOCK_DINNER
        print("⚠️ No valid dinner after filtering, using all")
    if not valid_snack:
        valid_snack = MOCK_SNACK
        print("⚠️ No valid snack after filtering, using all")
    
    print(f"📋 Valid dishes after filtering: {len(valid_breakfast)} breakfast, {len(valid_lunch)} lunch, {len(valid_dinner)} dinner, {len(valid_snack)} snack")
    
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)

    meal_plan = MealPlan(
        plan_id=uuid4(),
        user_id=user_id,
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        servings=1,
        preferences={"health_profile": health_profile} if health_profile else {},
        is_active=True,
        is_completed=False
    )
    db.add(meal_plan)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Chọn ngẫu nhiên 1 món từ mỗi bữa đã filter
        breakfast_item = random.choice(valid_breakfast)
        lunch_item = random.choice(valid_lunch)
        dinner_item = random.choice(valid_dinner)
        
        order_index = 0
        
        # Breakfast
        item = MealPlanItem(
            meal_plan_id=meal_plan.plan_id,
            food_id=None,
            day_date=current_date,
            meal_type="breakfast",
            serving_size_g=Decimal("100"),
            quantity=Decimal("1"),
            calories=Decimal(str(breakfast_item["calories"])),
            protein_g=Decimal(str(breakfast_item["protein"])),
            carbs_g=Decimal(str(breakfast_item["carbs"])),
            fat_g=Decimal(str(breakfast_item["fat"])),
            unit="serving",
            notes=f"Recipe: {breakfast_item['name_vi']}",
            order_index=order_index
        )
        db.add(item)
        order_index += 1
        
        # Lunch
        item = MealPlanItem(
            meal_plan_id=meal_plan.plan_id,
            food_id=None,
            day_date=current_date,
            meal_type="lunch",
            serving_size_g=Decimal("100"),
            quantity=Decimal("1"),
            calories=Decimal(str(lunch_item["calories"])),
            protein_g=Decimal(str(lunch_item["protein"])),
            carbs_g=Decimal(str(lunch_item["carbs"])),
            fat_g=Decimal(str(lunch_item["fat"])),
            unit="serving",
            notes=f"Recipe: {lunch_item['name_vi']}",
            order_index=order_index
        )
        db.add(item)
        order_index += 1
        
        # Dinner
        item = MealPlanItem(
            meal_plan_id=meal_plan.plan_id,
            food_id=None,
            day_date=current_date,
            meal_type="dinner",
            serving_size_g=Decimal("100"),
            quantity=Decimal("1"),
            calories=Decimal(str(dinner_item["calories"])),
            protein_g=Decimal(str(dinner_item["protein"])),
            carbs_g=Decimal(str(dinner_item["carbs"])),
            fat_g=Decimal(str(dinner_item["fat"])),
            unit="serving",
            notes=f"Recipe: {dinner_item['name_vi']}",
            order_index=order_index
        )
        db.add(item)
        order_index += 1
        
        # Snack (có 50% khả năng có)
        if random.random() > 0.5:
            snack_item = random.choice(valid_snack)
            item = MealPlanItem(
                meal_plan_id=meal_plan.plan_id,
                food_id=None,
                day_date=current_date,
                meal_type="snack",
                serving_size_g=Decimal("100"),
                quantity=Decimal("1"),
                calories=Decimal(str(snack_item["calories"])),
                protein_g=Decimal(str(snack_item["protein"])),
                carbs_g=Decimal(str(snack_item["carbs"])),
                fat_g=Decimal(str(snack_item["fat"])),
                unit="serving",
                notes=f"Recipe: {snack_item['name_vi']}",
                order_index=order_index
            )
            db.add(item)

    db.commit()
    db.refresh(meal_plan)
    print(f"✅ Đã tạo mock meal plan: {meal_plan.plan_id} với filter health profile!")
    return meal_plan


# ==========================================
# AI SERVICE INTEGRATION
# ==========================================

def _get_available_foods_for_ai(db: Session, limit: int = 50) -> List[Dict]:
    """
    Get available foods from database for AI to reference.
    Returns list of foods with nutrition info.
    """
    foods = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        Recipe.calories_per_serving.isnot(None)
    ).limit(limit).all()
    
    return [
        {
            "name_vi": f.name_vi,
            "calories": float(f.calories_per_serving or 0),
            "protein_g": float(f.protein_per_serving or 0),
            "carbs_g": float(f.carbs_per_serving or 0),
            "fat_g": float(f.fat_per_serving or 0),
            "tags": f.tags or [],
            "category": f.category
        }
        for f in foods
    ]


async def _call_ai_meal_planning(
    daily_calorie_target: int,
    days: int,
    goal_type: str,
    preferences: Optional[Dict],
    available_foods: List[Dict],
    health_profile: Optional[Dict]
) -> Dict:
    """
    Call AI meal planning service via HTTP API.
    This runs in a separate thread to avoid blocking the event loop.
    """
    import httpx
    import os
    
    # Get AI service URL from environment or use default Docker service name
    ai_service_url = os.environ.get("AI_SERVICE_URL", "http://ai_service:8001")
    api_endpoint = f"{ai_service_url}/meal-planning/generate"
    
    # Build request payload for AI service
    payload = {
        "daily_calorie_target": daily_calorie_target,
        "days": days,
        "goal_type": goal_type,
        "preferences": preferences,
        "available_foods": available_foods if available_foods else None,
        "health_profile": health_profile,
        "language": "vi"
    }
    
    print(f"🤖 Calling AI service at {api_endpoint}...")
    
    # Run HTTP request in thread pool since httpx is sync
    import asyncio
    loop = asyncio.get_event_loop()
    
    async def _make_request():
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(api_endpoint, json=payload)
            response.raise_for_status()
            return response.json()
    
    result = await _make_request()
    print(f"✅ AI service returned meal plan with {len(result.get('days', []))} days")
    return result


def _convert_ai_result_to_meal_plan(
    db: Session,
    user_id: UUID,
    plan_name: str,
    ai_result: Dict,
    days: int,
    health_profile: Optional[Dict] = None
) -> MealPlan:
    """
    Convert AI-generated meal plan to database MealPlan.
    Handles both database recipes and custom AI-created dishes.
    """
    from app.services.meal_plan_service import create_meal_plan
    from app.schemas.meal_plan import MealPlanCreate
    
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)
    
    # Count custom dishes for logging
    custom_count = sum(
        1 for day in ai_result.get('days', [])
        for meal in day.get('meals', [])
        if meal.get('is_custom', False)
    )
    
    meal_plan = create_meal_plan(db, user_id, MealPlanCreate(
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        servings=1,
        preferences={
            "source": "ai",
            "custom_dishes_count": custom_count,
            "health_profile": health_profile
        }
    ))
    
    day_offset = 0
    for day_data in ai_result.get("days", []):
        day_offset += 1
        current_date = start_date + timedelta(days=day_offset - 1)
        
        order_index = 0
        for meal in day_data.get("meals", []):
            meal_type = meal.get("meal_type", "snack")
            is_custom = meal.get("is_custom", False)
            food_name = meal.get("food_name", "Unknown")
            
            # Build notes
            if is_custom:
                notes = f"Custom: {food_name}"
                # Add ingredients if available
                ingredients = meal.get("ingredients", [])
                if ingredients:
                    notes += f" | Nguyên liệu: {', '.join(ingredients)}"
            else:
                notes = f"Recipe: {food_name}"
            
            item = MealPlanItem(
                meal_plan_id=meal_plan.plan_id,
                food_id=None,  # Custom dishes don't have food_id
                day_date=current_date,
                meal_type=meal_type,
                serving_size_g=Decimal("100"),
                quantity=Decimal("1"),
                calories=Decimal(str(meal.get("calories", 0))),
                protein_g=Decimal(str(meal.get("protein_g", 0))),
                carbs_g=Decimal(str(meal.get("carbs_g", 0))),
                fat_g=Decimal(str(meal.get("fat_g", 0))),
                unit="serving",
                notes=notes,
                order_index=order_index
            )
            
            db.add(item)
            order_index += 1
    
    db.commit()
    db.refresh(meal_plan)
    
    print(f"✅ Created AI meal plan: {meal_plan.plan_id} with {custom_count} custom dishes")
    return meal_plan


def _generate_with_ai(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int,
    goal,
    preferences: Optional[Dict] = None,
    health_profile: Optional[Dict] = None
) -> MealPlan:
    """
    Generate meal plan using AI service (PRIORITY when health_profile provided).
    AI can create NEW dishes not in database.
    """
    import asyncio
    
    daily_calorie_target = int(goal.daily_calorie_target)
    goal_type = goal.goal_type or "maintain"
    
    print(f"🤖 Starting AI meal plan generation...")
    print(f"   - Daily calories: {daily_calorie_target}")
    print(f"   - Goal type: {goal_type}")
    print(f"   - Days: {days}")
    
    if health_profile:
        print(f"   - Allergies: {health_profile.get('food_allergies', [])}")
        print(f"   - Preferences: {health_profile.get('dietary_preferences', [])}")
        print(f"   - Conditions: {health_profile.get('health_conditions', [])}")
    
    # Get available foods from database
    available_foods = _get_available_foods_for_ai(db)
    print(f"   - Available foods in DB: {len(available_foods)}")
    
    try:
        # Call AI service
        ai_result = asyncio.run(_call_ai_meal_planning(
            daily_calorie_target=daily_calorie_target,
            days=days,
            goal_type=goal_type,
            preferences=preferences,
            available_foods=available_foods,
            health_profile=health_profile
        ))
        
        # Convert AI result to MealPlan
        meal_plan = _convert_ai_result_to_meal_plan(
            db, user_id, plan_name, ai_result, days, health_profile
        )
        
        return meal_plan
        
    except Exception as e:
        print(f"⚠️ AI service failed: {e}")
        raise


def generate_meal_plan(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int = 7,
    preferences: Optional[Dict] = None,
    health_profile: Optional[Dict] = None
) -> MealPlan:
    """
    Generate intelligent meal plan - TÍCH HỢP AI.
    
    ALGORITHM:
    1. Thử gọi AI service (Gemini) nếu có health_profile
    2. Fallback: dùng recipe từ database nếu có
    3. Fallback cuối: dùng mock data đã filter theo health profile
    
    Args:
        db: Database session
        user_id: User UUID
        plan_name: Name for the meal plan
        days: Number of days (default 7)
        preferences: Optional filters
        health_profile: Optional health profile
            - health_conditions: List[str]
            - food_allergies: List[str]
            - dietary_preferences: List[str]
    
    Returns:
        Generated MealPlan with MealPlanItems
    """
    
    # Log health profile if provided
    if health_profile:
        print(f"🏥 Health profile provided - conditions={health_profile.get('health_conditions', [])}, "
               f"allergies={health_profile.get('food_allergies', [])}, "
               f"preferences={health_profile.get('dietary_preferences', [])}")
    
    # 1. Get user's active goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_deleted == False
    ).first()

    # 2. Check if recipes exist in database
    recipe_count = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        Recipe.calories_per_serving.isnot(None)
    ).count()

    # 3. Determine generation method
    # Default values when no goal exists
    default_calorie_target = 2000
    default_goal_type = "maintain"
    
    if goal and goal.daily_calorie_target:
        goal_type = goal.goal_type or "maintain"
        daily_calorie = goal.daily_calorie_target
        has_goal = True
    else:
        # No goal - use defaults but still try AI with health_profile
        goal_type = default_goal_type
        daily_calorie = default_calorie_target
        has_goal = False
        print(f"⚠️ No goal found, using defaults ({daily_calorie} kcal)...")
    
    # PRIORITY 1: AI Service when health_profile provided
    # AI can create custom dishes not in database
    # Also call AI if user has health_profile even without goal
    if health_profile:
        try:
            print(f"🤖 Using AI service for personalized meal planning...")
            # Create a pseudo-goal object for AI call
            pseudo_goal = type('obj', (object,), {
                'daily_calorie_target': daily_calorie,
                'goal_type': goal_type
            })()
            return _generate_with_ai(
                db, user_id, plan_name, days, pseudo_goal, preferences, health_profile
            )
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}, falling back to recipe-based...")
    
    # PRIORITY 2: Recipe-based generation (only if has recipes AND has goal)
    if has_goal and recipe_count > 0:
        print(f"📋 Using recipe-based generation ({recipe_count} recipes available)...")
        return _generate_with_recipes(
            db, user_id, plan_name, days, goal, preferences, health_profile
        )
    
    # PRIORITY 3: Mock data fallback WITH health profile filter
    print(f"⚠️ Using mock data with health profile filter...")
    return _get_mock_meal_plan(db, user_id, plan_name, days, goal_type, health_profile)


def _generate_with_recipes(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int,
    goal,
    preferences: Optional[Dict] = None,
    health_profile: Optional[Dict] = None
) -> MealPlan:
    """
    Generate meal plan using recipes from database.
    Fully respects health profile (allergies, conditions, preferences).
    """
    from app.services.meal_plan_service import create_meal_plan
    from app.schemas.meal_plan import MealPlanCreate
    
    daily_calories = Decimal(str(goal.daily_calorie_target))
    goal_type_key = goal.goal_type if goal.goal_type in MEAL_DISTRIBUTIONS else "default"
    meal_distribution = MEAL_DISTRIBUTIONS[goal_type_key]
    
    # Extract health profile data
    food_allergies = health_profile.get("food_allergies", []) if health_profile else []
    dietary_preferences = health_profile.get("dietary_preferences", []) if health_profile else []
    health_conditions = health_profile.get("health_conditions", []) if health_profile else []
    
    # Suggest additional tags from health conditions
    suggested_tags = _suggest_tags_from_health_conditions(health_conditions)
    all_preferences_tags = list(set(dietary_preferences + suggested_tags))
    
    if health_profile:
        print(f"🏥 Health profile: {len(food_allergies)} allergens, {len(dietary_preferences)} preferences, {len(health_conditions)} conditions")
        print(f"📋 All preference tags (including from conditions): {all_preferences_tags}")
        if food_allergies:
            print(f"🚫 ALLERGENS TO AVOID: {food_allergies}")
    
    print(f"🎯 Using {goal_type_key} distribution: {dict(meal_distribution)}")
    
    # Calculate meal calorie targets
    meal_targets = {
        meal_type: round_2(daily_calories * ratio)
        for meal_type, ratio in meal_distribution.items()
    }
    
    # Create meal plan
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)
    
    # Store health profile in preferences
    plan_preferences = preferences.copy() if preferences else {}
    if health_profile:
        plan_preferences["health_profile"] = health_profile
    
    meal_plan_data = MealPlanCreate(
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        servings=1,
        preferences=plan_preferences
    )
    
    meal_plan = create_meal_plan(db, user_id, meal_plan_data)
    
    # Generate meals for each day
    recipe_usage_by_date: Dict[date, Set[UUID]] = {}
    recipe_frequency: Dict[UUID, int] = {}
    
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        recipe_usage_by_date[current_date] = set()
        
        # Calculate recipes to exclude (from last 3 days)
        exclude_recent = set()
        for lookback in range(1, VARIETY_LOOKBACK_DAYS + 1):
            lookback_date = current_date - timedelta(days=lookback)
            if lookback_date in recipe_usage_by_date:
                exclude_recent.update(recipe_usage_by_date[lookback_date])
        
        print(f"📅 Day {day_offset + 1} ({current_date}): Excluding {len(exclude_recent)} recipes")
        
        order_index = 0
        for meal_type, target_calories in meal_targets.items():
            # Skip snack if calories too low (optional meal)
            if meal_type == "snack" and float(target_calories) < 100:
                continue
            
            recipe = _find_matching_recipe(
                db=db,
                target_calories=float(target_calories),
                meal_type=meal_type,
                goal_type=goal.goal_type,
                preferences=preferences,
                exclude_recipe_ids=exclude_recent,
                tolerance=0.25,
                food_allergies=food_allergies,
                dietary_preferences=all_preferences_tags,
                health_conditions=health_conditions
            )
            
            if not recipe:
                print(f"   ⚠️ No valid recipe found for {meal_type}")
                continue
            
            quantity = _calculate_quantity(
                recipe_calories=float(recipe.calories_per_serving or 0),
                target_calories=float(target_calories)
            )
            
            item = MealPlanItem(
                meal_plan_id=meal_plan.plan_id,
                food_id=None,
                day_date=current_date,
                meal_type=meal_type,
                serving_size_g=Decimal("100"),
                quantity=Decimal(str(quantity)),
                calories=round_2(target_calories),
                protein_g=round_2(
                    Decimal(str(recipe.protein_per_serving or 0)) * Decimal(str(quantity))
                ) if recipe.protein_per_serving else None,
                carbs_g=round_2(
                    Decimal(str(recipe.carbs_per_serving or 0)) * Decimal(str(quantity))
                ) if recipe.carbs_per_serving else None,
                fat_g=round_2(
                    Decimal(str(recipe.fat_per_serving or 0)) * Decimal(str(quantity))
                ) if recipe.fat_per_serving else None,
                unit="serving",
                notes=f"Recipe: {recipe.name_vi}",
                order_index=order_index
            )
            
            db.add(item)
            recipe_usage_by_date[current_date].add(recipe.recipe_id)
            recipe_frequency[recipe.recipe_id] = recipe_frequency.get(recipe.recipe_id, 0) + 1
            order_index += 1
            
            print(f"   ✅ {meal_type}: {recipe.name_vi}")
    
    db.commit()
    # Force reload items relationship
    db.refresh(meal_plan)
    # Access items to ensure they're loaded
    _ = meal_plan.items
    
    # Variety statistics
    unique_recipes = len(recipe_frequency)
    total_meals = sum(recipe_frequency.values())
    variety_score = (unique_recipes / total_meals * 100) if total_meals > 0 else 0
    
    print(f"\n📊 Variety: {unique_recipes} unique / {total_meals} total ({variety_score:.1f}%)")
    
    return meal_plan


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _find_matching_recipe(
    db: Session,
    target_calories: float,
    meal_type: str,
    goal_type: str,
    preferences: Optional[Dict],
    exclude_recipe_ids: Set[UUID],
    tolerance: float = 0.2,
    food_allergies: Optional[List[str]] = None,
    dietary_preferences: Optional[List[str]] = None,
    health_conditions: Optional[List[str]] = None
) -> Optional[Recipe]:
    """
    Find recipe matching calorie target and health profile requirements.

    STRATEGY:
    1. Calculate calorie range (target ± tolerance)
    2. Filter recipes by:
       - Calorie range
       - NOT in excluded list
       - NOT containing allergens (CRITICAL - STRICT)
       - NOT violating dietary restrictions
    3. Prioritize recipes matching dietary preferences
    4. Score based on preference match

    Args:
        db: Database session
        target_calories: Target calories for this meal
        meal_type: Meal type (breakfast, lunch, dinner, snack)
        goal_type: User's goal type
        preferences: User preferences (categories, tags, etc.)
        exclude_recipe_ids: Already used recipe IDs
        tolerance: Calorie tolerance (0.2 = ±20%)
        food_allergies: List of allergens to EXCLUDE (STRICT)
        dietary_preferences: List of dietary preferences to prioritize
        health_conditions: List of health conditions

    Returns:
        Matching Recipe or None if not found
    """
    
    # Calculate calorie range
    min_calories = target_calories * (1 - tolerance)
    max_calories = target_calories * (1 + tolerance)
    
    # Base query
    query = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        Recipe.calories_per_serving.isnot(None),
        Recipe.calories_per_serving >= min_calories,
        Recipe.calories_per_serving <= max_calories
    )
    
    # Exclude already used recipes
    if exclude_recipe_ids:
        query = query.filter(~Recipe.recipe_id.in_(exclude_recipe_ids))
    
    # Apply user preferences from form
    if preferences:
        # Filter by categories
        if preferences.get("categories"):
            query = query.filter(Recipe.category.in_(preferences["categories"]))
        
        # Filter by tags (ANY match)
        if preferences.get("tags"):
            query = query.filter(Recipe.tags.overlap(preferences["tags"]))
        
        # Filter by max cooking time
        if preferences.get("max_cook_time"):
            max_time = preferences["max_cook_time"]
            query = query.filter(
                (Recipe.prep_time_minutes + Recipe.cook_time_minutes) <= max_time
            )
    
    # Get candidate recipes
    candidates = query.limit(100).all()
    
    if not candidates:
        print(f"⚠️ No recipes found in calorie range {min_calories:.0f}-{max_calories:.0f} for {meal_type}")
        return None
    
    print(f"📋 Found {len(candidates)} candidates for {meal_type}")
    
    # Filter and score
    valid_recipes = []
    
    for recipe in candidates:
        # CRITICAL: Check allergens - STRICT EXCLUSION
        if food_allergies and _check_allergen_in_recipe(recipe, db, food_allergies):
            continue
        
        # Check dietary restrictions - VIOLATION = EXCLUDE
        if dietary_preferences and _check_dietary_restrictions_in_recipe(recipe, dietary_preferences):
            continue
        
        # Score for preference matching
        score = _score_recipe_for_preferences(recipe, dietary_preferences or [], health_conditions)
        valid_recipes.append((score, recipe))
    
    if not valid_recipes:
        print(f"⚠️ No recipes found after health profile filtering for {meal_type}")
        print(f"   Tried to avoid: {food_allergies}")
        print(f"   Tried to respect: {dietary_preferences}")
        return None
    
    # Sort by score (descending)
    valid_recipes.sort(key=lambda x: x[0], reverse=True)
    
    print(f"✅ Found {len(valid_recipes)} valid recipes after filtering")
    
    # Prioritize verified recipes from top scored
    verified_recipes = [r for score, r in valid_recipes if r.is_verified]
    non_verified_recipes = [r for score, r in valid_recipes if not r.is_verified]
    
    # Return verified if available, otherwise from top scored
    if verified_recipes:
        # Return best verified recipe (not random, since we need to respect health profile)
        return verified_recipes[0]
    
    if non_verified_recipes:
        return non_verified_recipes[0]
    
    return None


def _calculate_quantity(
    recipe_calories: float,
    target_calories: float
) -> float:
    """
    Calculate serving quantity to match target calories
    
    Formula: quantity = target_calories / recipe_calories
    Rounds to nearest 0.5 for practical serving sizes
    """
    
    if recipe_calories <= 0:
        return 1.0
    
    quantity = target_calories / recipe_calories
    
    # Round to nearest 0.5
    return round(quantity * 2) / 2


# ==========================================
# SHOPPING LIST GENERATION
# ==========================================

def generate_shopping_list(
    db: Session,
    meal_plan_id: UUID
) -> Dict[str, List[Dict]]:
    """
    Generate shopping list from meal plan
    """
    
    # Get meal plan items
    items = db.query(MealPlanItem).filter(
        MealPlanItem.meal_plan_id == meal_plan_id
    ).all()
    
    if not items:
        return {}
    
    # Accumulate ingredients
    ingredient_totals = {}
    
    for item in items:
        # Extract recipe name from notes
        if not item.notes or not item.notes.startswith("Recipe: "):
            continue
        
        recipe_name = item.notes.replace("Recipe: ", "")
        
        # Find recipe
        recipe = db.query(Recipe).filter(
            Recipe.name_vi == recipe_name,
            Recipe.is_deleted == False
        ).first()
        
        if not recipe:
            continue
        
        # Get ingredients
        for ingredient in recipe.ingredients:
            # Calculate total quantity needed
            ingredient_quantity = float(ingredient.quantity) * float(item.quantity)
            
            # Get food category
            category = "Other"
            if ingredient.food_id:
                food = db.query(Food).filter(
                    Food.food_id == ingredient.food_id
                ).first()
                if food:
                    category = food.category
            
            # Create unique key
            key = f"{ingredient.ingredient_name}_{ingredient.unit}"
            
            if key in ingredient_totals:
                ingredient_totals[key]["quantity"] += ingredient_quantity
            else:
                ingredient_totals[key] = {
                    "name": ingredient.ingredient_name,
                    "quantity": ingredient_quantity,
                    "unit": ingredient.unit,
                    "category": category
                }
    
    # Group by category
    shopping_list = {}
    for ingredient in ingredient_totals.values():
        category = ingredient["category"]
        
        if category not in shopping_list:
            shopping_list[category] = []
        
        shopping_list[category].append({
            "name": ingredient["name"],
            "quantity": round(ingredient["quantity"], 2),
            "unit": ingredient["unit"]
        })
    
    # Sort each category alphabetically
    for category in shopping_list:
        shopping_list[category].sort(key=lambda x: x["name"])
    
    return shopping_list


# ==========================================
# MEAL PLAN ANALYSIS
# ==========================================

def analyze_meal_plan(
    db: Session,
    meal_plan_id: UUID
) -> Dict:
    """
    Analyze meal plan nutrition and balance
    """
    
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == meal_plan_id
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found")
    
    items = meal_plan.items
    
    if not items:
        return {"error": "Meal plan has no items"}
    
    # Calculate totals
    total_days = (meal_plan.end_date - meal_plan.start_date).days + 1
    
    total_calories = sum(float(item.calories or 0) for item in items)
    total_protein = sum(float(item.protein_g or 0) for item in items)
    total_carbs = sum(float(item.carbs_g or 0) for item in items)
    total_fat = sum(float(item.fat_g or 0) for item in items)
    
    # Calculate daily averages
    avg_daily_calories = total_calories / total_days
    avg_daily_protein = total_protein / total_days
    avg_daily_carbs = total_carbs / total_days
    avg_daily_fat = total_fat / total_days
    
    # Calculate macro distribution
    protein_calories = total_protein * 4
    carbs_calories = total_carbs * 4
    fat_calories = total_fat * 9
    total_macro_calories = protein_calories + carbs_calories + fat_calories
    
    if total_macro_calories > 0:
        protein_percent = (protein_calories / total_macro_calories) * 100
        carbs_percent = (carbs_calories / total_macro_calories) * 100
        fat_percent = (fat_calories / total_macro_calories) * 100
    else:
        protein_percent = carbs_percent = fat_percent = 0
    
    # Meal balance
    meal_counts = {}
    for item in items:
        meal_type = item.meal_type
        meal_counts[meal_type] = meal_counts.get(meal_type, 0) + 1
    
    # Variety score
    unique_recipes = len(set(item.notes for item in items if item.notes))
    variety_score = (unique_recipes / len(items)) * 100 if items else 0
    
    return {
        "plan_name": meal_plan.plan_name,
        "days": total_days,
        "total_meals": len(items),
        "daily_averages": {
            "calories": round(avg_daily_calories, 1),
            "protein_g": round(avg_daily_protein, 1),
            "carbs_g": round(avg_daily_carbs, 1),
            "fat_g": round(avg_daily_fat, 1)
        },
        "macro_distribution": {
            "protein_percent": round(protein_percent, 1),
            "carbs_percent": round(carbs_percent, 1),
            "fat_percent": round(fat_percent, 1)
        },
        "meal_balance": meal_counts,
        "variety_score": round(variety_score, 1),
        "unique_recipes": unique_recipes
    }


# ==========================================
# REGENERATE SPECIFIC DAY
# ==========================================

def regenerate_day(
    db: Session,
    meal_plan_id: UUID,
    target_date: date,
    preferences: Optional[Dict] = None,
    health_profile: Optional[Dict] = None
) -> List[MealPlanItem]:
    """
    Regenerate meals for a specific day with health profile support
    """
    
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == meal_plan_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found")
    
    # Validate date
    if target_date < meal_plan.start_date or target_date > meal_plan.end_date:
        raise ValueError(
            f"Date must be between {meal_plan.start_date} and {meal_plan.end_date}"
        )
    
    # Delete existing items for this date
    db.query(MealPlanItem).filter(
        MealPlanItem.meal_plan_id == meal_plan_id,
        MealPlanItem.day_date == target_date
    ).delete()
    
    db.commit()
    
    # Get user goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == meal_plan.user_id,
        UserGoal.is_deleted == False
    ).first()
    
    if not goal:
        raise ValueError("User has no active goal")
    
    daily_calories = Decimal(str(goal.daily_calorie_target))
    
    # Get goal-specific meal distribution
    goal_type_key = goal.goal_type if goal.goal_type in MEAL_DISTRIBUTIONS else "default"
    meal_distribution = MEAL_DISTRIBUTIONS[goal_type_key]
    
    print(f"🎯 Regenerating day with {goal_type_key} distribution")
    
    # Use health profile from meal plan preferences if not provided
    if not health_profile and meal_plan.preferences:
        health_profile = meal_plan.preferences.get("health_profile")
    
    # Extract health profile data
    food_allergies = health_profile.get("food_allergies", []) if health_profile else []
    dietary_preferences = health_profile.get("dietary_preferences", []) if health_profile else []
    health_conditions = health_profile.get("health_conditions", []) if health_profile else []
    suggested_tags = _suggest_tags_from_health_conditions(health_conditions)
    all_preferences_tags = list(set(dietary_preferences + suggested_tags))
    
    # Calculate meal targets
    meal_targets = {
        meal_type: round_2(daily_calories * ratio)
        for meal_type, ratio in meal_distribution.items()
    }
    
    # Get recipes used in nearby dates (for variety)
    exclude_recent = set()
    for lookback in range(1, VARIETY_LOOKBACK_DAYS + 1):
        nearby_date = target_date - timedelta(days=lookback)
        nearby_items = db.query(MealPlanItem).filter(
            MealPlanItem.meal_plan_id == meal_plan_id,
            MealPlanItem.day_date == nearby_date
        ).all()
        
        for item in nearby_items:
            if item.notes and item.notes.startswith("Recipe: "):
                recipe_name = item.notes.replace("Recipe: ", "")
                recipe = db.query(Recipe).filter(
                    Recipe.name_vi == recipe_name,
                    Recipe.is_deleted == False
                ).first()
                if recipe:
                    exclude_recent.add(recipe.recipe_id)
    
    print(f"📅 Excluding {len(exclude_recent)} recipes from last {VARIETY_LOOKBACK_DAYS} days")
    
    # Generate new meals
    new_items = []
    
    for meal_type, target_calories in meal_targets.items():
        recipe = _find_matching_recipe(
            db=db,
            target_calories=float(target_calories),
            meal_type=meal_type,
            goal_type=goal.goal_type,
            preferences=preferences or meal_plan.preferences,
            exclude_recipe_ids=exclude_recent,
            tolerance=0.2,
            food_allergies=food_allergies,
            dietary_preferences=all_preferences_tags,
            health_conditions=health_conditions
        )
        
        if not recipe:
            continue
        
        quantity = _calculate_quantity(
            recipe_calories=float(recipe.calories_per_serving or 0),
            target_calories=float(target_calories)
        )
        
        item = MealPlanItem(
            meal_plan_id=meal_plan_id,
            day_date=target_date,
            meal_type=meal_type,
            serving_size_g=Decimal("100"),
            quantity=Decimal(str(quantity)),
            calories=round_2(target_calories),
            protein_g=round_2(
                Decimal(str(recipe.protein_per_serving or 0)) * Decimal(str(quantity))
            ) if recipe.protein_per_serving else None,
            carbs_g=round_2(
                Decimal(str(recipe.carbs_per_serving or 0)) * Decimal(str(quantity))
            ) if recipe.carbs_per_serving else None,
            fat_g=round_2(
                Decimal(str(recipe.fat_per_serving or 0)) * Decimal(str(quantity))
            ) if recipe.fat_per_serving else None,
            unit="serving",
            notes=f"Recipe: {recipe.name_vi}",
            order_index=list(meal_distribution.keys()).index(meal_type)
        )
        
        db.add(item)
        new_items.append(item)
        print(f"   ✅ {meal_type}: {recipe.name_vi}")
    
    db.commit()
    
    return new_items
