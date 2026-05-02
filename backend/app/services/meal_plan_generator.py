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
import asyncio

from app.models.user import UserGoal
from app.models.recipe import Recipe, RecipeIngredient
from app.models.meal_plan import MealPlan, MealPlanItem
from app.models.food import Food


# ==========================================
# MOCK DATA - Chỉ dùng khi không có AI/DB
# ==========================================

MOCK_BREAKFAST = [
    {"name_vi": "Bánh mì trứng", "calories": 350, "protein": 15, "carbs": 40, "fat": 12},
    {"name_vi": "Xôi gấc", "calories": 350, "protein": 8, "carbs": 55, "fat": 12},
    {"name_vi": "Trứng chiên bánh mì", "calories": 320, "protein": 14, "carbs": 35, "fat": 14},
    {"name_vi": "Cháo gà", "calories": 280, "protein": 18, "carbs": 35, "fat": 8},
    {"name_vi": "Bánh đa cua", "calories": 380, "protein": 16, "carbs": 45, "fat": 14},
]

MOCK_LUNCH = [
    {"name_vi": "Cơm gà xối mỡ", "calories": 600, "protein": 30, "carbs": 70, "fat": 18},
    {"name_vi": "Bún bò Huế", "calories": 550, "protein": 25, "carbs": 60, "fat": 20},
    {"name_vi": "Mì Quảng", "calories": 580, "protein": 24, "carbs": 60, "fat": 22},
    {"name_vi": "Phở bò", "calories": 500, "protein": 22, "carbs": 55, "fat": 16},
    {"name_vi": "Hủ tiếu Mỹ Tho", "calories": 450, "protein": 18, "carbs": 52, "fat": 16},
]

MOCK_DINNER = [
    {"name_vi": "Cá kho tộ", "calories": 380, "protein": 28, "carbs": 20, "fat": 18},
    {"name_vi": "Thịt kho trứng", "calories": 400, "protein": 24, "carbs": 15, "fat": 25},
    {"name_vi": "Gà rang gừng", "calories": 380, "protein": 30, "carbs": 15, "fat": 20},
    {"name_vi": "Canh chua cá lóc", "calories": 220, "protein": 25, "carbs": 12, "fat": 8},
    {"name_vi": "Rau muống xào tỏi + cơm", "calories": 280, "protein": 8, "carbs": 45, "fat": 6},
]

