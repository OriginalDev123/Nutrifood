"""
NutriAI - Test Food Logs Seed Generator v1.0
Logic: Tạo sample food logs cho test users trong 7 ngày gần đây
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta
from random import choice, uniform

# Setup import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import User
from app.models.food import Food, FoodServing
from app.models.food_log import FoodLog

db = SessionLocal()

# ==========================================
# SAMPLE MEAL PATTERNS (for realistic data)
# ==========================================

BREAKFAST_FOODS = [
    "Gạo trắng (Jasmine)",  # Rice
    "Trứng gà",  # Eggs
    "Sữa tươi",  # Milk
    "Chuối",  # Banana
]

LUNCH_DINNER_FOODS = [
    "Gạo trắng (Jasmine)",  # Rice
    "Ức gà (có da)",  # Chicken breast
    "Thịt ba chỉ",  # Pork belly
    "Cá hồi",  # Salmon
    "Cải bó xôi",  # Spinach
    "Cà chua",  # Tomato
]

SNACK_FOODS = [
    "Chuối",  # Banana
    "Táo",  # Apple
    "Cà phê đen",  # Black coffee
    "Sữa chua",  # Yogurt
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_test_user():
    """Get first test user"""
    user = db.query(User).filter(User.email == "test1@nutriai.com").first()
    if not user:
        raise ValueError("Test user not found. Run seed_test_users.py first!")
    return user


def get_food_by_name_vi(name_vi: str):
    """Get food by Vietnamese name (partial match)"""
    food = db.query(Food).filter(
        Food.name_vi.ilike(f"%{name_vi}%"),
        Food.is_deleted == False
    ).first()
    return food


def get_default_serving(food_id):
    """Get default serving size for a food"""
    serving = db.query(FoodServing).filter(
        FoodServing.food_id == food_id,
        FoodServing.is_default == True
    ).first()
    
    if not serving:
        # Fallback to first serving
        serving = db.query(FoodServing).filter(
            FoodServing.food_id == food_id
        ).first()
    
    return serving


def calculate_nutrition(food: Food, portion_grams: Decimal) -> dict:
    """Calculate nutrition for a portion"""
    multiplier = portion_grams / Decimal("100")
    
    return {
        "calories": round(float(food.calories_per_100g * multiplier), 1),
        "protein_g": round(float((food.protein_per_100g or 0) * multiplier), 1),
        "carbs_g": round(float((food.carbs_per_100g or 0) * multiplier), 1),
        "fat_g": round(float((food.fat_per_100g or 0) * multiplier), 1),
        "fiber_g": round(float((food.fiber_per_100g or 0) * multiplier), 1),
    }


# ==========================================
# SEED FUNCTION
# ==========================================

def seed_food_logs_for_week():
    """Create food logs for past 7 days"""
    
    print("=" * 60)
    print("SEED FOOD LOGS (7 DAYS)")
    print("=" * 60)
    
    try:
        user = get_test_user()
        print(f"📝 Creating logs for: {user.full_name} ({user.email})")
        
        total_logs = 0
        
        # Create logs for past 7 days
        for day_offset in range(7):
            log_date = date.today() - timedelta(days=day_offset)
            
            print(f"\n📅 Date: {log_date}")
            
            # Breakfast
            breakfast_food_name = choice(BREAKFAST_FOODS)
            breakfast_food = get_food_by_name_vi(breakfast_food_name)
            
            if breakfast_food:
                serving = get_default_serving(breakfast_food.food_id)
                if serving:
                    portion_g = Decimal(str(uniform(80, 150)))  # Random portion
                    nutrition = calculate_nutrition(breakfast_food, portion_g)
                    
                    log = FoodLog(
                        user_id=user.user_id,
                        food_id=breakfast_food.food_id,
                        food_name=breakfast_food.name_vi,
                        meal_type="breakfast",
                        meal_date=log_date,
                        serving_size_g=serving.serving_size_g,
                        quantity=Decimal("1.0"),
                        calories=Decimal(str(nutrition["calories"])),
                        protein_g=Decimal(str(nutrition["protein_g"])),
                        carbs_g=Decimal(str(nutrition["carbs_g"])),
                        fat_g=Decimal(str(nutrition["fat_g"]))
                    )
                    db.add(log)
                    total_logs += 1
                    print(f"  🍳 Breakfast: {breakfast_food.name_vi} ({nutrition['calories']} kcal)")
            
            # Lunch
            for _ in range(2):  # 2 items for lunch
                lunch_food_name = choice(LUNCH_DINNER_FOODS)
                lunch_food = get_food_by_name_vi(lunch_food_name)
                
                if lunch_food:
                    serving = get_default_serving(lunch_food.food_id)
                    if serving:
                        portion_g = Decimal(str(uniform(100, 200)))
                        nutrition = calculate_nutrition(lunch_food, portion_g)
                        
                        log = FoodLog(
                            user_id=user.user_id,
                            food_id=lunch_food.food_id,
                            food_name=lunch_food.name_vi,
                            meal_type="lunch",
                            meal_date=log_date,
                            serving_size_g=serving.serving_size_g,
                            quantity=Decimal("1.0"),
                            calories=Decimal(str(nutrition["calories"])),
                            protein_g=Decimal(str(nutrition["protein_g"])),
                            carbs_g=Decimal(str(nutrition["carbs_g"])),
                            fat_g=Decimal(str(nutrition["fat_g"]))
                        )
                        db.add(log)
                        total_logs += 1
                        print(f"  🍱 Lunch: {lunch_food.name_vi} ({nutrition['calories']} kcal)")
            
            # Dinner
            for _ in range(2):  # 2 items for dinner
                dinner_food_name = choice(LUNCH_DINNER_FOODS)
                dinner_food = get_food_by_name_vi(dinner_food_name)
                
                if dinner_food:
                    serving = get_default_serving(dinner_food.food_id)
                    if serving:
                        portion_g = Decimal(str(uniform(100, 200)))
                        nutrition = calculate_nutrition(dinner_food, portion_g)
                        
                        log = FoodLog(
                            user_id=user.user_id,
                            food_id=dinner_food.food_id,
                            food_name=dinner_food.name_vi,
                            meal_type="dinner",
                            meal_date=log_date,
                            serving_size_g=serving.serving_size_g,
                            quantity=Decimal("1.0"),
                            calories=Decimal(str(nutrition["calories"])),
                            protein_g=Decimal(str(nutrition["protein_g"])),
                            carbs_g=Decimal(str(nutrition["carbs_g"])),
                            fat_g=Decimal(str(nutrition["fat_g"]))
                        )
                        db.add(log)
                        total_logs += 1
                        print(f"  🍽️  Dinner: {dinner_food.name_vi} ({nutrition['calories']} kcal)")
            
            # Snack (random, 50% chance)
            if day_offset % 2 == 0:  # Every other day
                snack_food_name = choice(SNACK_FOODS)
                snack_food = get_food_by_name_vi(snack_food_name)
                
                if snack_food:
                    serving = get_default_serving(snack_food.food_id)
                    if serving:
                        portion_g = Decimal(str(uniform(50, 100)))
                        nutrition = calculate_nutrition(snack_food, portion_g)
                        
                        log = FoodLog(
                            user_id=user.user_id,
                            food_id=snack_food.food_id,
                            food_name=snack_food.name_vi,
                            meal_type="snack",
                            meal_date=log_date,
                            serving_size_g=serving.serving_size_g,
                            quantity=Decimal("1.0"),
                            calories=Decimal(str(nutrition["calories"])),
                            protein_g=Decimal(str(nutrition["protein_g"])),
                            carbs_g=Decimal(str(nutrition["carbs_g"])),
                            fat_g=Decimal(str(nutrition["fat_g"]))
                        )
                        db.add(log)
                        total_logs += 1
                        print(f"  🍿 Snack: {snack_food.name_vi} ({nutrition['calories']} kcal)")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ SUMMARY: Created {total_logs} food logs for 7 days")
        print("=" * 60)
        
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        db.rollback()


if __name__ == "__main__":
    try:
        seed_food_logs_for_week()
    finally:
        db.close()
