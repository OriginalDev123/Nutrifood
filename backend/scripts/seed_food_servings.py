"""
NutriAI - Food Serving Seed Generator v1.0
Logic: Nạp serving cho toàn bộ foods dựa theo category
"""

import sys
from pathlib import Path
from decimal import Decimal
from sqlalchemy import and_

# Thiết lập path để import module từ thư mục gốc
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.food import Food, FoodServing

db = SessionLocal()

# ==========================================
# SERVING CONFIG THEO CATEGORY
# ==========================================

# Thịt, gia cầm và protein
PROTEIN_SERVINGS = [
    {"description": "100g", "size_g": 100, "is_default": True},
    {"description": "1 phần (150g)", "size_g": 150, "is_default": False},
    {"description": "1 lạng", "size_g": 100, "is_default": False},
]

# Ngũ cốc, tinh bột, carbs
CARBS_SERVINGS = [
    {"description": "100g", "size_g": 100, "is_default": True},
    {"description": "1 bát/chén (vơi)", "size_g": 150, "is_default": False},
    {"description": "1 bát/chén (đầy)", "size_g": 200, "is_default": False},
    {"description": "1 lát (bánh mì)", "size_g": 30, "is_default": False},
]

# Rau củ, chất xơ, vitamin
VEGETABLE_SERVINGS = [
    {"description": "100g", "size_g": 100, "is_default": True},
    {"description": "1 đĩa nhỏ", "size_g": 150, "is_default": False},
    {"description": "1 bát rau", "size_g": 100, "is_default": False},
]

# Trái cây
FRUIT_SERVINGS = [
    {"description": "100g", "size_g": 100, "is_default": True},
    {"description": "1 quả trung bình", "size_g": 150, "is_default": False},
    {"description": "1 miếng", "size_g": 50, "is_default": False},
]

# Dầu ăn, chất béo, gia vị
FAT_SERVINGS = [
    {"description": "1 muỗng cà phê (tsp)", "size_g": 5, "is_default": True},
    {"description": "1 muỗng canh (tbsp)", "size_g": 15, "is_default": False},
    {"description": "100g", "size_g": 100, "is_default": False},
]

# Đồ uống
BEVERAGE_SERVINGS = [
    {"description": "1 ly/cốc", "size_g": 200, "is_default": True},
    {"description": "1 lon/chai nhỏ", "size_g": 330, "is_default": False},
    {"description": "100ml", "size_g": 100, "is_default": False},
]

# Món ăn hỗn hợp/dishes
MIXED_SERVINGS = [
    {"description": "100g", "size_g": 100, "is_default": True},
    {"description": "1 bát/chén (vơi)", "size_g": 150, "is_default": False},
    {"description": "1 đĩa (phần ăn)", "size_g": 200, "is_default": False},
]

# Map categories to servings
SERVINGS_BY_CATEGORY = {
    # Protein group
    "protein": PROTEIN_SERVINGS,
    "plant-protein": PROTEIN_SERVINGS,
    "protein-fat": PROTEIN_SERVINGS,
    "fat-protein": PROTEIN_SERVINGS,
    
    # Carbs group
    "carbs": CARBS_SERVINGS,
    "smart-carbs": CARBS_SERVINGS,
    "pantry": CARBS_SERVINGS,
    
    # Vegetables group
    "fiber": VEGETABLE_SERVINGS,
    "digestive": VEGETABLE_SERVINGS,
    "probiotics": VEGETABLE_SERVINGS,
    "vitamin": VEGETABLE_SERVINGS,
    "minerals": VEGETABLE_SERVINGS,
    "herb": VEGETABLE_SERVINGS,
    "medicinal-herb": VEGETABLE_SERVINGS,
    "antioxidant": VEGETABLE_SERVINGS,
    "anti-inflammatory": VEGETABLE_SERVINGS,
    "detox": VEGETABLE_SERVINGS,
    "folate": VEGETABLE_SERVINGS,
    
    # Fruits
    "fruit": FRUIT_SERVINGS,
    
    # Fats
    "fat": FAT_SERVINGS,
    "fat-mcts": FAT_SERVINGS,
    "sodium": FAT_SERVINGS,
    "sugar": FAT_SERVINGS,
    
    # Beverages
    "hydration": BEVERAGE_SERVINGS,
    "alcohol": BEVERAGE_SERVINGS,
    "electrolytes": BEVERAGE_SERVINGS,
    
    # Mixed dishes
    "mixed": MIXED_SERVINGS,
    
    # Special categories
    "collagen": VEGETABLE_SERVINGS,
    "metabolism": VEGETABLE_SERVINGS,
    "wellness": VEGETABLE_SERVINGS,
    "pH": VEGETABLE_SERVINGS,
}

# Fallback nếu category không xác định
DEFAULT_SERVING = [
    {"description": "100g", "size_g": 100, "is_default": True}
]

# ==========================================
# MAIN SEED FUNCTION
# ==========================================

def seed_food_servings():
    print("=" * 70)
    print("🥣 BẮT ĐẦU NẠP DỮ LIỆU FOOD SERVINGS")
    print("-" * 70)

    count_success = 0
    count_skip = 0
    count_error = 0

    foods = db.query(Food).filter(
        Food.is_deleted == False
    ).all()

    for food in foods:
        try:
            servings_config = SERVINGS_BY_CATEGORY.get(
                food.category,
                DEFAULT_SERVING
            )

            for s in servings_config:
                # Kiểm tra serving đã tồn tại chưa
                exists = db.query(FoodServing).filter(
                    and_(
                        FoodServing.food_id == food.food_id,
                        FoodServing.description == s["description"],
                        FoodServing.is_deleted == False
                    )
                ).first()

                if exists:
                    count_skip += 1
                    continue

                new_serving = FoodServing(
                    food_id=food.food_id,
                    description=s["description"],
                    serving_size_g=Decimal(str(s["size_g"])),
                    is_default=s.get("is_default", False),
                    is_deleted=False
                )

                db.add(new_serving)
                count_success += 1

            db.commit()
            print(f"✅ {food.name_vi} → đã nạp serving")

        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi tại food {food.name_vi}: {str(e)}")
            count_error += 1

    print("-" * 70)
    print(
        f"📊 TỔNG KẾT: "
        f"Thành công: {count_success} | "
        f"Bỏ qua: {count_skip} | "
        f"Lỗi: {count_error}"
    )
    print("=" * 70)

# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    seed_food_servings()
    db.close()