MOCK_SNACK = [
    {"name_vi": "Gỏi cuốn", "calories": 180, "protein": 12, "carbs": 20, "fat": 6},
    {"name_vi": "Chả giò", "calories": 280, "protein": 15, "carbs": 25, "fat": 14},
    {"name_vi": "Rau câu", "calories": 80, "protein": 2, "carbs": 18, "fat": 0},
    {"name_vi": "Trái cây", "calories": 100, "protein": 1, "carbs": 22, "fat": 0},
    {"name_vi": "Sữa chua", "calories": 120, "protein": 8, "carbs": 15, "fat": 4},
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
# Based on nutrition science and goal optimization
MEAL_DISTRIBUTIONS = {
    "weight_loss": {
        "breakfast": Decimal("0.30"),  # 30% - Higher morning for metabolism
        "lunch": Decimal("0.35"),      # 35% - Main meal when active
        "dinner": Decimal("0.25"),     # 25% - Lower evening to avoid fat storage
        "snack": Decimal("0.10")       # 10% - Fill gaps
    },
    "weight_gain": {  # For muscle gain / bulking
        "breakfast": Decimal("0.25"),  # 25% - Moderate start
        "lunch": Decimal("0.30"),      # 30% - Fuel for workout
        "dinner": Decimal("0.35"),     # 35% - Post-workout recovery
        "snack": Decimal("0.10")       # 10% - Pre/post workout
    },
    "maintain": {
        "breakfast": Decimal("0.25"),  # 25% - Standard
        "lunch": Decimal("0.35"),      # 35% - Standard
        "dinner": Decimal("0.30"),     # 30% - Standard
        "snack": Decimal("0.10")       # 10% - Standard
    },
    "healthy_lifestyle": {  # For general health
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
VARIETY_LOOKBACK_DAYS = 3  # Don't repeat recipes from last 3 days

# Decimal constants
DECIMAL_0 = Decimal("0")
DECIMAL_100 = Decimal("100")


def round_2(value: Decimal) -> Decimal:
    """Round Decimal to 2 decimal places"""
    if value is None:
        return DECIMAL_0
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==========================================
# MAIN GENERATION FUNCTION
# ==========================================

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _get_mock_meal_plan(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int,
    goal_type: str = "maintain"
) -> MealPlan:
    """
    Tạo kế hoạch ăn từ dữ liệu mock - ĐÃ SỬA: phân biệt rõ bữa ăn.
    Mỗi ngày: 1 breakfast + 1 lunch + 1 dinner + có thể 1 snack
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)

    meal_plan = MealPlan(
        plan_id=uuid4(),
        user_id=user_id,
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        servings=1,
        preferences={},
        is_active=True,
        is_completed=False
    )
    db.add(meal_plan)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Chọn ngẫu nhiên 1 món từ mỗi bữa
        breakfast_item = random.choice(MOCK_BREAKFAST)
        lunch_item = random.choice(MOCK_LUNCH)
        dinner_item = random.choice(MOCK_DINNER)
        
        # Thứ tự: breakfast=0, lunch=1, dinner=2, snack=3
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
            snack_item = random.choice(MOCK_SNACK)
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
    print(f"✅ Đã tạo mock meal plan: {meal_plan.plan_id} - Đúng cấu trúc bữa ăn!")
    return meal_plan


def generate_meal_plan(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int = 7,
    preferences: Optional[Dict] = None
) -> MealPlan:
    """
    Generate intelligent meal plan - TÍCH HỢP AI.
    
    ALGORITHM:
    1. Thử gọi AI service (Gemini) nếu có
    2. Fallback: dùng recipe từ database nếu có
    3. Fallback cuối: dùng mock data đã sửa (đúng cấu trúc bữa ăn)
    
    Args:
        db: Database session
        user_id: User UUID
        plan_name: Name for the meal plan
        days: Number of days (default 7)
        preferences: Optional filters
    
    Returns:
        Generated MealPlan with MealPlanItems
    """
    
    # 1. Get user's active goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_active == True
    ).first()

    # 2. Check if recipes exist in database
    recipe_count = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        Recipe.calories_per_serving.isnot(None)
    ).count()

    # 3. Try AI first, then recipe-based, then mock
    if goal and goal.daily_calorie_target:
        goal_type = goal.goal_type or "maintain"
        
        # Try AI service
        try:
            print(f"🤖 Attempting AI-powered meal plan generation...")
            return asyncio.run(_generate_with_ai(
                db, user_id, plan_name, days, goal, preferences
            ))
        except Exception as e:
            print(f"⚠️ AI service failed: {e}")
        
        # Fallback: Recipe-based generation
        if recipe_count > 0:
            print(f"📋 Using recipe-based generation...")
            return _generate_with_recipes(
                db, user_id, plan_name, days, goal, preferences
            )
        
        # Final fallback: Mock data
        print(f"⚠️ Using mock data fallback...")
        return _get_mock_meal_plan(db, user_id, plan_name, days, goal_type)
    
    # No goal - use mock with default
    print(f"⚠️ No goal found, using mock data...")
    return _get_mock_meal_plan(db, user_id, plan_name, days, "maintain")


def _generate_with_recipes(
    db: Session,
    user_id: UUID,
    plan_name: str,
    days: int,
    goal,
    preferences: Optional[Dict] = None
) -> MealPlan:
    """
    Generate meal plan using recipes from database.
    Fallback khi AI service không khả dụng.
    """
    from app.services.meal_plan_service import create_meal_plan
    from app.schemas.meal_plan import MealPlanCreate
    
    daily_calories = Decimal(str(goal.daily_calorie_target))
    goal_type_key = goal.goal_type if goal.goal_type in MEAL_DISTRIBUTIONS else "default"
    meal_distribution = MEAL_DISTRIBUTIONS[goal_type_key]
    
    print(f"🎯 Using {goal_type_key} distribution: {dict(meal_distribution)}")
    
    # Calculate meal calorie targets
    meal_targets = {
        meal_type: round_2(daily_calories * ratio)
        for meal_type, ratio in meal_distribution.items()
    }
    
    # Create meal plan
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)
    
    meal_plan_data = MealPlanCreate(
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        servings=1,
        preferences=preferences or {}
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
                tolerance=0.25
            )
            
            if not recipe:
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
    db.refresh(meal_plan)
    
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
    tolerance: float = 0.2
) -> Optional[Recipe]:
    """
    Find recipe matching calorie target and preferences
    
    STRATEGY:
    1. Calculate calorie range (target ± tolerance)
    2. Filter recipes by:
       - Calorie range
       - Not in excluded list
       - User preferences (categories, tags, cook time)
    3. Prioritize verified recipes
    4. Randomly select from top matches for variety
    
    Args:
        db: Database session
        target_calories: Target calories for this meal
        meal_type: Meal type (breakfast, lunch, dinner, snack)
        goal_type: User's goal type
        preferences: User preferences (categories, tags, etc.)
        exclude_recipe_ids: Already used recipe IDs
        tolerance: Calorie tolerance (0.2 = ±20%)
    
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
    
    # Apply user preferences
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
    
    # Prioritize verified recipes
    query = query.order_by(
        Recipe.is_verified.desc(),
        Recipe.favorite_count.desc()
    )
    
    # Get top candidates
    recipes = query.limit(10).all()
    
    if not recipes:
        return None
    
    # Randomly select for variety
    return random.choice(recipes)


def _calculate_quantity(
    recipe_calories: float,
    target_calories: float
) -> float:
    """
    Calculate serving quantity to match target calories
    
    Formula: quantity = target_calories / recipe_calories
    Rounds to nearest 0.5 for practical serving sizes
    
    Args:
        recipe_calories: Calories per serving of recipe
        target_calories: Target calories for meal
    
    Returns:
        Number of servings (rounded to 0.5)
    
    Examples:
        recipe_calories=300, target=450 → 1.5 servings
        recipe_calories=250, target=500 → 2.0 servings
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
    
    ALGORITHM:
    1. Get all meal plan items
    2. Extract recipe names from notes
    3. For each recipe:
       - Get ingredients
       - Multiply by item quantity
       - Accumulate by ingredient name + unit
    4. Group by food category
    
    Args:
        meal_plan_id: Meal plan UUID
    
    Returns:
        Dictionary grouped by category:
        {
            "Vegetables": [
                {"name": "Carrot", "quantity": 500, "unit": "gram"},
                {"name": "Tomato", "quantity": 3, "unit": "pieces"}
            ],
            "Meat": [...],
            ...
        }
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
    
    ANALYSIS:
    1. Daily averages (calories, protein, carbs, fat)
    2. Macro distribution (% from protein, carbs, fat)
    3. Meal balance (count by type)
    4. Variety score (unique recipes / total meals)
    
    Args:
        meal_plan_id: Meal plan UUID
    
    Returns:
        Analysis report with:
        {
            "plan_name": str,
            "days": int,
            "total_meals": int,
            "daily_averages": {
                "calories": float,
                "protein_g": float,
                "carbs_g": float,
                "fat_g": float
            },
            "macro_distribution": {
                "protein_percent": float,
                "carbs_percent": float,
                "fat_percent": float
            },
            "meal_balance": {
                "breakfast": int,
                "lunch": int,
                ...
            },
            "variety_score": float,
            "unique_recipes": int
        }
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
    
    # Calculate macro distribution (calories from each macro)
    # Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
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
    preferences: Optional[Dict] = None
) -> List[MealPlanItem]:
    """
    Regenerate meals for a specific day
    
    PROCESS:
    1. Verify meal plan exists
    2. Delete existing items for target date
    3. Get user goal for calorie targets
    4. Generate new meals using same algorithm
    
    Args:
        meal_plan_id: Meal plan UUID
        target_date: Date to regenerate
        preferences: Optional new preferences
    
    Returns:
        List of new MealPlanItem objects
    
    Raises:
        ValueError: If plan not found or date out of range
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
        UserGoal.is_active == True
    ).first()
    
    if not goal:
        raise ValueError("User has no active goal")
    
    daily_calories = Decimal(str(goal.daily_calorie_target))
    
    # Get goal-specific meal distribution
    goal_type_key = goal.goal_type if goal.goal_type in MEAL_DISTRIBUTIONS else "default"
    meal_distribution = MEAL_DISTRIBUTIONS[goal_type_key]
    
    print(f"🎯 Regenerating day with {goal_type_key} distribution")
    
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
            tolerance=0.2
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