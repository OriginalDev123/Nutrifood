"""
NutriAI - Recipe Ingredient & Auto-Nutrition Sync v1.1
Logic: 
1. Seed bảng recipe_ingredients.
2. Tự động tính tổng Calo, Protein, Carbs, Fat, Fiber từ Foods.
3. Cập nhật lại các cột tương ứng trong bảng Recipes.
"""

import sys
from pathlib import Path
from decimal import Decimal
from sqlalchemy import and_

# Setup import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.food import Food
from app.models.recipe import Recipe, RecipeIngredient


db = SessionLocal()

# ==========================================
# DATA CONFIG (NHÓM R1: EAT CLEAN)
# ==========================================
RECIPE_INGREDIENTS_DATA = [
    
    {
        "recipe_name_en": "Pan-seared Chicken with Passion Fruit Sauce",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 180, "unit": "g", "notes": "Nguyên liệu chính giàu đạm"},
            {"food_name_en": "Passion Fruit (Juice)", "qty": 40, "unit": "ml", "notes": "Lọc bỏ hạt"},
            {"food_name_en": "Honey", "qty": 10, "unit": "g", "notes": "Tạo độ ngọt tự nhiên"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 5, "unit": "ml", "notes": "Áp chảo"},
            {"food_name_en": "Asparagus", "qty": 50, "unit": "g", "notes": "Ăn kèm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Vietnamese Shredded Chicken Salad",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 150, "unit": "g", "notes": "Luộc chín xé phay"},
            {"food_name_en": "Onion", "qty": 50, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Carrot", "qty": 30, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Stevia Sweetener", "qty": 5, "unit": "g", "notes": "Pha nước mắm"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Pha nước mắm"},
            {"food_name_en": "Lime", "qty": 15, "unit": "g", "notes": "Lấy nước cốt"},
            {"food_name_en": "Chili Pepper", "qty": 2, "unit": "g", "notes": "Băm nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Rosemary Roasted Chicken Breast",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 190, "unit": "g", "notes": "Nguyên liệu chính giàu đạm"},
            {"food_name_en": "Fresh Rosemary", "qty": 5, "unit": "g", "notes": "Băm nhỏ để ướp"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 8, "unit": "ml", "notes": "Giúp gà không bị khô khi nướng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị tạo độ thơm nồng"}
        ]
    },
    {
        "recipe_name_en": "Asparagus Stuffed Chicken Rolls",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 175, "unit": "g", "notes": "Lạng mỏng để cuộn"},
            {"food_name_en": "Asparagus", "qty": 120, "unit": "g", "notes": "Chọn ngọn non, giòn"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 10, "unit": "ml", "notes": "Áp chảo tạo độ bóng và béo"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Foil-Wrapped Steamed Chicken with Mushrooms",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 180, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Enoki Mushroom", "qty": 100, "unit": "g", "notes": "Trải đều dưới giấy bạc"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Thái sợi khử mùi"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Hành lá tạo mùi thơm"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Ướp gà"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Chicken Veggie Balls",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 160, "unit": "g", "notes": "Xay nhuyễn"},
            {"food_name_en": "Broccoli", "qty": 100, "unit": "g", "notes": "Băm nhuyễn"},
            {"food_name_en": "Carrot", "qty": 50, "unit": "g", "notes": "Băm nhuyễn"},
            {"food_name_en": "Corn Starch", "qty": 5, "unit": "g", "notes": "Chất kết dính"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xịt nhẹ lớp màng để nướng không khô"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Eat Clean Chicken Curry with Nut Milk",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 160, "unit": "g", "notes": "Cắt miếng vuông"},
            {"food_name_en": "Sweet Potato", "qty": 130, "unit": "g", "notes": "Carb chậm giúp no lâu"},
            {"food_name_en": "Almond Milk", "qty": 100, "unit": "ml", "notes": "Thay cho nước cốt dừa béo"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Hành tím xào thơm"},
            {"food_name_en": "Bột Cà ri", "qty": 5, "unit": "g", "notes": "Gia vị chủ đạo"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào săn gà"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Chicken Stir-fry with Cashews and Bell Peppers",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 170, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Cashew", "qty": 25, "unit": "g", "notes": "Nguồn chất béo tốt"},
            {"food_name_en": "Red Bell Pepper", "qty": 60, "unit": "g", "notes": "Giàu Vitamin C"},
            {"food_name_en": "Green Bell Pepper", "qty": 40, "unit": "g", "notes": "Tạo màu sắc đa dạng"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 5, "unit": "ml", "notes": "Xào nhanh tay"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nêm nếm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Garlic Butter Chicken Breast",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 185, "unit": "g", "notes": "Nguyên liệu chính"},
            {"food_name_en": "Unsalted Butter", "qty": 15, "unit": "g", "notes": "Tạo độ béo và thơm"},
            {"food_name_en": "Garlic", "qty": 15, "unit": "g", "notes": "Tỏi băm thật nhiều"},
            {"food_name_en": "Parsley", "qty": 2, "unit": "g", "notes": "Trang trí và tạo mùi"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Chicken with Pesto Sauce",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 170, "unit": "g", "notes": "Áp chảo mọng nước"},
            {"food_name_en": "Thai Basil", "qty": 20, "unit": "g", "notes": "Thành phần chính của sốt Pesto"},
            {"food_name_en": "Cashew", "qty": 10, "unit": "g", "notes": "Tạo độ bùi cho sốt"},
            {"food_name_en": "Parmesan Cheese", "qty": 10, "unit": "g", "notes": "Tạo độ mặn và béo"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 15, "unit": "ml", "notes": "Nền tảng của sốt Pesto"},
            {"food_name_en": "Garlic", "qty": 3, "unit": "g", "notes": "Gia vị cho sốt"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Northwestern Vietnamese Spiced Chicken",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 200, "unit": "g", "notes": "Nguyên liệu chính giàu đạm"},
            {"food_name_en": "Mac Khen Seeds", "qty": 3, "unit": "g", "notes": "Rang thơm, giã nhỏ"},
            {"food_name_en": "Hat Doi Seeds", "qty": 2, "unit": "g", "notes": "Rang thơm, giã nhỏ"},
            {"food_name_en": "Soybean Oil", "qty": 3, "unit": "ml", "notes": "Giúp gia vị bám đều"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành băm nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Hasselback Chicken with Tomato and Mozzarella",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 190, "unit": "g", "notes": "Khía rãnh thuyền"},
            {"food_name_en": "Fresh Mozzarella", "qty": 50, "unit": "g", "notes": "Kẹp vào rãnh thịt"},
            {"food_name_en": "Tomato", "qty": 60, "unit": "g", "notes": "Thái lát kẹp cùng phô mai"},
            {"food_name_en": "Dried Oregano", "qty": 1, "unit": "g", "notes": "Rắc lên mặt"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 5, "unit": "ml", "notes": "Rưới nhẹ trước khi nướng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Chicken Stir-fry with Broccoli and Shiitake",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 180, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Broccoli", "qty": 150, "unit": "g", "notes": "Chần sơ trước khi xào"},
            {"food_name_en": "Shiitake Mushroom", "qty": 50, "unit": "g", "notes": "Nấm tươi hoặc khô đã ngâm nở"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Tạo vị Umami"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Dầu xào"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Low-carb Chicken Seaweed Rolls",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 165, "unit": "g", "notes": "Băm nhỏ và xào chín"},
            {"food_name_en": "Nori (Fresh)", "qty": 5, "unit": "g", "notes": "2 lá rong biển lớn"},
            {"food_name_en": "Cucumber", "qty": 40, "unit": "g", "notes": "Thái sợi dài"},
            {"food_name_en": "Carrot", "qty": 30, "unit": "g", "notes": "Thái sợi dài"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nước chấm kèm"},
            {"food_name_en": "Sesame Oil", "qty": 3, "unit": "ml", "notes": "Quét lên lá rong biển cho thơm"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Zucchini Noodle Chicken Soup",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 150, "unit": "g", "notes": "Thịt gà chính"},
            {"food_name_en": "Zucchini", "qty": 150, "unit": "g", "notes": "Bào sợi thay bánh phở"},
            {"food_name_en": "Chicken Carcass", "qty": 100, "unit": "g", "notes": "Ninh lấy nước dùng (không ăn xương)"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Nướng thơm nấu nước dùng"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Nấu nước dùng"},
            {"food_name_en": "Star Anise", "qty": 1, "unit": "g", "notes": "Gia vị nước dùng"},
            {"food_name_en": "Cinnamon Powder", "qty": 1, "unit": "g", "notes": "Gia vị nước dùng"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nước dùng"}
        ]
    },
    
    {
        "recipe_name_en": "Ginger and Turmeric Chicken Stew",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 190, "unit": "g", "notes": "Thái miếng vuông"},
            {"food_name_en": "Ginger", "qty": 15, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Turmeric", "qty": 10, "unit": "g", "notes": "Nghệ tươi giã nhỏ"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Phi thơm hành"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị kho"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành tím băm"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Chicken & Avocado Salad",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 155, "unit": "g", "notes": "Áp chảo hoặc nướng"},
            {"food_name_en": "Trái Bơ", "qty": 100, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Lettuce", "qty": 100, "unit": "g", "notes": "Rau nền cho salad"},
            {"food_name_en": "Cherry Tomato", "qty": 50, "unit": "g", "notes": "Tạo vị chua ngọt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Thành phần sốt"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 10, "unit": "ml", "notes": "Thành phần sốt hỗ trợ đốt mỡ"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Cân bằng vị sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Honey Teriyaki Chicken Breast",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 185, "unit": "g", "notes": "Cắt miếng vuông"},
            {"food_name_en": "Honey", "qty": 15, "unit": "g", "notes": "Thay thế đường cát"},
            {"food_name_en": "Soy Sauce", "qty": 15, "unit": "ml", "notes": "Nền sốt Teriyaki"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Gừng băm tạo mùi"},
            {"food_name_en": "Hạt Vừng (Mè)", "qty": 5, "unit": "g", "notes": "Rắc trang trí"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo gà"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },

    {
        "recipe_name_en": "Pan-seared Chicken with Greek Yogurt & Dill Sauce",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 170, "unit": "g", "notes": "Áp chảo vàng hai mặt"},
            {"food_name_en": "Greek Yogurt (Original)", "qty": 50, "unit": "g", "notes": "Làm nền sốt Probiotics"},
            {"food_name_en": "Dill", "qty": 5, "unit": "g", "notes": "Băm nhỏ trộn sốt"},
            {"food_name_en": "Lime", "qty": 5, "unit": "g", "notes": "Lấy nước cốt trộn sốt"},
            {"food_name_en": "Garlic", "qty": 2, "unit": "g", "notes": "Nghiền nhỏ trộn sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo gà"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Goji Berry & Red Date Chicken Stew",
        "ingredients": [
            {"food_name_en": "Chicken Breast Boneless Skinless", "qty": 185, "unit": "g", "notes": "Thái miếng to"},
            {"food_name_en": "Dried Red Dates", "qty": 20, "unit": "g", "notes": "Tạo vị ngọt thanh và bổ máu"},
            {"food_name_en": "Goji Berries", "qty": 10, "unit": "g", "notes": "Tăng cường chất chống oxy hóa"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái lát làm ấm nước dùng"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Purified Water", "qty": 300, "unit": "ml", "notes": "Nước hầm"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Salmon with Asparagus Sauce",
        "ingredients": [
            {"food_name_en": "Salmon", "qty": 170, "unit": "g", "notes": "Áp chảo mặt da cho giòn"},
            {"food_name_en": "Asparagus", "qty": 150, "unit": "g", "notes": "100g xào, 50g xay làm sốt"},
            {"food_name_en": "Almond Milk", "qty": 50, "unit": "ml", "notes": "Nền sốt măng tây"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 7, "unit": "ml", "notes": "Áp chảo cá và xào măng"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Shrimp in Coconut Water",
        "ingredients": [
            {"food_name_en": "Whiteleg Shrimp", "qty": 160, "unit": "g", "notes": "Lọc chỉ lưng"},
            {"food_name_en": "Coconut Water", "qty": 150, "unit": "ml", "notes": "Dùng hấp/luộc lấy vị ngọt"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Khử tanh"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Tạo mùi thơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Squid with Ginger",
        "ingredients": [
            {"food_name_en": "Squid", "qty": 205, "unit": "g", "notes": "Mực ống tươi, làm sạch"},
            {"food_name_en": "Ginger", "qty": 15, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Cắt khúc"},
            {"food_name_en": "Chili Pepper", "qty": 3, "unit": "g", "notes": "Ớt sừng thái lát"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Gia vị ướp nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Mackerel Baked in Foil",
        "ingredients": [
            {"food_name_en": "Mackerel", "qty": 205, "unit": "g", "notes": "Thân cá thu chắc thịt"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành băm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Tiêu đen"},
            {"food_name_en": "Soybean Oil", "qty": 2, "unit": "ml", "notes": "Quét nhẹ mặt giấy bạc chống dính"}
        ]
    },
    
    {
        "recipe_name_en": "Lemon Butter Salmon",
        "ingredients": [
            {"food_name_en": "Salmon", "qty": 160, "unit": "g", "notes": "Áp chảo vừa chín tới"},
            {"food_name_en": "Unsalted Butter", "qty": 15, "unit": "g", "notes": "Đun chảy làm sốt"},
            {"food_name_en": "Lemon", "qty": 20, "unit": "g", "notes": "Lấy nước cốt và vỏ bào"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 5, "unit": "ml", "notes": "Quét mặt chảo áp chảo"},
            {"food_name_en": "Parsley", "qty": 2, "unit": "g", "notes": "Trang trí"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Shrimp and Cauliflower with Roasted Sesame Sauce",
        "ingredients": [
            {"food_name_en": "Whiteleg Shrimp", "qty": 150, "unit": "g", "notes": "Bóc vỏ, bỏ chỉ lưng"},
            {"food_name_en": "Cauliflower", "qty": 150, "unit": "g", "notes": "Cắt nhỏ, chần sơ"},
            {"food_name_en": "Roasted Sesame Dressing", "qty": 30, "unit": "ml", "notes": "Trộn sau khi tắt bếp"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm xào tôm"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Dầu xào"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Hong Kong Style Steamed Sea Bass",
        "ingredients": [
            {"food_name_en": "Barramundi", "qty": 210, "unit": "g", "notes": "Cá tươi, khía thân"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Nền nước sốt"},
            {"food_name_en": "Sesame Oil", "qty": 8, "unit": "ml", "notes": "Tạo mùi thơm đặc trưng"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái sợi hấp cùng cá"},
            {"food_name_en": "Scallion", "qty": 15, "unit": "g", "notes": "Thái sợi trang trí"},
            {"food_name_en": "Chicken Carcass", "qty": 30, "unit": "ml", "notes": "Nước dùng ninh xương pha sốt"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Seameed Salad with Seared Tuna",
        "ingredients": [
            {"food_name_en": "Tuna", "qty": 160, "unit": "g", "notes": "Áp chảo Medium Rare"},
            {"food_name_en": "Nori (Fresh)", "qty": 40, "unit": "g", "notes": "Rong biển tươi trộn salad"},
            {"food_name_en": "Cucumber", "qty": 80, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Thành phần sốt"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 10, "unit": "ml", "notes": "Thành phần sốt"},
            {"food_name_en": "Black Pepper", "qty": 3, "unit": "g", "notes": "Tẩm mặt cá ngừ"},
            {"food_name_en": "Hạt Vừng (Mè)", "qty": 3, "unit": "g", "notes": "Rắc lên cá"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fry Squid with Celery and Bell Peppers",
        "ingredients": [
            {"food_name_en": "Squid", "qty": 190, "unit": "g", "notes": "Khứa caro, thái miếng"},
            {"food_name_en": "Celery", "qty": 100, "unit": "g", "notes": "Cắt khúc"},
            {"food_name_en": "Red Bell Pepper", "qty": 80, "unit": "g", "notes": "Thái miếng vuông"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nếm"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Air-fried Garlic Chili Cod",
        "ingredients": [
            {"food_name_en": "Cod", "qty": 195, "unit": "g", "notes": "Phi lê cá trắng"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 7, "unit": "ml", "notes": "Xoa đều mặt cá"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Dùng tỏi băm hoặc bột tỏi"},
            {"food_name_en": "Paprika Powder", "qty": 3, "unit": "g", "notes": "Tạo màu và mùi"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Bitter Melon with Shrimp Filling",
        "ingredients": [
            {"food_name_en": "Whiteleg Shrimp", "qty": 145, "unit": "g", "notes": "Băm nhuyễn làm nhân"},
            {"food_name_en": "Bitter Melon", "qty": 200, "unit": "g", "notes": "Bỏ ruột, cắt khoanh"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành tím băm trộn nhân"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Gia vị trộn nhân"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị trộn nhân"}
        ]
    },
    
    {
        "recipe_name_en": "Seafood Clear Soup with Herbs",
        "ingredients": [
            {"food_name_en": "Whiteleg Shrimp", "qty": 100, "unit": "g", "notes": "Nguyên con bóc vỏ"},
            {"food_name_en": "Squid", "qty": 80, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Shiitake Mushroom", "qty": 30, "unit": "g", "notes": "Thái lát tạo vị Umami"},
            {"food_name_en": "Brown Shimeji Mushroom", "qty": 50, "unit": "g", "notes": "Nấm linh chi tươi"},
            {"food_name_en": "Black Cardamom", "qty": 1, "unit": "g", "notes": "1 quả nhỏ nấu nước dùng"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Gừng nướng thơm"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Nêm nước dùng"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Salmon Patties",
        "ingredients": [
            {"food_name_en": "Salmon", "qty": 140, "unit": "g", "notes": "Băm nhỏ hoặc xay sơ"},
            {"food_name_en": "Chicken Egg", "qty": 30, "unit": "g", "notes": "Dùng làm chất kết dính"},
            {"food_name_en": "Onion", "qty": 20, "unit": "g", "notes": "Nghiền nhỏ lấy hương vị"},
            {"food_name_en": "Dill", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Healthy Grilled Oysters with Scallion Oil",
        "ingredients": [
            {"food_name_en": "Oyster", "qty": 200, "unit": "g", "notes": "Trọng lượng phần thịt hàu"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Phi hành lá"},
            {"food_name_en": "Scallion", "qty": 15, "unit": "g", "notes": "Thái nhỏ làm mỡ hành"},
            {"food_name_en": "Peanut", "qty": 5, "unit": "g", "notes": "Rang chín, giã dập"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Nêm rất nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Grilled Amberjack with Green Chili Salt",
        "ingredients": [
            {"food_name_en": "Amberjack", "qty": 180, "unit": "g", "notes": "Khứa sâu thân cá"},
            {"food_name_en": "Chili Pepper", "qty": 10, "unit": "g", "notes": "Ớt xiêm xanh"},
            {"food_name_en": "Lime", "qty": 15, "unit": "g", "notes": "Lấy nước cốt"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 10, "unit": "ml", "notes": "Hòa cùng muối ớt để xoa mặt cá"},
            {"food_name_en": "Salt", "qty": 5, "unit": "g", "notes": "Muối hột giã nhỏ"},
            {"food_name_en": "Fresh Rosemary", "qty": 2, "unit": "g", "notes": "Hoặc lá chanh thái sợi"}
        ]
    },
    
    {
        "recipe_name_en": "Honey Satay Grilled Octopus",
        "ingredients": [
            {"food_name_en": "Octopus", "qty": 235, "unit": "g", "notes": "Làm sạch, để nguyên hoặc cắt miếng lớn"},
            {"food_name_en": "Honey", "qty": 15, "unit": "g", "notes": "Tạo màu nâu bóng và vị ngọt"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nền sốt ướp"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Thành phần của sa tế ít dầu"},
            {"food_name_en": "Chili Pepper", "qty": 5, "unit": "g", "notes": "Ớt băm cho sa tế"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm ướp gà"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Khử tanh khi sơ chế"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Red Tilapia Rolls with Enoki Mushrooms",
        "ingredients": [
            {"food_name_en": "Red Tilapia", "qty": 180, "unit": "g", "notes": "Lạng phi lê mỏng"},
            {"food_name_en": "Enoki Mushroom", "qty": 100, "unit": "g", "notes": "Cuộn bên trong cá"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Rưới lên trước khi hấp"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Khử tanh"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Hành lá chần để buộc cuộn cá"},
            {"food_name_en": "Chili Pepper", "qty": 2, "unit": "g", "notes": "Trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Grilled Shrimp with Chimichurri Sauce",
        "ingredients": [
            {"food_name_en": "Whiteleg Shrimp", "qty": 160, "unit": "g", "notes": "Tôm nguyên vỏ, xẻ lưng"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 12, "unit": "ml", "notes": "Nền sốt Chimichurri"},
            {"food_name_en": "Parsley", "qty": 15, "unit": "g", "notes": "Ngò tây băm nhỏ cho sốt"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ cho sốt"},
            {"food_name_en": "Lemon", "qty": 10, "unit": "g", "notes": "Lấy nước cốt pha sốt"},
            {"food_name_en": "Paprika Powder", "qty": 2, "unit": "g", "notes": "Tạo vị cay nhẹ và màu sắc"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Scallops with Cauliflower Rice",
        "ingredients": [
            {"food_name_en": "Scallops", "qty": 155, "unit": "g", "notes": "Thấm thật khô trước khi áp chảo"},
            {"food_name_en": "Broccoli", "qty": 150, "unit": "g", "notes": "Băm/xay nhỏ làm cơm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Áp chảo và xào cơm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm xào cơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Mediterranean Mackerel Stew",
        "ingredients": [
            {"food_name_en": "Mackerel", "qty": 190, "unit": "g", "notes": "Cắt lát dày, áp chảo sơ"},
            {"food_name_en": "Cherry Tomato", "qty": 100, "unit": "g", "notes": "Bổ đôi nấu sốt"},
            {"food_name_en": "Olives", "qty": 30, "unit": "g", "notes": "Quả ô liu cắt lát hoặc để nguyên"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo cá"},
            {"food_name_en": "Basil", "qty": 5, "unit": "g", "notes": "Lá húng tây tươi"},
            {"food_name_en": "Purified Water", "qty": 50, "unit": "ml", "notes": "Nước lọc hầm cá"}
        ]
    },
    
    {
        "recipe_name_en": "Lean Beef Tenderloin Steak with Salad",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 175, "unit": "g", "notes": "Để nhiệt độ phòng trước khi áp chảo"},
            {"food_name_en": "Lettuce", "qty": 100, "unit": "g", "notes": "Salad ăn kèm"},
            {"food_name_en": "Cherry Tomato", "qty": 50, "unit": "g", "notes": "Salad ăn kèm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Áp chảo và làm sốt dầu giấm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Beef and Broccoli Stir-fry",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 145, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Broccoli", "qty": 180, "unit": "g", "notes": "Nguồn Vitamin C hỗ trợ hấp thụ sắt"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Ướp bò"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Soybean Oil", "qty": 8, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Boiled Lean Pork Loin with Garlic Fish Sauce",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 185, "unit": "g", "notes": "Thái lát mỏng sau khi luộc"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Luộc cùng thịt"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành tím luộc cùng thịt"},
            {"food_name_en": "Fish Sauce", "qty": 15, "unit": "ml", "notes": "Làm nước mắm tỏi ớt"},
            {"food_name_en": "Stevia Sweetener", "qty": 5, "unit": "g", "notes": "Pha nước chấm"},
            {"food_name_en": "Lime", "qty": 10, "unit": "g", "notes": "Nước cốt chanh cho nước chấm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm cho nước chấm"}
        ]
    },
    
    {
        "recipe_name_en": "Grilled Beef Wrapped in Betel Leaves",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 155, "unit": "g", "notes": "Băm nhỏ làm nhân"},
            {"food_name_en": "Wild Betel Leaf", "qty": 30, "unit": "g", "notes": "Khoảng 15-20 lá để cuốn"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Phết mặt lá trước khi nướng"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Ướp thịt"},
            {"food_name_en": "Onion", "qty": 5, "unit": "g", "notes": "Hành tím ướp thịt"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị ướp"}
        ]
    },
    
    {
        "recipe_name_en": "Beef Shank Soaked in Pepper Fish Sauce",
        "ingredients": [
            {"food_name_en": "Beef Shank", "qty": 190, "unit": "g", "notes": "Luộc kỹ cho mềm gân"},
            {"food_name_en": "Honey", "qty": 15, "unit": "g", "notes": "Thay cho đường trong nước ngâm"},
            {"food_name_en": "Fish Sauce", "qty": 30, "unit": "ml", "notes": "Nước cốt ngâm"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 20, "unit": "ml", "notes": "Tạo độ chua thanh và làm mềm thịt"},
            {"food_name_en": "Black Pepper", "qty": 10, "unit": "g", "notes": "Tiêu xanh hoặc tiêu đen nguyên hạt"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Khử mùi khi luộc"},
            {"food_name_en": "Lemongrass", "qty": 10, "unit": "g", "notes": "Khử mùi khi luộc"}
        ]
    },
    
    {
        "recipe_name_en": "Five-Spice Roasted Pork Loin",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 180, "unit": "g", "notes": "Phần nạc nhất của heo"},
            {"food_name_en": "Five Spice Powder", "qty": 3, "unit": "g", "notes": "Tạo mùi thơm"},
            {"food_name_en": "Honey", "qty": 10, "unit": "g", "notes": "Giúp bề mặt thịt có màu nâu đẹp"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị ướp chính"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ ướp cùng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Quick-seared Beef with Tonkin Jasmine Flowers",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 145, "unit": "g", "notes": "Thái lát thật mỏng"},
            {"food_name_en": "Tonkin Jasmine Flowers", "qty": 150, "unit": "g", "notes": "Xào nhanh tay lửa lớn"},
            {"food_name_en": "Soybean Oil", "qty": 10, "unit": "ml", "notes": "Dùng cho kỹ thuật né lửa lớn"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Oyster Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị ướp bò"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Apple Glazed Pork Loin",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 175, "unit": "g", "notes": "Dần nhẹ cho mềm"},
            {"food_name_en": "Apple", "qty": 80, "unit": "g", "notes": "Băm nhuyễn làm sốt và thái lát"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Cân bằng vị chua của táo"},
            {"food_name_en": "Lime", "qty": 5, "unit": "g", "notes": "Lấy nước cốt cho sốt"},
            {"food_name_en": "Olive Oil (EVOO)", "qty": 5, "unit": "ml", "notes": "Áp chảo thịt heo"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Southern Vietnamese Beef Salad (Low-carb Style)",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 135, "unit": "g", "notes": "Thái lát mỏng, xào tỏi"},
            {"food_name_en": "Dried Brown Rice Vermicelli", "qty": 30, "unit": "g", "notes": "Luộc chín, để ráo"},
            {"food_name_en": "Lettuce", "qty": 100, "unit": "g", "notes": "Thái sợi làm nền salad"},
            {"food_name_en": "Giá đỗ", "qty": 50, "unit": "g", "notes": "Chần sơ"},
            {"food_name_en": "Peanut", "qty": 10, "unit": "g", "notes": "Rang chín, giã dập"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào thịt bò"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Pha nước trộn"},
            {"food_name_en": "Stevia Sweetener", "qty": 5, "unit": "g", "notes": "Pha nước trộn"}
        ]
    },
    
    {
        "recipe_name_en": "Beef Shank Stew with Green Peppercorn & Radish",
        "ingredients": [
            {"food_name_en": "Beef Shank", "qty": 180, "unit": "g", "notes": "Thái miếng vuông"},
            {"food_name_en": "Củ cải trắng", "qty": 150, "unit": "g", "notes": "Tạo vị ngọt thanh"},
            {"food_name_en": "Green Peppercorns", "qty": 15, "unit": "g", "notes": "Để nguyên chùm hầm lấy tinh dầu"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Khử mùi khi luộc sơ"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Nêm nước hầm"},
            {"food_name_en": "Purified Water", "qty": 400, "unit": "ml", "notes": "Nước dùng hầm"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fry Pork Loin with Rainbow Bell Peppers",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 175, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Red Bell Pepper", "qty": 60, "unit": "g", "notes": "Cắt miếng vuông"},
            {"food_name_en": "Yellow Bell Pepper", "qty": 60, "unit": "g", "notes": "Cắt miếng vuông"},
            {"food_name_en": "Green Bell Pepper", "qty": 60, "unit": "g", "notes": "Cắt miếng vuông"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị ướp"},
            {"food_name_en": "Soybean Oil", "qty": 6, "unit": "ml", "notes": "Xào nhanh lửa lớn"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Khử mùi"}
        ]
    },
    
    {
        "recipe_name_en": "Grilled Beef Rolls with Enoki Mushrooms",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 155, "unit": "g", "notes": "Lạng lát mỏng, bản to"},
            {"food_name_en": "Enoki Mushroom", "qty": 100, "unit": "g", "notes": "Nhân cuộn"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Thành phần sốt phết"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Thành phần sốt phết"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Hòa vào sốt để thịt không khô"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Gia vị sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Pork Loin with Oyster Sauce and Cauliflower",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 170, "unit": "g", "notes": "Thái lát mỏng, chần sơ"},
            {"food_name_en": "Cauliflower", "qty": 180, "unit": "g", "notes": "Cắt miếng nhỏ, hấp chín tới"},
            {"food_name_en": "Oyster Sauce", "qty": 10, "unit": "ml", "notes": "Dùng loại ít muối (Low-sodium)"},
            {"food_name_en": "Soybean Oil", "qty": 4, "unit": "ml", "notes": "Xào thịt heo"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Rosemary Pan-Seared Beef",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 165, "unit": "g", "notes": "Để nguyên miếng dày"},
            {"food_name_en": "Fresh Rosemary", "qty": 5, "unit": "g", "notes": "Áp chảo cùng để lấy mùi"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 12, "unit": "ml", "notes": "Áp chảo lửa lớn"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pork Loin Stew with Pineapple",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 165, "unit": "g", "notes": "Thái miếng vuông"},
            {"food_name_en": "Pineapple", "qty": 100, "unit": "g", "notes": "Thái lát tam giác"},
            {"food_name_en": "Fish Sauce", "qty": 15, "unit": "ml", "notes": "Gia vị kho chính"},
            {"food_name_en": "Onion", "qty": 10, "unit": "g", "notes": "Hành tím băm"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Tạo màu và xào thịt"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Minced Beef Stir-fry with Green Beans",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 135, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Green Beans", "qty": 180, "unit": "g", "notes": "Thái hạt lựu hoặc cắt nhỏ"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nêm nếm"},
            {"food_name_en": "Soybean Oil", "qty": 10, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Five-Spice Pork 'Gia Cay' Style",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 175, "unit": "g", "notes": "Thái miếng vuông dày"},
            {"food_name_en": "Galangal", "qty": 20, "unit": "g", "notes": "Giã nhuyễn lấy cả nước và bã"},
            {"food_name_en": "Lemongrass", "qty": 15, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Fermented Rice", "qty": 15, "unit": "g", "notes": "Lọc lấy nước chua"},
            {"food_name_en": "Shrimp Paste", "qty": 5, "unit": "g", "notes": "Dùng loại ngon, ít muối"},
            {"food_name_en": "Turmeric", "qty": 5, "unit": "g", "notes": "Nghệ tươi hoặc bột nghệ"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Cân bằng vị mặn"}
        ]
    },
    
    {
        "recipe_name_en": "Beef Dipped in Apple Cider Vinegar Broth",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 145, "unit": "g", "notes": "Thái lát thật mỏng"},
            {"food_name_en": "Coconut Water", "qty": 200, "unit": "ml", "notes": "Làm nước dùng"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 30, "unit": "ml", "notes": "Tạo độ chua và làm chín thịt"},
            {"food_name_en": "Onion", "qty": 40, "unit": "g", "notes": "Thái khoanh nhúng kèm"},
            {"food_name_en": "Lemongrass", "qty": 10, "unit": "g", "notes": "Đập dập cho nước dùng"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Khử mùi nước dùng"},
            {"food_name_en": "Lettuce", "qty": 50, "unit": "g", "notes": "Rau cuốn kèm"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Pork Loin Wrapped Ladyfingers",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 155, "unit": "g", "notes": "Lạng lát mỏng, bản to"},
            {"food_name_en": "Okra", "qty": 150, "unit": "g", "notes": "Để nguyên trái cuộn bên trong"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Quét nhẹ lớp ngoài khi nướng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Seaweed Soup with Minced Beef",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 120, "unit": "g", "notes": "Băm nhỏ, xào sơ"},
            {"food_name_en": "Dried Seaweed", "qty": 10, "unit": "g", "notes": "Ngâm nở trước khi nấu (tương đương 100g tươi)"},
            {"food_name_en": "Sesame Oil", "qty": 8, "unit": "ml", "notes": "Xào thịt bò tạo mùi thơm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nêm nước dùng"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước dùng canh"}
        ]
    },
    
    {
        "recipe_name_en": "Rainbow Vegetable Egg Rolls",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "Khoảng 2 quả lớn, đánh tan"},
            {"food_name_en": "Carrot", "qty": 20, "unit": "g", "notes": "Băm thật nhỏ"},
            {"food_name_en": "Onion", "qty": 15, "unit": "g", "notes": "Băm thật nhỏ"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Thái nhỏ"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Tráng chảo chống dính"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Tofu with Tamari Glaze",
        "ingredients": [
            {"food_name_en": "Firm Tofu", "qty": 160, "unit": "g", "notes": "Thấm khô, cắt miếng"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Thành phần sốt chính"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Áp chảo tạo độ giòn"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo độ bóng cho sốt"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Băm nhỏ tạo mùi thơm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ tạo mùi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Poached Eggs with Avocado",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "Chần trong nước có pha chút giấm"},
            {"food_name_en": "Avocado", "qty": 100, "unit": "g", "notes": "Thái lát hoặc nghiền nhẹ"},
            {"food_name_en": "Chia Seeds", "qty": 5, "unit": "g", "notes": "Rắc lên trên tạo độ giòn và thêm xơ"},
            {"food_name_en": "Paprika Powder", "qty": 2, "unit": "g", "notes": "Tạo màu sắc và vị cay nhẹ"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Soft Tofu with Shiitake Mushroom Sauce",
        "ingredients": [
            {"food_name_en": "Silken Tofu", "qty": 240, "unit": "g", "notes": "Hấp nóng"},
            {"food_name_en": "Shiitake Mushroom", "qty": 60, "unit": "g", "notes": "Nấm tươi, thái nhỏ làm sốt"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Nền nước sốt"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào nấm"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Băm nhỏ tạo mùi thơm"},
            {"food_name_en": "Tapioca Starch", "qty": 5, "unit": "g", "notes": "Pha loãng tạo độ sệt cho sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Egg with Wood Ear & Glass Noodles",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 120, "unit": "g", "notes": "Khoảng 2 quả lớn, 1 lòng đỏ để riêng tráng mặt"},
            {"food_name_en": "Wood Ear Mushroom", "qty": 15, "unit": "g", "notes": "Ngâm nở, băm nhỏ"},
            {"food_name_en": "Glass Noodles", "qty": 10, "unit": "g", "notes": "Ngâm mềm, cắt ngắn"},
            {"food_name_en": "Carrot", "qty": 20, "unit": "g", "notes": "Thái sợi nhỏ"},
            {"food_name_en": "Onion", "qty": 15, "unit": "g", "notes": "Thái sợi nhỏ"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Seaweed & Soft Tofu Soup",
        "ingredients": [
            {"food_name_en": "Silken Tofu", "qty": 250, "unit": "g", "notes": "Thái khối vuông"},
            {"food_name_en": "Dried Seaweed", "qty": 8, "unit": "g", "notes": "Ngâm nở (tương đương 80g tươi)"},
            {"food_name_en": "Sesame Oil", "qty": 5, "unit": "ml", "notes": "Thêm sau khi tắt bếp"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nêm nước dùng"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Khử mùi tanh rong biển"},
            {"food_name_en": "Purified Water", "qty": 450, "unit": "ml", "notes": "Nước nấu canh"}
        ]
    },
    
    {
        "recipe_name_en": "Boiled Egg Salad with Cashews",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "Luộc chín tới, cắt múi cau"},
            {"food_name_en": "Roasted Cashews", "qty": 20, "unit": "g", "notes": "Rắc lên trên cùng"},
            {"food_name_en": "Rau mầm (Radish Sprouts)", "qty": 80, "unit": "g", "notes": "Nền salad"},
            {"food_name_en": "Cherry Tomato", "qty": 50, "unit": "g", "notes": "Cắt đôi"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Thành phần sốt dầu giấm"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 5, "unit": "ml", "notes": "Thành phần sốt dầu giấm"}
        ]
    },
    
    {
        "recipe_name_en": "Classic Boiled Tofu with Soy Dip",
        "ingredients": [
            {"food_name_en": "Firm Tofu", "qty": 160, "unit": "g", "notes": "Cắt miếng vuông, luộc nóng"},
            {"food_name_en": "Soy Sauce", "qty": 15, "unit": "ml", "notes": "Nước chấm"},
            {"food_name_en": "Chili Pepper", "qty": 3, "unit": "g", "notes": "Thái lát cho nước chấm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Cho vào nước luộc đậu"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Egg with Bitter Melon",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "Đánh tan cùng tiêu và mắm"},
            {"food_name_en": "Bitter Melon", "qty": 150, "unit": "g", "notes": "Bỏ ruột, thái lát mỏng"},
            {"food_name_en": "Soybean Oil", "qty": 6, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Gia vị nêm trứng"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Baked Mung Bean & Veggie Patties",
        "ingredients": [
            {"food_name_en": "Peeled Mung Beans", "qty": 45, "unit": "g", "notes": "Trọng lượng hạt khô, hấp chín xay nhuyễn"},
            {"food_name_en": "Sweet Corn", "qty": 30, "unit": "g", "notes": "Hạt ngô ngọt"},
            {"food_name_en": "Carrot", "qty": 30, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Phết mặt chả trước khi nướng"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Thái nhỏ trộn nhân"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared King Oyster Mushrooms with Black Pepper Sauce",
        "ingredients": [
            {"food_name_en": "King Oyster Mushroom", "qty": 300, "unit": "g", "notes": "Thái lát dọc, khứa vảy rồng"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Thành phần sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Áp chảo nấm"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo độ sệt và cân bằng vị"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Black Pepper", "qty": 3, "unit": "g", "notes": "Tiêu đen giã dập"}
        ]
    },
    
    {
        "recipe_name_en": "Sunny-side Up with Cherry Tomatoes & Onions",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "2 quả lớn, ốp la"},
            {"food_name_en": "Cherry Tomato", "qty": 80, "unit": "g", "notes": "Bổ đôi, xào mềm"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Thái múi cau nhỏ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Dùng xào rau củ và ốp trứng"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Trang trí"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Braised Tofu in Fresh Tomato Sauce",
        "ingredients": [
            {"food_name_en": "Firm Tofu", "qty": 180, "unit": "g", "notes": "Chần sơ, không chiên"},
            {"food_name_en": "Tomato", "qty": 100, "unit": "g", "notes": "Băm nhỏ làm sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào sốt cà chua"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nêm vị"},
            {"food_name_en": "Scallion", "qty": 15, "unit": "g", "notes": "Rắc sau cùng"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Edamame Salad with Sesame Dressing",
        "ingredients": [
            {"food_name_en": "Edamame", "qty": 120, "unit": "g", "notes": "Trọng lượng hạt đã tách vỏ"},
            {"food_name_en": "Purple Cabbage", "qty": 50, "unit": "g", "notes": "Bào sợi"},
            {"food_name_en": "Carrot", "qty": 30, "unit": "g", "notes": "Bào sợi"},
            {"food_name_en": "Roasted Sesame Dressing", "qty": 15, "unit": "ml", "notes": "Sốt trộn"},
            {"food_name_en": "Black Sesame Seeds", "qty": 2, "unit": "g", "notes": "Rắc trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Scrambled Eggs with Enoki Mushrooms",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "Khoảng 2 quả lớn, đánh tan"},
            {"food_name_en": "Enoki Mushroom", "qty": 100, "unit": "g", "notes": "Cắt đoạn vừa ăn, xào trước"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào nấm và khuấy trứng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Mixed Mushroom Stew in Claypot",
        "ingredients": [
            {"food_name_en": "King Oyster Mushroom", "qty": 150, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Straw Mushrooms", "qty": 50, "unit": "g", "notes": "Làm sạch, để nguyên hoặc cắt đôi"},
            {"food_name_en": "Shiitake Mushroom", "qty": 50, "unit": "g", "notes": "Thái lát dày"},
            {"food_name_en": "Green Peppercorns", "qty": 10, "unit": "g", "notes": "Để nguyên chùm kho cùng"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 20, "unit": "ml", "notes": "Nước sốt kho chính"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo độ bóng và cân bằng vị"},
            {"food_name_en": "Leek", "qty": 10, "unit": "g", "notes": "Phi thơm đầu hành"},
            {"food_name_en": "Soybean Oil", "qty": 7, "unit": "ml", "notes": "Dùng xào nấm"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Tofu Wrapped in Seaweed",
        "ingredients": [
            {"food_name_en": "Firm Tofu", "qty": 160, "unit": "g", "notes": "Thấm thật khô, cắt khối chữ nhật"},
            {"food_name_en": "Nori Seaweed", "qty": 5, "unit": "g", "notes": "Cắt dải dài để cuộn"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Áp chảo đậu"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Rưới gia vị sau cùng"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Gừng băm tạo mùi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Eggs with Chives",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 115, "unit": "g", "notes": "Khoảng 2 quả lớn"},
            {"food_name_en": "Chives", "qty": 30, "unit": "g", "notes": "Thái nhỏ, trộn đều cùng trứng"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Gia vị nêm trứng"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Hearty Lentil and Vegetable Stew",
        "ingredients": [
            {"food_name_en": "Dried Lentils", "qty": 65, "unit": "g", "notes": "Ngâm mềm trước khi hầm"},
            {"food_name_en": "Carrot", "qty": 40, "unit": "g", "notes": "Thái hạt lựu"},
            {"food_name_en": "Potato", "qty": 40, "unit": "g", "notes": "Thái hạt lựu"},
            {"food_name_en": "Celery", "qty": 20, "unit": "g", "notes": "Thái hạt lựu"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào hành tỏi"},
            {"food_name_en": "Dried Thyme", "qty": 1, "unit": "g", "notes": "Tạo mùi thơm"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Mustard Greens Soup with Beaten Eggs",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả, đánh tan tạo vân mây"},
            {"food_name_en": "Mustard Greens", "qty": 150, "unit": "g", "notes": "Thái nhỏ"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Đập dập nấu nước dùng"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nước dùng"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"}
        ]
    },
    
    {
        "recipe_name_en": "Classic Cauliflower Rice",
        "ingredients": [
            {"food_name_en": "Cauliflower", "qty": 200, "unit": "g", "notes": "Băm nhỏ hoặc xay vụn như hạt cơm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 3, "unit": "ml", "notes": "Áp chảo sơ"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Zucchini Noodles (Zoodles) with Pesto",
        "ingredients": [
            {"food_name_en": "Zucchini", "qty": 250, "unit": "g", "notes": "Bào sợi dài bằng dụng cụ spiralizer"},
            {"food_name_en": "Cashew Basil Pesto", "qty": 25, "unit": "ml", "notes": "Sốt trộn chính"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Xào thơm cùng mì bí"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 2, "unit": "ml", "notes": "Láng chảo xào tỏi"},
            {"food_name_en": "Parmesan Cheese", "qty": 5, "unit": "g", "notes": "Rắc lên trên (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Mustard Leaf Wraps with Shrimp and Pork",
        "ingredients": [
            {"food_name_en": "Mustard Greens", "qty": 100, "unit": "g", "notes": "Chọn lá to, bỏ gân cứng"},
            {"food_name_en": "Boiled Shrimp", "qty": 50, "unit": "g", "notes": "Chẻ đôi theo chiều dọc"},
            {"food_name_en": "Pork Tenderloin", "qty": 40, "unit": "g", "notes": "Luộc chín, thái lát mỏng"},
            {"food_name_en": "Scallion", "qty": 20, "unit": "g", "notes": "Chần sơ để buộc cuốn"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nước chấm kèm"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Pha nước chấm"}
        ]
    },
    
    {
        "recipe_name_en": "Classic Broccoli Rice",
        "ingredients": [
            {"food_name_en": "Broccoli", "qty": 220, "unit": "g", "notes": "Băm nhỏ hoặc xay vụn như hạt gạo"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 3, "unit": "ml", "notes": "Áp chảo nhanh"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Enoki Mushroom 'Noodles'",
        "ingredients": [
            {"food_name_en": "Enoki Mushroom", "qty": 180, "unit": "g", "notes": "Tách sợi, chần chín tái"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Cho vào nước chần"},
            {"food_name_en": "Purified Water", "qty": 300, "unit": "ml", "notes": "Nước dùng (tùy chọn theo món ăn kèm)"}
        ]
    },
    
    {
        "recipe_name_en": "Cauliflower Crust Pizza",
        "ingredients": [
            {"food_name_en": "Cauliflower", "qty": 250, "unit": "g", "notes": "Xay nhuyễn, hấp và vắt kiệt nước"},
            {"food_name_en": "Chicken Egg", "qty": 55, "unit": "g", "notes": "1 quả vừa, làm chất kết dính đế"},
            {"food_name_en": "Mozzarella Cheese", "qty": 40, "unit": "g", "notes": "20g cho đế, 20g cho topping"},
            {"food_name_en": "Chicken Breast", "qty": 50, "unit": "g", "notes": "Topping: áp chảo hoặc luộc xé nhỏ"},
            {"food_name_en": "Tomato", "qty": 30, "unit": "g", "notes": "Làm sốt nền"},
            {"food_name_en": "Dried Italian Herbs", "qty": 2, "unit": "g", "notes": "Gia vị trộn đế bánh"},
            {"food_name_en": "Bell Pepper", "qty": 20, "unit": "g", "notes": "Topping trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Green Papaya Noodle Stir-fry",
        "ingredients": [
            {"food_name_en": "Green Papaya", "qty": 180, "unit": "g", "notes": "Bào sợi dài, vắt khô nước"},
            {"food_name_en": "Boiled Shrimp", "qty": 50, "unit": "g", "notes": "Bóc vỏ, chẻ đôi"},
            {"food_name_en": "Pork Tenderloin", "qty": 50, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Soybean Oil", "qty": 7, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị xào"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Phi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Healthy Lettuce Taco Wraps",
        "ingredients": [
            {"food_name_en": "Romaine Lettuce", "qty": 100, "unit": "g", "notes": "Sử dụng lá lớn để làm vỏ bánh"},
            {"food_name_en": "Beef Tenderloin", "qty": 80, "unit": "g", "notes": "Băm nhỏ, xào gia vị taco"},
            {"food_name_en": "Fresh Salsa", "qty": 40, "unit": "g", "notes": "Topping tươi"},
            {"food_name_en": "Avocado", "qty": 30, "unit": "g", "notes": "Thái hạt lựu hoặc nghiền"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào thịt bò"},
            {"food_name_en": "Onion", "qty": 20, "unit": "g", "notes": "Xào cùng thịt bò"}
        ]
    },
    
    {
        "recipe_name_en": "Grain-Free Cloud Bread",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 165, "unit": "g", "notes": "3 quả, tách riêng lòng đỏ và trắng"},
            {"food_name_en": "Cream Cheese", "qty": 30, "unit": "g", "notes": "Để mềm ở nhiệt độ phòng"},
            {"food_name_en": "Cream of Tartar", "qty": 1, "unit": "g", "notes": "Giúp lòng trắng bông cứng"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Green Bean 'Fries'",
        "ingredients": [
            {"food_name_en": "Green Beans", "qty": 150, "unit": "g", "notes": "Tước xơ, để thật khô"},
            {"food_name_en": "Almond Flour", "qty": 15, "unit": "g", "notes": "Lớp phủ tạo độ giòn"},
            {"food_name_en": "Parmesan Cheese", "qty": 10, "unit": "g", "notes": "Bào nhỏ trộn cùng bột hạnh nhân"},
            {"food_name_en": "Chicken Egg", "qty": 30, "unit": "g", "notes": "Chỉ sử dụng lòng trắng để nhúng"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Phun nhẹ trước khi chiên không dầu"}
        ]
    },
    
    {
        "recipe_name_en": "Eggplant Lasagna (Noodle-Free)",
        "ingredients": [
            {"food_name_en": "Eggplant", "qty": 200, "unit": "g", "notes": "Thái lát dọc, thấm khô nước"},
            {"food_name_en": "Beef Tenderloin", "qty": 80, "unit": "g", "notes": "Băm nhỏ làm sốt Bolognese"},
            {"food_name_en": "Tomato", "qty": 100, "unit": "g", "notes": "Nấu sốt cà chua"},
            {"food_name_en": "Ricotta Cheese", "qty": 40, "unit": "g", "notes": "Xen kẽ giữa các lớp"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Nướng sơ cà tím"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Nấu sốt thịt"}
        ]
    },
    
    {
        "recipe_name_en": "Rice-free Protein Sushi Rolls",
        "ingredients": [
            {"food_name_en": "Salmon", "qty": 100, "unit": "g", "notes": "Thái thanh dài làm nhân"},
            {"food_name_en": "Nori Seaweed", "qty": 5, "unit": "g", "notes": "1-2 lá lớn để cuộn"},
            {"food_name_en": "Cucumber", "qty": 40, "unit": "g", "notes": "Thái sợi dài"},
            {"food_name_en": "Avocado", "qty": 30, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Carrot", "qty": 20, "unit": "g", "notes": "Thái sợi nhỏ"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nước chấm"}
        ]
    },
    
    {
        "recipe_name_en": "Shirataki Noodles with Sesame Sauce",
        "ingredients": [
            {"food_name_en": "Shirataki Noodles", "qty": 200, "unit": "g", "notes": "Chần nước sôi, áp chảo khô"},
            {"food_name_en": "Roasted Sesame Sauce", "qty": 15, "unit": "ml", "notes": "Sốt trộn chính"},
            {"food_name_en": "Cucumber", "qty": 50, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Black Sesame Seeds", "qty": 2, "unit": "g", "notes": "Rắc trang trí"},
            {"food_name_en": "Ginger", "qty": 3, "unit": "g", "notes": "Băm nhỏ hòa vào sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Flourless Banh Xeo Style Lettuce Wraps",
        "ingredients": [
            {"food_name_en": "Boiled Shrimp", "qty": 60, "unit": "g", "notes": "Xào nhanh cùng nhân"},
            {"food_name_en": "Pork Tenderloin", "qty": 60, "unit": "g", "notes": "Thái sợi hoặc băm nhỏ"},
            {"food_name_en": "Mung Bean Sprouts", "qty": 100, "unit": "g", "notes": "Xào vừa chín tới"},
            {"food_name_en": "Mustard Greens", "qty": 80, "unit": "g", "notes": "Dùng làm vỏ cuốn"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Pha nước mắm chua ngọt"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào nhân tôm thịt"},
            {"food_name_en": "Stevia Sweetener", "qty": 5, "unit": "g", "notes": "Pha nước chấm"}
        ]
    },
    
    {
        "recipe_name_en": "Portobello Mushroom Bun Burger",
        "ingredients": [
            {"food_name_en": "Portobello Mushroom", "qty": 150, "unit": "g", "notes": "Sử dụng 2 mũ nấm lớn thay vỏ bánh"},
            {"food_name_en": "Beef Tenderloin", "qty": 100, "unit": "g", "notes": "Băm viên nướng chín"},
            {"food_name_en": "Low-fat Cheddar Cheese", "qty": 20, "unit": "g", "notes": "1 lát đặt lên nhân thịt"},
            {"food_name_en": "Tomato", "qty": 30, "unit": "g", "notes": "Thái lát"},
            {"food_name_en": "Onion", "qty": 20, "unit": "g", "notes": "Thái lát hoặc xào sơ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo nấm và thịt"}
        ]
    },
    
    {
        "recipe_name_en": "Konjac Rice (Miracle Rice)",
        "ingredients": [
            {"food_name_en": "Konjac Rice", "qty": 200, "unit": "g", "notes": "Rửa sạch, chần và rang khô trên chảo"},
            {"food_name_en": "Purified Water", "qty": 300, "unit": "ml", "notes": "Dùng để chần hạt cơm"}
        ]
    },
    
    {
        "recipe_name_en": "Crispy Kale Chips",
        "ingredients": [
            {"food_name_en": "Curly Kale", "qty": 100, "unit": "g", "notes": "Bỏ gân lá cứng, xé miếng vừa"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Áo đều lên lá cải"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Garlic Powder", "qty": 2, "unit": "g", "notes": "Tạo vị thơm cho snack"}
        ]
    },
    
    {
        "recipe_name_en": "Spaghetti Squash with Bolognese",
        "ingredients": [
            {"food_name_en": "Spaghetti Squash", "qty": 250, "unit": "g", "notes": "Nướng và cào thành sợi"},
            {"food_name_en": "Beef Tenderloin", "qty": 60, "unit": "g", "notes": "Băm nhỏ làm sốt"},
            {"food_name_en": "Tomato", "qty": 80, "unit": "g", "notes": "Làm sốt cà chua tươi"},
            {"food_name_en": "Onion", "qty": 20, "unit": "g", "notes": "Băm nhỏ xào sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Phết mặt bí và xào thịt"},
            {"food_name_en": "Dried Thyme", "qty": 1, "unit": "g", "notes": "Gia vị thảo mộc cho sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Egg White Skin Rice-less Rolls",
        "ingredients": [
            {"food_name_en": "Egg White", "qty": 150, "unit": "g", "notes": "Tráng thật mỏng trên chảo chống dính"},
            {"food_name_en": "Pork Tenderloin", "qty": 50, "unit": "g", "notes": "Băm nhỏ làm nhân"},
            {"food_name_en": "Wood Ear Mushroom", "qty": 10, "unit": "g", "notes": "Băm nhỏ trộn nhân"},
            {"food_name_en": "Shallot", "qty": 10, "unit": "g", "notes": "Hành tím phi làm topping"},
            {"food_name_en": "Soybean Oil", "qty": 4, "unit": "ml", "notes": "Láng chảo tráng trứng và xào nhân"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Pha nước chấm chua ngọt"}
        ]
    },
    
    {
        "recipe_name_en": "Savory Oatmeal with Minced Pork & Ginger",
        "ingredients": [
            {"food_name_en": "Rolled Oats", "qty": 50, "unit": "g", "notes": "Nấu nhừ như cháo"},
            {"food_name_en": "Pork Tenderloin", "qty": 60, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái sợi tạo vị ấm"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Hành lá thái nhỏ"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nếm"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Carp Congee with Straw Mushrooms",
        "ingredients": [
            {"food_name_en": "Carp", "qty": 120, "unit": "g", "notes": "Hấp chín, gỡ lấy thịt, bỏ xương"},
            {"food_name_en": "Rolled Oats", "qty": 50, "unit": "g", "notes": "Nấu nhừ làm nền cháo"},
            {"food_name_en": "Straw Mushrooms", "qty": 50, "unit": "g", "notes": "Làm sạch, cắt đôi"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Khử tanh và làm ấm"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Phi thơm xào thịt cá"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào sơ thịt cá"}
        ]
    },
    {
        "recipe_name_en": "Green Papaya Soup with Lean Pork Knuckle",
        "ingredients": [
            {"food_name_en": "Lean Pork Knuckle", "qty": 130, "unit": "g", "notes": "Chặt miếng, chần sạch, hớt mỡ khi hầm"},
            {"food_name_en": "Green Papaya", "qty": 150, "unit": "g", "notes": "Thái miếng vừa ăn"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Khử mùi và ấm bụng"},
            {"food_name_en": "Purified Water", "qty": 600, "unit": "ml", "notes": "Nước dùng hầm"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị tối giản"}
        ]
    },
    
    {
        "recipe_name_en": "Chia & Walnut Yogurt Salad",
        "ingredients": [
            {"food_name_en": "Greek Yogurt Plain", "qty": 100, "unit": "g", "notes": "Sữa chua nền"},
            {"food_name_en": "Chia Seeds", "qty": 15, "unit": "g", "notes": "Ngâm nở trước khi trộn"},
            {"food_name_en": "Walnuts", "qty": 20, "unit": "g", "notes": "Bẻ nhỏ, rắc lên trên"},
            {"food_name_en": "Strawberry", "qty": 50, "unit": "g", "notes": "Thái lát hoặc bổ đôi"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo vị ngọt thanh"}
        ]
    },
    
    {
        "recipe_name_en": "Seaweed & Beef Recovery Soup",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 110, "unit": "g", "notes": "Thái mỏng hoặc băm nhỏ"},
            {"food_name_en": "Dried Seaweed", "qty": 10, "unit": "g", "notes": "Ngâm nở, rửa sạch"},
            {"food_name_en": "Sesame Oil", "qty": 10, "unit": "ml", "notes": "Xào thơm thịt bò và tỏi"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Gia vị nêm chính"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Chicken with Goji Berries & Red Dates",
        "ingredients": [
            {"food_name_en": "Chicken Breast", "qty": 150, "unit": "g", "notes": "Để nguyên miếng hoặc cắt khối lớn"},
            {"food_name_en": "Dried Red Dates", "qty": 15, "unit": "g", "notes": "Khoảng 3-4 quả, ngâm mềm"},
            {"food_name_en": "Goji Berries", "qty": 5, "unit": "g", "notes": "Rửa sạch"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái sợi mỏng"},
            {"food_name_en": "Purified Water", "qty": 200, "unit": "ml", "notes": "Nước dùng hấp cách thủy"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Shrimp Stir-fry with Fresh Turmeric",
        "ingredients": [
            {"food_name_en": "Shrimp", "qty": 100, "unit": "g", "notes": "Giữ vỏ để thêm Canxi"},
            {"food_name_en": "Fresh Turmeric", "qty": 15, "unit": "g", "notes": "Giã nát hoặc băm nhỏ"},
            {"food_name_en": "Shallot", "qty": 10, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Dùng để phi hành nghệ"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo độ sệt và cân bằng vị"},
            {"food_name_en": "Fish Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị rim"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Eggs with Mugwort Leaves",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả trứng lớn"},
            {"food_name_en": "Mugwort Leaves", "qty": 40, "unit": "g", "notes": "Thái nhỏ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 7, "unit": "ml", "notes": "Dùng để xào hoặc đúc bánh"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Mixed Brown Rice with Lotus Seeds & Black Beans",
        "ingredients": [
            {"food_name_en": "Brown Rice", "qty": 60, "unit": "g", "notes": "Gạo khô, ngâm trước khi nấu"},
            {"food_name_en": "Black Beans", "qty": 20, "unit": "g", "notes": "Ngâm mềm"},
            {"food_name_en": "Fresh Lotus Seeds", "qty": 20, "unit": "g", "notes": "Bỏ tâm sen"},
            {"food_name_en": "Purified Water", "qty": 150, "unit": "ml", "notes": "Nước nấu cơm"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Salmon with Soy & Ginger",
        "ingredients": [
            {"food_name_en": "Salmon Fillet", "qty": 120, "unit": "g", "notes": "Khử tanh bằng rượu trắng và gừng"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Sốt hấp"},
            {"food_name_en": "Sesame Oil", "qty": 5, "unit": "ml", "notes": "Hòa vào sốt tạo mùi thơm"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái sợi mỏng"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Trình bày bên trên"}
        ]
    },
    
    {
        "recipe_name_en": "Lotus Seed & Walnut Plant-Based Milk",
        "ingredients": [
            {"food_name_en": "Fresh Lotus Seeds", "qty": 30, "unit": "g", "notes": "Bỏ tâm sen"},
            {"food_name_en": "Walnuts", "qty": 15, "unit": "g", "notes": "Ngâm mềm"},
            {"food_name_en": "Purified Water", "qty": 200, "unit": "ml", "notes": "Dùng để xay sữa"},
            {"food_name_en": "Palm Sugar", "qty": 5, "unit": "g", "notes": "Tạo vị ngọt nhẹ (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Creamy Pumpkin Soup",
        "ingredients": [
            {"food_name_en": "Pumpkin", "qty": 200, "unit": "g", "notes": "Hấp chín, xay nhuyễn"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Xào thơm nền súp"},
            {"food_name_en": "Whipping Cream", "qty": 20, "unit": "ml", "notes": "Tạo độ ngậy và hòa tan Vitamin A"},
            {"food_name_en": "Chicken Stock", "qty": 150, "unit": "ml", "notes": "Nước dùng nền"},
            {"food_name_en": "Pumpkin Seeds", "qty": 5, "unit": "g", "notes": "Rang giòn rắc lên trên"},
            {"food_name_en": "Cinnamon Powder", "qty": 1, "unit": "g", "notes": "Gia vị làm ấm"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Beef Tenderloin with Asparagus",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 140, "unit": "g", "notes": "Thịt thăn nội nạc, áp chảo chín"},
            {"food_name_en": "Asparagus", "qty": 100, "unit": "g", "notes": "Bỏ gốc già, chần sơ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Ướp bò và xào măng tây"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Áp chảo cùng bò và măng tây"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Pigeon Congee with Lotus Seeds",
        "ingredients": [
            {"food_name_en": "Pigeon Meat", "qty": 120, "unit": "g", "notes": "Băm nhỏ và xào sơ"},
            {"food_name_en": "Rolled Oats", "qty": 50, "unit": "g", "notes": "Nấu nhừ làm nền cháo"},
            {"food_name_en": "Fresh Lotus Seeds", "qty": 20, "unit": "g", "notes": "Bỏ tâm sen, nấu mềm"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái sợi khử mùi"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Phi thơm xào thịt"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào thịt bồ câu"}
        ]
    },
    
    {
        "recipe_name_en": "Spinach & Boiled Egg Salad",
        "ingredients": [
            {"food_name_en": "Spinach", "qty": 150, "unit": "g", "notes": "Lá non, rửa sạch để ráo"},
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả, luộc chín tới"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Sốt trộn salad"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 5, "unit": "ml", "notes": "Sốt trộn salad"},
            {"food_name_en": "Roasted Sesame Seeds", "qty": 3, "unit": "g", "notes": "Rắc trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Bean Sprouts with Beef",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 110, "unit": "g", "notes": "Thái mỏng, xào chín tái"},
            {"food_name_en": "Mung Bean Sprouts", "qty": 150, "unit": "g", "notes": "Xào nhanh tay lửa lớn"},
            {"food_name_en": "Soybean Oil", "qty": 7, "unit": "ml", "notes": "Dùng xào thịt và giá"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Thái sợi ướp thịt bò"},
            {"food_name_en": "Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị xào"}
        ]
    },
    
    {
        "recipe_name_en": "Katuk Soup with Minced Pork",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 80, "unit": "g", "notes": "Bằm nhỏ, xào sơ"},
            {"food_name_en": "Katuk Leaves", "qty": 120, "unit": "g", "notes": "Vò nhẹ lá trước khi nấu"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Phi thơm xào thịt"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị tối giản"}
        ]
    },
    
    {
        "recipe_name_en": "Braised Mackerel with Fresh Ginger",
        "ingredients": [
            {"food_name_en": "Mackerel", "qty": 120, "unit": "g", "notes": "Cắt lát, khử tanh bằng rượu gừng"},
            {"food_name_en": "Ginger", "qty": 20, "unit": "g", "notes": "Thái sợi dày, lót đáy nồi"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Gia vị kho chính"},
            {"food_name_en": "Shallot", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Dùng xào thơm hành gừng"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Red Bean & Lotus Seed Medley",
        "ingredients": [
            {"food_name_en": "Dried Red Beans", "qty": 40, "unit": "g", "notes": "Ngâm qua đêm, ninh mềm"},
            {"food_name_en": "Fresh Lotus Seeds", "qty": 20, "unit": "g", "notes": "Bỏ tâm sen"},
            {"food_name_en": "Palm Sugar", "qty": 8, "unit": "g", "notes": "Tạo vị ngọt thanh tối giản"},
            {"food_name_en": "Purified Water", "qty": 400, "unit": "ml", "notes": "Nước nấu chè"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Black Bean Detox Tea",
        "ingredients": [
            {"food_name_en": "Green Kernel Black Bean", "qty": 15, "unit": "g", "notes": "Rang thơm trước khi nấu"},
            {"food_name_en": "Purified Water", "qty": 1000, "unit": "ml", "notes": "Nước dùng để đun và ủ đậu"}
        ]
    },
    
    {
        "recipe_name_en": "Bird's Nest Soup with Red Dates",
        "ingredients": [
            {"food_name_en": "Bird's Nest", "qty": 15, "unit": "g", "notes": "Trọng lượng yến tươi đã ngâm nở"},
            {"food_name_en": "Dried Red Dates", "qty": 10, "unit": "g", "notes": "2-3 quả thái lát"},
            {"food_name_en": "Rock Sugar", "qty": 5, "unit": "g", "notes": "Dùng đường phèn tạo vị thanh"},
            {"food_name_en": "Ginger", "qty": 3, "unit": "g", "notes": "Thái lát khử tanh và làm ấm"},
            {"food_name_en": "Purified Water", "qty": 150, "unit": "ml", "notes": "Nước chưng trong thố"}
        ]
    },
    
    {
        "recipe_name_en": "Bitter Melon Stir-fried with Eggs",
        "ingredients": [
            {"food_name_en": "Bitter Melon", "qty": 150, "unit": "g", "notes": "Bỏ ruột, thái lát mỏng"},
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả trứng gà lớn"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào nhanh tay"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Băm nhỏ phi thơm"},
            {"food_name_en": "Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Sugar-free Orange Glazed Chicken",
        "ingredients": [
            {"food_name_en": "Chicken Breast", "qty": 140, "unit": "g", "notes": "Cắt miếng hoặc để nguyên áp chảo"},
            {"food_name_en": "Fresh Orange Juice", "qty": 80, "unit": "ml", "notes": "Nước cốt cam tươi làm sốt"},
            {"food_name_en": "Orange Zest", "qty": 2, "unit": "g", "notes": "Vỏ cam bào lấy tinh dầu"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 5, "unit": "ml", "notes": "Tạo vị đậm đà cho sốt"},
            {"food_name_en": "Garlic Powder", "qty": 2, "unit": "g", "notes": "Gia vị sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo gà"}
        ]
    },
    
    {
        "recipe_name_en": "Low-GI Mung Bean Dessert with Stevia",
        "ingredients": [
            {"food_name_en": "Whole Mung Beans", "qty": 35, "unit": "g", "notes": "Ngâm mềm, giữ nguyên vỏ"},
            {"food_name_en": "Stevia Sweetener", "qty": 2, "unit": "g", "notes": "Điều chỉnh theo vị ngọt mong muốn"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Giã dập"},
            {"food_name_en": "Purified Water", "qty": 300, "unit": "ml", "notes": "Nước nấu chè"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Salmon with Chia Seed Glaze",
        "ingredients": [
            {"food_name_en": "Salmon Fillet", "qty": 130, "unit": "g", "notes": "Áp chảo da giòn"},
            {"food_name_en": "Chia Seeds", "qty": 10, "unit": "g", "notes": "Ngâm nở trong nước chanh"},
            {"food_name_en": "Lemon Juice", "qty": 15, "unit": "ml", "notes": "Làm nền sốt hạt chia"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 7, "unit": "ml", "notes": "Áp chảo cá"},
            {"food_name_en": "Lemon Zest", "qty": 1, "unit": "g", "notes": "Rắc lên mặt cá"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Broccoli with Minced Garlic",
        "ingredients": [
            {"food_name_en": "Broccoli", "qty": 180, "unit": "g", "notes": "Hấp chín tới trong 4-5 phút"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ, phi thơm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 4, "unit": "ml", "notes": "Rưới lên sau khi hấp"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 5, "unit": "ml", "notes": "Gia vị thanh đạm"}
        ]
    },
    
    {
        "recipe_name_en": "Lentil and Bell Pepper Salad",
        "ingredients": [
            {"food_name_en": "Lentils Boiled", "qty": 120, "unit": "g", "notes": "Đậu lăng đã luộc chín, để nguội"},
            {"food_name_en": "Bell Pepper", "qty": 80, "unit": "g", "notes": "Thái hạt lựu"},
            {"food_name_en": "Red Onion", "qty": 15, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Lemon Juice", "qty": 10, "unit": "ml", "notes": "Làm nước sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Làm nước sốt"},
            {"food_name_en": "Parsley", "qty": 5, "unit": "g", "notes": "Băm nhỏ tạo mùi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Beef with Tonkin Jasmine",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 120, "unit": "g", "notes": "Thái mỏng, ướp tỏi và Tamari"},
            {"food_name_en": "Tonkin Jasmine", "qty": 150, "unit": "g", "notes": "Xào nhanh tay với lửa lớn"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Dùng xào thịt bò"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Vegetable Stock", "qty": 20, "unit": "ml", "notes": "Dùng để xào hoa không bị khô"}
        ]
    },
    
    {
        "recipe_name_en": "Chive Soup with Silken Tofu",
        "ingredients": [
            {"food_name_en": "Silken Tofu", "qty": 150, "unit": "g", "notes": "Cắt khối vuông"},
            {"food_name_en": "Chives", "qty": 50, "unit": "g", "notes": "Cắt khúc 3cm"},
            {"food_name_en": "Dried Shrimp", "qty": 5, "unit": "g", "notes": "Băm nhỏ tạo vị ngọt (tùy chọn)"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị tối giản"}
        ]
    },
    
    {
        "recipe_name_en": "Savory Oats with Minced Pork & Mushrooms",
        "ingredients": [
            {"food_name_en": "Rolled Oats", "qty": 50, "unit": "g", "notes": "Ngâm nước cho nở"},
            {"food_name_en": "Pork Tenderloin", "qty": 60, "unit": "g", "notes": "Băm nhỏ, xào sơ"},
            {"food_name_en": "Shiitake Mushroom", "qty": 30, "unit": "g", "notes": "Thái lát hoặc băm nhỏ"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào thịt nấm"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nếm"}
        ]
    },
    
    {
        "recipe_name_en": "Boiled Edamame with Sea Salt",
        "ingredients": [
            {"food_name_en": "Edamame", "qty": 100, "unit": "g", "notes": "Luộc chín với nước muối"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 2, "unit": "g", "notes": "Rắc ngoài vỏ"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước luộc"}
        ]
    },
    
    {
        "recipe_name_en": "Shrimp-wrapped Cauliflower Bites",
        "ingredients": [
            {"food_name_en": "Shrimp", "qty": 100, "unit": "g", "notes": "Bóc vỏ, giữ đuôi"},
            {"food_name_en": "Cauliflower", "qty": 150, "unit": "g", "notes": "Cắt miếng vừa để cuộn tôm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Phết mặt nướng"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Parsley", "qty": 2, "unit": "g", "notes": "Lá khô hoặc tươi băm nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Chicken Soup with River Leaf (La Giang)",
        "ingredients": [
            {"food_name_en": "Chicken Meat", "qty": 120, "unit": "g", "notes": "Chặt miếng, chần sạch"},
            {"food_name_en": "River Leaf (La Giang)", "qty": 50, "unit": "g", "notes": "Vò nhẹ trước khi nấu"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Thái lát khử mùi"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Hành tím để nguyên củ nướng sơ"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước dùng nấu canh"},
            {"food_name_en": "Salt", "qty": 2, "unit": "g", "notes": "Gia vị tối giản"}
        ]
    },
    
    {
        "recipe_name_en": "King Oyster Mushrooms Braised with Green Peppercorns",
        "ingredients": [
            {"food_name_en": "King Oyster Mushroom", "qty": 180, "unit": "g", "notes": "Thái lát hoặc cắt miếng vừa"},
            {"food_name_en": "Green Peppercorns", "qty": 15, "unit": "g", "notes": "Đập dập nhẹ"},
            {"food_name_en": "Fresh Coconut Water", "qty": 30, "unit": "ml", "notes": "Dùng để kho lấy vị ngọt"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Gia vị chính"},
            {"food_name_en": "Soybean Oil", "qty": 5, "unit": "ml", "notes": "Xào thơm hành tiêu"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Băm nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Avocado and Pumpkin Seed Salad",
        "ingredients": [
            {"food_name_en": "Avocado", "qty": 100, "unit": "g", "notes": "Thái lát hoặc cắt khối"},
            {"food_name_en": "Pumpkin Seeds", "qty": 20, "unit": "g", "notes": "Rang sơ cho giòn"},
            {"food_name_en": "Mixed Greens", "qty": 50, "unit": "g", "notes": "Rau mầm hoặc xà lách"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Sốt trộn"},
            {"food_name_en": "Lemon Juice", "qty": 10, "unit": "ml", "notes": "Sốt trộn"},
            {"food_name_en": "Feta Cheese", "qty": 10, "unit": "g", "notes": "Rắc lên trên (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Homemade Unsweetened Almond Milk",
        "ingredients": [
            {"food_name_en": "Raw Almonds", "qty": 10, "unit": "g", "notes": "Ngâm qua đêm, bóc vỏ lụa"},
            {"food_name_en": "Purified Water", "qty": 250, "unit": "ml", "notes": "Dùng để xay sữa"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 0.5, "unit": "g", "notes": "Cân bằng hương vị"},
            {"food_name_en": "Vanilla Extract", "qty": 1, "unit": "ml", "notes": "Tạo mùi thơm tự nhiên"}
        ]
    },
    {
        "recipe_name_en": "Steamed Mackerel with Basil & Cinnamon Leaves",
        "ingredients": [
            {"food_name_en": "Mackerel", "qty": 120, "unit": "g", "notes": "Khử tanh bằng gừng rượu"},
            {"food_name_en": "Basil Leaves", "qty": 20, "unit": "g", "notes": "Lót đĩa và phủ mặt cá"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Nước chấm kèm"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "White Wine", "qty": 5, "unit": "ml", "notes": "Khử mùi cá"}
        ]
    },
    
    {
        "recipe_name_en": "Winter Melon Soup with Shrimp",
        "ingredients": [
            {"food_name_en": "Winter Melon", "qty": 200, "unit": "g", "notes": "Thái miếng vừa hoặc băm nhỏ"},
            {"food_name_en": "Shrimp", "qty": 60, "unit": "g", "notes": "Lột vỏ, giã nhẹ"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Giã cùng tôm"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị thanh đạm"}
        ]
    },
    
    {
        "recipe_name_en": "Boiled Beef Shank with Mustard Dipping Sauce",
        "ingredients": [
            {"food_name_en": "Beef Shank", "qty": 140, "unit": "g", "notes": "Luộc chín, thái lát mỏng"},
            {"food_name_en": "Mustard", "qty": 10, "unit": "g", "notes": "Mù tạt vàng hoặc Wasabi"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Pha nước chấm"},
            {"food_name_en": "Lemon Juice", "qty": 5, "unit": "ml", "notes": "Pha nước chấm"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Luộc cùng bò để khử mùi"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Luộc cùng bò để tạo vị ngọt"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Eggs with Shiitake Mushrooms",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả trứng lớn, đánh tan"},
            {"food_name_en": "Dried Shiitake Mushroom", "qty": 10, "unit": "g", "notes": "Ngâm nở, băm nhỏ"},
            {"food_name_en": "Purified Water", "qty": 120, "unit": "ml", "notes": "Hòa vào trứng để tạo độ mịn"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Thái nhỏ rắc lên trên"}
        ]
    },
    
    {
        "recipe_name_en": "Green Glow Smoothie (Kale, Cucumber, Green Apple)",
        "ingredients": [
            {"food_name_en": "Curly Kale", "qty": 30, "unit": "g", "notes": "Bỏ cuống, lấy lá"},
            {"food_name_en": "Cucumber", "qty": 100, "unit": "g", "notes": "Để cả vỏ nếu sạch"},
            {"food_name_en": "Green Apple", "qty": 80, "unit": "g", "notes": "1/2 quả vừa"},
            {"food_name_en": "Purified Water", "qty": 150, "unit": "ml", "notes": "Nước nền xay"},
            {"food_name_en": "Lemon Juice", "qty": 5, "unit": "ml", "notes": "Giữ màu xanh và tăng Vitamin C"}
        ]
    },
    
    {
        "recipe_name_en": "Garlic Butter Salmon",
        "ingredients": [
            {"food_name_en": "Salmon Fillet", "qty": 120, "unit": "g", "notes": "Thấm thật khô trước khi áp chảo"},
            {"food_name_en": "Unsalted Butter", "qty": 15, "unit": "g", "notes": "Dùng để rưới lên cá"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo cá lúc đầu"},
            {"food_name_en": "Lemon Juice", "qty": 5, "unit": "ml", "notes": "Vắt vào cuối cùng"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Crispy Roasted Pork Belly",
        "ingredients": [
            {"food_name_en": "Pork Belly", "qty": 120, "unit": "g", "notes": "Chọn miếng mỡ thịt xen kẽ đều"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 5, "unit": "ml", "notes": "Phết mặt da để nổ giòn"},
            {"food_name_en": "Five-spice Powder", "qty": 2, "unit": "g", "notes": "Ướp mặt thịt"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 3, "unit": "g", "notes": "Ướp thịt và phủ mặt da"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Keto Cheesy Omelette",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả trứng lớn"},
            {"food_name_en": "Cheddar Cheese", "qty": 30, "unit": "g", "notes": "Bào sợi"},
            {"food_name_en": "Heavy Cream", "qty": 15, "unit": "ml", "notes": "Đánh cùng trứng"},
            {"food_name_en": "Unsalted Butter", "qty": 5, "unit": "g", "notes": "Dùng tráng chảo"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Steak with Hollandaise Sauce",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 130, "unit": "g", "notes": "Áp chảo vừa chín tới"},
            {"food_name_en": "Egg Yellow", "qty": 36, "unit": "g", "notes": "2 lòng đỏ làm sốt"},
            {"food_name_en": "Unsalted Butter", "qty": 25, "unit": "g", "notes": "Đun chảy làm sốt"},
            {"food_name_en": "Lemon Juice", "qty": 5, "unit": "ml", "notes": "Tạo vị chua cho sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Áp chảo bò"}
        ]
    },
    
    {
        "recipe_name_en": "Crispy Garlic Butter Chicken (No Flour)",
        "ingredients": [
            {"food_name_en": "Chicken Wing with Skin", "qty": 140, "unit": "g", "notes": "Thấm thật khô trước khi chiên"},
            {"food_name_en": "Unsalted Butter", "qty": 20, "unit": "g", "notes": "Làm sốt bơ tỏi"},
            {"food_name_en": "Garlic", "qty": 15, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 2, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Lettuce Wraps with Creamy Mayo Pork",
        "ingredients": [
            {"food_name_en": "Pork Belly", "qty": 80, "unit": "g", "notes": "Băm nhỏ, xào chín"},
            {"food_name_en": "Keto Mayonnaise", "qty": 20, "unit": "g", "notes": "Trộn sau khi thịt nguội"},
            {"food_name_en": "Butterhead Lettuce", "qty": 50, "unit": "g", "notes": "Làm vỏ cuốn"},
            {"food_name_en": "Onion", "qty": 20, "unit": "g", "notes": "Thái hạt lựu xào cùng thịt"},
            {"food_name_en": "Avocado", "qty": 30, "unit": "g", "notes": "Thái lát kẹp cùng (tùy chọn)"}
        ]
    },  
    
    {
        "recipe_name_en": "Stir-fried Cauliflower with Pork Belly",
        "ingredients": [
            {"food_name_en": "Fatty Pork Belly", "qty": 100, "unit": "g", "notes": "Thái mỏng, áp chảo ra mỡ"},
            {"food_name_en": "Cauliflower", "qty": 150, "unit": "g", "notes": "Cắt bông nhỏ"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Thái khúc"}
        ]
    },
    
    {
        "recipe_name_en": "Avocado Egg Boats",
        "ingredients": [
            {"food_name_en": "Avocado", "qty": 120, "unit": "g", "notes": "Nửa quả chín, bỏ hạt"},
            {"food_name_en": "Chicken Egg", "qty": 55, "unit": "g", "notes": "1 quả lớn"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Cung cấp khoáng chất"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Chili Powder", "qty": 0.5, "unit": "g", "notes": "Tạo vị cay nhẹ (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Braised Mackerel in Thick Coconut Cream",
        "ingredients": [
            {"food_name_en": "Mackerel", "qty": 120, "unit": "g", "notes": "Thấm thật khô, khử tanh bằng gừng"},
            {"food_name_en": "Coconut Cream Thick", "qty": 100, "unit": "ml", "notes": "Nước cốt vắt đầu tiên"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 15, "unit": "ml", "notes": "Gia vị"},
            {"food_name_en": "Shallot", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Bird's Eye Chili", "qty": 2, "unit": "g", "notes": "Tạo vị cay nồng"}
        ]
    },
    
    {
        "recipe_name_en": "Creamy Garlic Shrimp with Asparagus",
        "ingredients": [
            {"food_name_en": "Shrimp", "qty": 120, "unit": "g", "notes": "Bóc vỏ, bỏ chỉ lưng"},
            {"food_name_en": "Asparagus", "qty": 100, "unit": "g", "notes": "Cắt khúc, chần sơ"},
            {"food_name_en": "Heavy Cream", "qty": 40, "unit": "ml", "notes": "Làm sốt kem"},
            {"food_name_en": "Unsalted Butter", "qty": 10, "unit": "g", "notes": "Xào tôm tỏi"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Parmesan Cheese", "qty": 5, "unit": "g", "notes": "Rắc tạo độ sệt và vị Umami"}
        ]
    },
    
    {
        "recipe_name_en": "Pan-seared Mushroom & Walnut Salad",
        "ingredients": [
            {"food_name_en": "King Oyster Mushroom", "qty": 100, "unit": "g", "notes": "Thái lát, áp chảo"},
            {"food_name_en": "Walnuts", "qty": 25, "unit": "g", "notes": "Bẻ nhỏ, rang sơ"},
            {"food_name_en": "Unsalted Butter", "qty": 5, "unit": "g", "notes": "Áp chảo nấm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Sốt trộn salad"},
            {"food_name_en": "Mixed Greens", "qty": 50, "unit": "g", "notes": "Rau mầm hoặc xà lách"},
            {"food_name_en": "Apple Cider Vinegar", "qty": 5, "unit": "ml", "notes": "Sốt trộn salad"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Bitter Melon stuffed with Fatty Pork",
        "ingredients": [
            {"food_name_en": "Bitter Melon", "qty": 150, "unit": "g", "notes": "Cắt khúc, bỏ ruột"},
            {"food_name_en": "Fatty Pork Shoulder", "qty": 100, "unit": "g", "notes": "Băm nhỏ làm nhân"},
            {"food_name_en": "Wood Ear Mushroom", "qty": 10, "unit": "g", "notes": "Băm nhỏ trộn nhân"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Dùng làm nước chấm kèm"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị trộn nhân"}
        ]
    },
    
    {
        "recipe_name_en": "Pork Tenderloin Cheese Rolls",
        "ingredients": [
            {"food_name_en": "Pork Tenderloin", "qty": 120, "unit": "g", "notes": "Thái lát mỏng, dần mềm"},
            {"food_name_en": "Cheddar Cheese", "qty": 30, "unit": "g", "notes": "Cắt thanh hoặc lát"},
            {"food_name_en": "Unsalted Butter", "qty": 10, "unit": "g", "notes": "Pha với tỏi để phết mặt thịt"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Cauliflower Fried Rice with Lard & Eggs",
        "ingredients": [
            {"food_name_en": "Cauliflower", "qty": 200, "unit": "g", "notes": "Băm nhỏ hoặc xay vụn như hạt gạo"},
            {"food_name_en": "Lard", "qty": 20, "unit": "g", "notes": "Mỡ lợn thắng lấy cả tóp mỡ"},
            {"food_name_en": "Chicken Egg", "qty": 55, "unit": "g", "notes": "1 quả lớn"},
            {"food_name_en": "Scallion", "qty": 10, "unit": "g", "notes": "Thái nhỏ"},
            {"food_name_en": "Black Pepper", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Skin-on Chicken Breast Roast",
        "ingredients": [
            {"food_name_en": "Chicken Breast with Skin", "qty": 150, "unit": "g", "notes": "Giữ nguyên da để khóa ẩm"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Ướp mặt da"},
            {"food_name_en": "Rosemary", "qty": 2, "unit": "g", "notes": "Lá tươi hoặc khô"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 2, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Grilled Eggplant with Scallion Oil & Peanuts",
        "ingredients": [
            {"food_name_en": "Eggplant", "qty": 200, "unit": "g", "notes": "Nướng nguyên quả, tước sợi"},
            {"food_name_en": "Lard", "qty": 15, "unit": "g", "notes": "Mỡ lợn thắng để làm mỡ hành"},
            {"food_name_en": "Roasted Peanuts", "qty": 15, "unit": "g", "notes": "Giã dập, rắc lên trên"},
            {"food_name_en": "Scallion", "qty": 20, "unit": "g", "notes": "Làm mỡ hành"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Dùng rưới kèm (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Tuna Mayo Salad with Onions",
        "ingredients": [
            {"food_name_en": "Canned Tuna in Oil", "qty": 100, "unit": "g", "notes": "Chắt ráo dầu trước khi trộn"},
            {"food_name_en": "Keto Mayonnaise", "qty": 25, "unit": "g", "notes": "Loại không đường"},
            {"food_name_en": "Red Onion", "qty": 20, "unit": "g", "notes": "Thái hạt lựu nhỏ"},
            {"food_name_en": "Butterhead Lettuce", "qty": 50, "unit": "g", "notes": "Dùng làm nền salad"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Spicy Salt Grilled Pork Ribs (Sugar-free)",
        "ingredients": [
            {"food_name_en": "Pork Spareribs", "qty": 150, "unit": "g", "notes": "Chặt miếng, thấm khô"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Trộn vào sốt ướp để khóa ẩm"},
            {"food_name_en": "Chili", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 2, "unit": "g", "notes": "Gia vị chính"},
            {"food_name_en": "Lemon", "qty": 10, "unit": "g", "notes": "Vắt lấy cốt sau khi nướng"}
        ]
    },
    
    {
        "recipe_name_en": "Butter-Glazed Beef Wrapped Asparagus",
        "ingredients": [
            {"food_name_en": "Beef Tenderloin", "qty": 120, "unit": "g", "notes": "Thái lát mỏng, to bản"},
            {"food_name_en": "Asparagus", "qty": 80, "unit": "g", "notes": "Cắt bỏ gốc già"},
            {"food_name_en": "Unsalted Butter", "qty": 20, "unit": "g", "notes": "Đun chảy với tỏi và lá thơm"},
            {"food_name_en": "Garlic", "qty": 5, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Thyme", "qty": 2, "unit": "g", "notes": "Lá tươi tạo mùi thơm"}
        ]
    },
    
    {
        "recipe_name_en": "Bulletproof Coffee (Keto Coffee)",
        "ingredients": [
            {"food_name_en": "Black Coffee", "qty": 250, "unit": "ml", "notes": "Pha nóng nguyên chất"},
            {"food_name_en": "Unsalted Butter", "qty": 15, "unit": "g", "notes": "Ưu tiên bơ từ bò ăn cỏ"},
            {"food_name_en": "MCT Oil", "qty": 15, "unit": "ml", "notes": "Hoặc dầu dừa nguyên chất"}
        ]
    },
    
    {
        "recipe_name_en": "Rainbow Phytonutrient Salad",
        "ingredients": [
            {"food_name_en": "Purple Cabbage", "qty": 50, "unit": "g", "notes": "Thái sợi mỏng"},
            {"food_name_en": "Bell Pepper", "qty": 50, "unit": "g", "notes": "Cắt thanh dài"},
            {"food_name_en": "Carrot", "qty": 40, "unit": "g", "notes": "Bào sợi"},
            {"food_name_en": "Sweet Corn", "qty": 30, "unit": "g", "notes": "Luộc chín"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 15, "unit": "ml", "notes": "Làm nước sốt"},
            {"food_name_en": "Lemon Juice", "qty": 10, "unit": "ml", "notes": "Làm nước sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Detox Beetroot & Ginger Soup",
        "ingredients": [
            {"food_name_en": "Beetroot", "qty": 120, "unit": "g", "notes": "Cắt khối vuông"},
            {"food_name_en": "Potato", "qty": 50, "unit": "g", "notes": "Tạo độ sánh cho súp"},
            {"food_name_en": "Ginger", "qty": 10, "unit": "g", "notes": "Băm nhuyễn"},
            {"food_name_en": "Almond Milk", "qty": 30, "unit": "ml", "notes": "Thêm vào cuối để tạo độ béo"},
            {"food_name_en": "Vegetable Stock", "qty": 300, "unit": "ml", "notes": "Nước dùng súp"}
        ]
    },
    
    {
        "recipe_name_en": "Classic Detox Infused Water",
        "ingredients": [
            {"food_name_en": "Lemon", "qty": 40, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Cucumber", "qty": 100, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Mint Leaves", "qty": 5, "unit": "g", "notes": "Vò nhẹ"},
            {"food_name_en": "Purified Water", "qty": 1500, "unit": "ml", "notes": "Nước lọc sạch"}
        ]
    },
    
    {
        "recipe_name_en": "Glowing Green Smoothie (GGS)",
        "ingredients": [
            {"food_name_en": "Spinach", "qty": 50, "unit": "g", "notes": "Rửa sạch, bỏ cuống già"},
            {"food_name_en": "Cucumber", "qty": 100, "unit": "g", "notes": "Cắt miếng nhỏ"},
            {"food_name_en": "Green Apple", "qty": 80, "unit": "g", "notes": "Giữ cả vỏ để lấy pectin"},
            {"food_name_en": "Lemon Juice", "qty": 10, "unit": "ml", "notes": "Tăng vị chua và bảo quản vitamin"},
            {"food_name_en": "Purified Water", "qty": 200, "unit": "ml", "notes": "Nước nền để xay"}
        ]
    },
    
    {
        "recipe_name_en": "Seaweed Soup with Silken Tofu",
        "ingredients": [
            {"food_name_en": "Dried Seaweed", "qty": 10, "unit": "g", "notes": "Ngâm nở, rửa sạch"},
            {"food_name_en": "Silken Tofu", "qty": 100, "unit": "g", "notes": "Cắt khối vuông"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Thái sợi"},
            {"food_name_en": "Vegetable Stock", "qty": 500, "unit": "ml", "notes": "Nước dùng thanh đạm"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 10, "unit": "ml", "notes": "Gia vị sạch"}
        ]
    },
    
    {
        "recipe_name_en": "Steamed Broccoli with Passion Fruit Glaze",
        "ingredients": [
            {"food_name_en": "Broccoli", "qty": 150, "unit": "g", "notes": "Hấp chín tới 5 phút"},
            {"food_name_en": "Passion Fruit", "qty": 60, "unit": "g", "notes": "Lấy nước cốt (khoảng 2 quả)"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Hòa vào sốt"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo vị ngọt nhẹ cân bằng"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Flaxseed & Avocado Gut-Cleanse Salad",
        "ingredients": [
            {"food_name_en": "Avocado", "qty": 100, "unit": "g", "notes": "Thái khối vuông"},
            {"food_name_en": "Flaxseed", "qty": 15, "unit": "g", "notes": "Xay vỡ trước khi trộn"},
            {"food_name_en": "Spinach", "qty": 50, "unit": "g", "notes": "Rau nền"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Nước sốt"},
            {"food_name_en": "Lemon Juice", "qty": 10, "unit": "ml", "notes": "Nước sốt"}
        ]
    },
    
    {
        "recipe_name_en": "Anti-Inflammatory Carrot & Turmeric Soup",
        "ingredients": [
            {"food_name_en": "Carrot", "qty": 150, "unit": "g", "notes": "Thái khoanh, hầm mềm"},
            {"food_name_en": "Fresh Turmeric", "qty": 5, "unit": "g", "notes": "Giã nhuyễn hoặc băm nhỏ"},
            {"food_name_en": "Onion", "qty": 30, "unit": "g", "notes": "Xào thơm nền súp"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào hành và nghệ"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Bắt buộc để hấp thụ Curcumin"},
            {"food_name_en": "Vegetable Stock", "qty": 300, "unit": "ml", "notes": "Nước dùng súp"}
        ]
    },
    
    {
        "recipe_name_en": "Pure Celery Juice",
        "ingredients": [
            {"food_name_en": "Celery", "qty": 350, "unit": "g", "notes": "Chỉ lấy phần bẹ và lá xanh tươi"}
        ]
    },
    
    {
        "recipe_name_en": "Beauty Collagen Dessert Soup (Peach Gum & Red Dates)",
        "ingredients": [
            {"food_name_en": "Peach Gum", "qty": 10, "unit": "g", "notes": "Trọng lượng khô, ngâm 15 tiếng"},
            {"food_name_en": "Pith of Sterculia", "qty": 5, "unit": "g", "notes": "Tuyết yến khô, ngâm nở"},
            {"food_name_en": "Red Dates", "qty": 20, "unit": "g", "notes": "Táo đỏ cắt lát"},
            {"food_name_en": "Goji Berries", "qty": 5, "unit": "g", "notes": "Kỷ tử"},
            {"food_name_en": "Purified Water", "qty": 400, "unit": "ml", "notes": "Nước nấu chè"},
            {"food_name_en": "Stevia", "qty": 1, "unit": "g", "notes": "Tạo ngọt không calo"}
        ]
    },
    
    {
        "recipe_name_en": "Sprouted Bean & Brown Rice Paper Rolls",
        "ingredients": [
            {"food_name_en": "Brown Rice Paper", "qty": 30, "unit": "g", "notes": "Khoảng 3-4 cái"},
            {"food_name_en": "Brown Rice Vermicelli", "qty": 30, "unit": "g", "notes": "Luộc chín"},
            {"food_name_en": "Tofu", "qty": 50, "unit": "g", "notes": "Áp chảo không dầu, thái sợi"},
            {"food_name_en": "Sprouted Beans", "qty": 50, "unit": "g", "notes": "Rau mầm tươi"},
            {"food_name_en": "Mixed Herbs", "qty": 20, "unit": "g", "notes": "Xà lách, húng quế"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Zucchini with Garlic & Sesame Seeds",
        "ingredients": [
            {"food_name_en": "Zucchini", "qty": 200, "unit": "g", "notes": "Thái lát hoặc sợi"},
            {"food_name_en": "Sesame Seeds", "qty": 5, "unit": "g", "notes": "Hạt mè rang vàng"},
            {"food_name_en": "Sesame Oil", "qty": 3, "unit": "ml", "notes": "Thêm vào sau khi tắt bếp"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ phi thơm"},
            {"food_name_en": "Tamari Soy Sauce", "qty": 5, "unit": "ml", "notes": "Nêm nhẹ"}
        ]
    },
    
    {
        "recipe_name_en": "Bitter Melon & Mushroom Clear Soup",
        "ingredients": [
            {"food_name_en": "Bitter Melon", "qty": 150, "unit": "g", "notes": "Thái lát mỏng"},
            {"food_name_en": "Straw Mushroom", "qty": 80, "unit": "g", "notes": "Rửa sạch, cắt đôi"},
            {"food_name_en": "Vegetable Stock", "qty": 500, "unit": "ml", "notes": "Nước dùng rau củ thanh đạm"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị nhẹ"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Thái nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Overnight Oats with Mixed Berries",
        "ingredients": [
            {"food_name_en": "Rolled Oats", "qty": 40, "unit": "g", "notes": "Yến mạch cán dẹt"},
            {"food_name_en": "Almond Milk", "qty": 150, "unit": "ml", "notes": "Loại không đường"},
            {"food_name_en": "Chia Seeds", "qty": 10, "unit": "g", "notes": "Tạo độ kết dính"},
            {"food_name_en": "Blueberries", "qty": 50, "unit": "g", "notes": "Hoặc dâu tây cắt lát"},
            {"food_name_en": "Sliced Almonds", "qty": 5, "unit": "g", "notes": "Rắc lên trên"}
        ]
    },
    
    {
        "recipe_name_en": "Garlic Cauliflower Mash",
        "ingredients": [
            {"food_name_en": "Cauliflower", "qty": 250, "unit": "g", "notes": "Hấp chín mềm"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Hấp cùng súp lơ"},
            {"food_name_en": "Unsalted Butter", "qty": 10, "unit": "g", "notes": "Tạo độ mịn và béo"},
            {"food_name_en": "Almond Milk", "qty": 30, "unit": "ml", "notes": "Điều chỉnh độ đặc"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Black Bean Tea",
        "ingredients": [
            {"food_name_en": "Green Kernel Black Beans", "qty": 20, "unit": "g", "notes": "Rang thơm trước khi nấu"},
            {"food_name_en": "Purified Water", "qty": 1000, "unit": "ml", "notes": "Nước nấu trà"},
            {"food_name_en": "Ginger", "qty": 5, "unit": "g", "notes": "Thêm vào khi ủ để ấm bụng (tùy chọn)"}
        ]
    },
    
    {
        "recipe_name_en": "Cherry Tomato Salad with Apple Cider Vinaigrette",
        "ingredients": [
            {"food_name_en": "Cherry Tomato", "qty": 200, "unit": "g", "notes": "Bổ đôi"},
            {"food_name_en": "Organic Apple Cider Vinegar", "qty": 15, "unit": "ml", "notes": "Sốt trộn"},
            {"food_name_en": "Honey", "qty": 5, "unit": "g", "notes": "Tạo vị ngọt thanh"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Giúp hấp thụ Lycopene"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Garlic Roasted Asparagus",
        "ingredients": [
            {"food_name_en": "Asparagus", "qty": 180, "unit": "g", "notes": "Bỏ gốc già"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 10, "unit": "ml", "notes": "Ướp nướng"},
            {"food_name_en": "Garlic", "qty": 10, "unit": "g", "notes": "Băm nhỏ"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Black Pepper", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
    
    {
        "recipe_name_en": "Fruit Infused Kombucha",
        "ingredients": [
            {"food_name_en": "Kombucha Tea", "qty": 250, "unit": "ml", "notes": "Nước cốt F1"},
            {"food_name_en": "Mixed Berries/Mango", "qty": 50, "unit": "g", "notes": "Trái cây tươi cắt nhỏ"},
            {"food_name_en": "Purified Water", "qty": 50, "unit": "ml", "notes": "Dùng nếu muốn pha loãng"}
        ]
    },
    
    {
        "recipe_name_en": "Luffa Soup with Crushed Peanuts",
        "ingredients": [
            {"food_name_en": "Luffa", "qty": 200, "unit": "g", "notes": "Gọt vỏ, thái miếng"},
            {"food_name_en": "Peanuts", "qty": 25, "unit": "g", "notes": "Ngâm mềm, giã dập"},
            {"food_name_en": "Purified Water", "qty": 500, "unit": "ml", "notes": "Nước nấu canh"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Thái nhỏ"}
        ]
    },
    
    {
        "recipe_name_en": "Mugwort Omelet",
        "ingredients": [
            {"food_name_en": "Chicken Egg", "qty": 110, "unit": "g", "notes": "2 quả lớn"},
            {"food_name_en": "Mugwort", "qty": 30, "unit": "g", "notes": "Lấy lá và ngọn non"},
            {"food_name_en": "Fish Sauce", "qty": 5, "unit": "ml", "notes": "Nước mắm truyền thống"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Dùng tráng chảo chiên"}
        ]
    },
    
    {
        "recipe_name_en": "Tofu in Tomato Sauce",
        "ingredients": [
            {"food_name_en": "Tofu", "qty": 150, "unit": "g", "notes": "Cắt khối vuông"},
            {"food_name_en": "Tomato", "qty": 100, "unit": "g", "notes": "Băm nhỏ làm sốt"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 5, "unit": "ml", "notes": "Xào cà chua"},
            {"food_name_en": "Shallot", "qty": 5, "unit": "g", "notes": "Phi thơm"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"},
            {"food_name_en": "Scallion", "qty": 5, "unit": "g", "notes": "Trang trí"}
        ]
    },
    
    {
        "recipe_name_en": "Roasted Salty Peanuts",
        "ingredients": [
            {"food_name_en": "Peanuts Raw", "qty": 40, "unit": "g", "notes": "Hạt đều, không mốc"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 3, "unit": "ml", "notes": "Tạo độ bóng và dính muối"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 2, "unit": "g", "notes": "Rắc khi lạc còn nóng"}
        ]
    },
    
    {
        "recipe_name_en": "Stir-fried Morning Glory with Garlic",
        "ingredients": [
            {"food_name_en": "Morning Glory", "qty": 200, "unit": "g", "notes": "Nhặt sạch, để ráo"},
            {"food_name_en": "Garlic", "qty": 15, "unit": "g", "notes": "Băm nhỏ, phi vàng"},
            {"food_name_en": "Extra Virgin Olive Oil", "qty": 8, "unit": "ml", "notes": "Xào lửa lớn"},
            {"food_name_en": "Pink Himalayan Salt", "qty": 1, "unit": "g", "notes": "Gia vị"}
        ]
    },
        
]

# ==========================================
# HELPER: TÍNH TOÁN DINH DƯỠNG
# ==========================================
def update_recipe_nutrition(recipe_id):
    """Tính tổng dinh dưỡng từ các thành phần và update bảng Recipe"""
    ingredients = db.query(RecipeIngredient, Food).join(
        Food, RecipeIngredient.food_id == Food.food_id
    ).filter(RecipeIngredient.recipe_id == recipe_id).all()

    total_cal = Decimal('0')
    total_pro = Decimal('0')
    total_carb = Decimal('0')
    total_fat = Decimal('0')
    total_fib = Decimal('0')

    for ri, food in ingredients:
        ratio = Decimal(str(ri.quantity)) / Decimal('100')
        total_cal += Decimal(str(food.calories_per_100g or 0)) * ratio
        total_pro += Decimal(str(food.protein_per_100g or 0)) * ratio
        total_carb += Decimal(str(food.carbs_per_100g or 0)) * ratio
        total_fat += Decimal(str(food.fat_per_100g or 0)) * ratio
        total_fib += Decimal(str(food.fiber_per_100g or 0)) * ratio

    recipe = db.query(Recipe).get(recipe_id)
    recipe.calories_per_serving = total_cal
    recipe.protein_per_serving = total_pro
    recipe.carbs_per_serving = total_carb
    recipe.fat_per_serving = total_fat
    recipe.fiber_per_serving = total_fib
    db.commit()

# ==========================================
# MAIN SEED FUNCTION
# ==========================================
def seed_recipe_ingredients():
    print("🚀 BẮT ĐẦU ĐỒNG BỘ RECIPE INGREDIENTS & NUTRITION")
    print("-" * 70)

    for data in RECIPE_INGREDIENTS_DATA:
        recipe = db.query(Recipe).filter(Recipe.name_en == data["recipe_name_en"]).first()
        if not recipe: continue

        for idx, ing in enumerate(data["ingredients"], start=1):
            food = db.query(Food).filter(Food.name_en == ing["food_name_en"]).first()
            if not food: continue

            # Check exist
            exists = db.query(RecipeIngredient).filter(
                and_(RecipeIngredient.recipe_id == recipe.recipe_id, 
                     RecipeIngredient.food_id == food.food_id)
            ).first()

            if not exists:
                new_ri = RecipeIngredient(
                    recipe_id=recipe.recipe_id,
                    food_id=food.food_id,
                    ingredient_name=food.name_vi, # Tự lấy tên Việt từ bảng Food
                    quantity=Decimal(str(ing["qty"])),
                    unit=ing["unit"],
                    order_index=idx
                )
                db.add(new_ri)
        
        db.commit() # Lưu toàn bộ ingredient trước khi tính toán
        update_recipe_nutrition(recipe.recipe_id)
        print(f"✅ Đã đồng bộ dinh dưỡng cho món: {recipe.name_vi}")

if __name__ == "__main__":
    seed_recipe_ingredients()
    db.close()