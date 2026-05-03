"""
Meal Planning AI Service

AI-powered meal plan generation using Gemini.
Features:
- Analyzes user's nutrition goals
- Selects appropriate foods from database
- Balances macros across meals
- Diversifies diet to avoid repetition
- Respects dietary preferences and health profile
- CAN CREATE CUSTOM DISHES not in database when needed
"""

import logging
from typing import Dict, List, Optional, Any
import json
import re
import os

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini client
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


# ==========================================
# CONSTANTS FOR HEALTH PROFILE
# ==========================================

# Allergen synonyms mapping (Vietnamese -> English keywords)
ALLERGEN_SYNONYMS = {
    "hải sản": ["seafood", "shrimp", "crab", "fish", "tôm", "cua", "cá", "mực", "ngao", "sò", "hàu"],
    "tôm": ["shrimp", "prawn", "tôm", "tôm rang", "tôm hấp", "tôm chiên"],
    "cua": ["crab", "cua", "cua biển"],
    "cá": ["fish", "cá", "cá kho", "cá chiên", "cá lóc", "cá thu", "cá hồi"],
    "đậu phộng": ["peanut", "đậu phộng", "lạc", "peanuts"],
    "đậu nành": ["soy", "đậu nành", "sữa đậu nành", "tofu"],
    "gluten": ["gluten", "wheat", "bột mì", "mì", "bánh mì", "bread"],
    "sữa": ["milk", "sữa", "cheese", "phô mai", "yogurt", "dairy"],
    "trứng": ["egg", "trứng", "trứng gà", "trứng vịt"],
    "đậu": ["bean", "đậu", "đậu xanh", "đậu đen", "đậu đỏ"],
    "ngô": ["corn", "ngô", "bắp"],
    "thịt bò": ["beef", "bò", "steak", "thịt bò", "bò bít tết"],
    "thịt gà": ["chicken", "gà", "thịt gà", "chicken breast"],
    "thịt heo": ["pork", "heo", "thịt heo", "thịt lợn"],
}

# Health condition to dietary tags mapping
HEALTH_CONDITION_TAGS = {
    "tiểu đường": ["low_sugar", "low_carb", "high_fiber"],
    "tiểu đường type 1": ["low_sugar", "low_carb", "high_fiber"],
    "tiểu đường type 2": ["low_sugar", "low_carb", "high_fiber"],
    "huyết áp cao": ["low_sodium", "heart_healthy"],
    "huyết áp thấp": ["normal_sodium", "heart_healthy"],
    "bệnh tim mạch": ["heart_healthy", "low_fat"],
    "cholesterol cao": ["low_cholesterol", "low_fat"],
    "gan nhiễm mỡ": ["low_fat", "detox"],
    "viêm khớp": ["anti_inflammatory"],
    "loãng xương": ["high_calcium", "high_protein"],
}

# Dietary preference restrictions (what to AVOID)
DIETARY_RESTRICTIONS = {
    "low carb": {
        "avoid": ["rice", "com", "bún", "bánh", "mì", "phở", "bánh mì", "xôi", "noodle", "bread", "sticky rice"],
        "prefer": ["vegetable", "meat", "fish", "egg", "salad"]
    },
    "keto": {
        "avoid": ["rice", "com", "bún", "bánh", "mì", "phở", "bánh mì", "xôi", "noodle", "bread", "sugar", "đường"],
        "prefer": ["vegetable", "meat", "fish", "egg", "fat", "avocado", "butter"]
    },
    "eat clean": {
        "avoid": ["fried", "chiên", "rán", "processed", "đồ chế biến"],
        "prefer": ["healthy", "vegetable", "fruit", "grilled", "steamed"]
    },
    "vegetarian": {
        "avoid": ["chicken", "beef", "pork", "fish", "seafood", "thịt", "bò", "heo", "gà", "cá", "hải sản", "meat", "thịt"],
        "prefer": ["vegetable", "tofu", "bean", "fruit", "vegetarian"]
    },
    "vegan": {
        "avoid": ["chicken", "beef", "pork", "fish", "seafood", "egg", "milk", "dairy", "cheese", "honey", "thịt", "bò", "heo", "gà", "cá", "trứng", "sữa"],
        "prefer": ["vegetable", "fruit", "tofu", "bean", "vegan"]
    },
    "mediterranean": {
        "avoid": [],
        "prefer": ["olive oil", "fish", "vegetable", "whole grain", "seafood"]
    },
    "dash": {
        "avoid": ["salted", "mắm", "muối", "đồ chế biến"],
        "prefer": ["vegetable", "fruit", "low_sodium", "heart_healthy"]
    },
    "low fat": {
        "avoid": ["fried", "chiên", "rán", "fat", "mỡ"],
        "prefer": ["grilled", "steamed", "boiled", "vegetable"]
    },
    "low sodium": {
        "avoid": ["salted", "mắm", "muối", "đồ chế biến", "processed"],
        "prefer": ["fresh", "vegetable", "fruit", "homemade"]
    },
    "high protein": {
        "avoid": [],
        "prefer": ["chicken", "beef", "fish", "egg", "tofu", "high_protein"]
    },
    "high fiber": {
        "avoid": [],
        "prefer": ["vegetable", "fruit", "whole grain", "bean", "high_fiber"]
    },
    "gluten free": {
        "avoid": ["wheat", "gluten", "bột mì", "bánh mì", "mì", "bread", "flour", "mì"],
        "prefer": ["rice", "vegetable", "fruit", "tuber", "gluten_free"]
    },
    "sugar free": {
        "avoid": ["sugar", "đường", "dessert", "bánh", "kẹo", "nước ngọt"],
        "prefer": ["vegetable", "protein", "unsweetened"]
    },
}


class MealPlanningAIService:
    """
    AI Service to generate intelligent meal plans using Gemini.

    Features:
    - Analyzes user's nutrition goals
    - Selects appropriate foods from database
    - Balances macros across meals
    - Diversifies diet to avoid repetition
    - Respects dietary preferences
    - Respects health profile (allergies, conditions)
    - CAN CREATE CUSTOM DISHES not in database when needed
    """

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL
        self.temperature = 0.8  # Higher for creative/varied meal suggestions
        self.min_custom_dishes_percent = 0.4  # At least 40% of meals should be custom dishes
        logger.info("✅ MealPlanningAIService initialized with Gemini")
    
    async def generate_meal_plan(
        self,
        daily_calorie_target: int,
        days: int,
        goal_type: str = "maintain",
        preferences: Optional[Dict] = None,
        available_foods: Optional[List[Dict]] = None,
        health_profile: Optional[Dict] = None,
        language: str = "vi"
    ) -> Dict:
        """
        Generate meal plan using AI.
        
        Args:
            daily_calorie_target: Target calories per day
            days: Number of days in plan
            goal_type: Goal type (weight_loss, weight_gain, maintain)
            preferences: User preferences (tags, categories, etc.)
            available_foods: List of available foods from database
            health_profile: User health profile (allergies, conditions, preferences)
            language: Response language (vi/en)
        
        Returns:
            Dict containing meal plan with days and meals
        """
        
        # Define calorie distribution based on goal type
        if goal_type == "weight_loss":
            meal_distribution = {
                "breakfast": 0.30,
                "lunch": 0.35,
                "dinner": 0.25,
                "snack": 0.10
            }
        elif goal_type == "weight_gain":
            meal_distribution = {
                "breakfast": 0.25,
                "lunch": 0.30,
                "dinner": 0.35,
                "snack": 0.10
            }
        else:  # maintain or default
            meal_distribution = {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10
            }
        
        # Calculate calorie targets for each meal
        meal_calorie_targets = {
            meal: int(daily_calorie_target * ratio)
            for meal, ratio in meal_distribution.items()
        }

        # Calculate minimum custom dishes needed for variety
        min_custom_count = int(days * 3 * self.min_custom_dishes_percent)  # 40% of main meals

        # Build prompt for Gemini with health profile and custom dish creation
        prompt = self._build_meal_plan_prompt(
            calorie_targets=meal_calorie_targets,
            days=days,
            goal_type=goal_type,
            preferences=preferences,
            available_foods=available_foods,
            health_profile=health_profile,
            language=language
        )

        try:
            # Call Gemini using new SDK
            response = client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192,
                    top_p=0.95,
                    top_k=40
                )
            )
            
            # Parse response with variety enforcement
            meal_plan = self._parse_gemini_response(response.text, min_custom_count=min_custom_count)

            logger.info(f"✅ AI generated meal plan: {len(meal_plan.get('days', []))} days")

            # Count custom dishes
            custom_count = sum(
                1 for day in meal_plan.get('days', [])
                for meal in day.get('meals', [])
                if meal.get('is_custom', False)
            )
            if custom_count > 0:
                logger.info(f"   📝 {custom_count} custom dishes created by AI")

            return meal_plan

        except Exception as e:
            logger.error(f"❌ Error calling AI: {str(e)}")
            raise ValueError(f"Failed to generate meal plan: {str(e)}")
    
    def _build_meal_plan_prompt(
        self,
        calorie_targets: Dict[str, int],
        days: int,
        goal_type: str,
        preferences: Optional[Dict],
        available_foods: Optional[List[Dict]],
        health_profile: Optional[Dict],
        language: str
    ) -> str:
        """Build detailed prompt for Gemini with health profile and custom dish support"""
        
        # Convert foods to text format
        if available_foods and len(available_foods) > 0:
            foods_text = "\n".join([
                f"- {f.get('name_vi', f.get('name', 'Unknown'))}: "
                f"{f.get('calories', 0)} kcal, "
                f"P: {f.get('protein', f.get('protein_g', 0))}g, "
                f"C: {f.get('carbs', f.get('carbs_g', 0))}g, "
                f"F: {f.get('fat', f.get('fat_g', 0))}g"
                for f in available_foods[:40]  # Limit to 40 foods for prompt size
            ])
        else:
            foods_text = """
- (Không có món ăn trong database - hãy tạo món mới phù hợp)
"""
        
        # Build health profile constraints
        health_constraints = self._build_health_constraints(health_profile)
        
        # Build goal-specific guidance
        goal_guidance = self._build_goal_guidance(goal_type)
        
        meal_labels = {
            "vi": {
                "breakfast": "bữa sáng",
                "lunch": "bữa trưa",
                "dinner": "bữa tối",
                "snack": "bữa phụ"
            },
            "en": {
                "breakfast": "breakfast",
                "lunch": "lunch",
                "dinner": "dinner",
                "snack": "snack"
            }
        }
        
        labels = meal_labels.get(language, meal_labels["vi"])
        
        lang_instruction = "Trả lời bằng tiếng Việt" if language == "vi" else "Respond in English"
        
        # Min protein per main meal based on goal
        min_protein = "25" if goal_type == "weight_gain" else "15"
        
        # Food categories for variety reference
        food_categories = {
            "breakfast": ["cháo", "bánh mì", "xôi", "phở", "bún", "mì", "trứng", "yến mạch", "sinh tố", "nước ép", "sữa", "bánh flan", "bánh bao", "bánh giò", "cơm", "bánh gai", "gỏi", "nem chua", "thịt", "cá"],
            "lunch": ["cơm", "phở", "bún", "mì", "bánh mì", "bánh canh", "bún bò", "bún chả", "hủ tiếu", "gỏi cuốn", "salad", "cơm tấm", "cơm gà", "cơm rang", "thịt kho", "cá kho", "tôm", "gà", "bò", "heo"],
            "dinner": ["canh", "soup", "cháo", "cơm", "mì", "bún", "phở", "rau xào", "rau luộc", "rau trộn", "thịt hấp", "thịt nướng", "thịt chiên", "cá hấp", "cá kho", "tôm hấp", "nấm", "đậu", "tofu", "đậu phụ"],
            "snack": ["trái cây", "sữa chua", "hạt", "óc chó", "hạnh nhân", "nho khô", "khoai lang chiên", "bánh gối", "chè", "rau câu", "thạch", "chả giò", "gỏi cuốn"]
        }
        
        # Calculate minimum custom dishes
        total_meals = days * 3
        min_custom = int(total_meals * 0.4)
        
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI. Nhiệm vụ: tạo kế hoạch ăn uống ĐA DẠNG và CÂN BẰNG.

{lang_instruction}

{health_constraints}

{goal_guidance}

**YÊU CẦU VỀ ĐA DẠNG (RẤT QUAN TRỌNG):**
1. Tạo kế hoạch cho {days} ngày
2. Mỗi ngày phải có: 1 bữa sáng, 1 bữa trưa, 1 bữa tối, và CÓ THỂ có 1 bữa phụ
3. **ÍT NHẤT {min_custom} MÓN ĂN PHẢI LÀ MÓN MỚI TỰ TẠO** (is_custom: true)
   - Đây là yêu cầu BẮT BUỘC để đảm bảo đa dạng!
4. KHÔNG Được lặp lại cùng một món ăn trong toàn bộ kế hoạch
5. MỖI BỮA ĂN phải khác biệt về loại nguyên liệu chính

**VÍ DỤ VỀ ĐA DẠNG:**
- Ngày 1 bữa sáng: Bánh mì trứng → Ngày 2: Yến mạch cháo → Ngày 3: Phở bò → Ngày 4: Sinh tố bơ
- KHÔNG lặp lại bất kỳ món nào trong suốt kế hoạch

**PHÂN BỔ CALO THEO BỮA:**
- Bữa sáng ({labels['breakfast']}): {calorie_targets.get('breakfast', 0)} kcal
- Bữa trưa ({labels['lunch']}): {calorie_targets.get('lunch', 0)} kcal
- Bữa tối ({labels['dinner']}): {calorie_targets.get('dinner', 0)} kcal
- Bữa phụ ({labels['snack']}): {calorie_targets.get('snack', 0)} kcal

**DANH SÁCH MÓN ĂN CÓ SẴN (dùng làm tham khảo, ƯU TIÊN TẠO MÓN MỚI):**
{foods_text}

**HƯỚNG DẪN TẠO MÓN ĂN MỚI (BẮT BUỘC THỰC HIỆN):**
TẠO MÓN MỚI khi:
1. Món từ database đã dùng rồi → TẠO MỚI
2. Cần thay đổi để đa dạng → TẠO MỚI
3. Luôn ưu tiên TẠO MỚI thay vì chọn món cũ

KHI TẠO MÓN MỚI:
- Đặt tên món SÁNG TẠO: [Nguyên liệu chính] + [Cách chế biến] + [Phong cách]
  Ví dụ: "Ức Gà Áp Chảo Sốt Mè Rang", "Rau Củ Xào Tỏi Kiểu Nhật", "Cá Hồi Nướng Giấy Bạc"
- Ước tính calories và macros hợp lý cho 1 serving
- Liệt kê nguyên liệu chính (5-7 nguyên liệu)
- Hướng dẫn chế biến ngắn gọn (1-2 câu)
- TUYỆT ĐỐI tuân thủ các ràng buộc về dị ứng và chế độ ăn

**LOẠI MÓN ĂN ĐỂ THAM KHẢO KHI TẠO MỚI:**
- Bữa sáng: {", ".join(food_categories['breakfast'])}
- Bữa trưa: {", ".join(food_categories['lunch'])}
- Bữa tối: {", ".join(food_categories['dinner'])}
- Bữa phụ: {", ".join(food_categories['snack'])}

**ĐỊNH DẠNG TRẢ LỜI (CHỈ JSON, KHÔNG markdown):**
```json
{{
  "days": [
    {{
      "date": "Ngày 1",
      "meals": [
        {{
          "meal_type": "breakfast",
          "food_name": "Tên món ăn (ưu tiên món mới!)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carb,
          "fat_g": số_fat,
          "is_custom": true,
          "ingredients": ["nguyên liệu 1", "nguyên liệu 2", "nguyên liệu 3"]
        }},
        {{
          "meal_type": "lunch",
          "food_name": "Tên món ăn (ưu tiên món mới!)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carb,
          "fat_g": số_fat,
          "is_custom": true,
          "ingredients": ["nguyên liệu 1", "nguyên liệu 2", "nguyên liệu 3"]
        }},
        {{
          "meal_type": "dinner",
          "food_name": "Tên món ăn (ưu tiên món mới!)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carb,
          "fat_g": số_fat,
          "is_custom": true,
          "ingredients": ["nguyên liệu 1", "nguyên liệu 2", "nguyên liệu 3"]
        }},
        {{
          "meal_type": "snack",
          "food_name": "Tên món ăn (tùy chọn)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carb,
          "fat_g": số_fat,
          "is_custom": false
        }}
      ]
    }},
    // ... ngày tiếp theo với món ăn KHÁC NHAU hoàn toàn
  ]
}}
```

BẮT ĐẦU TRẢ LỜI (CHỈ JSON). Hãy đảm bảo TẠO ÍT NHẤT {min_custom} MÓN MỚI để đa dạng cho người dùng!
"""
        return prompt
    
    def _build_health_constraints(self, health_profile: Optional[Dict]) -> str:
        """Build health constraints text for prompt"""
        if not health_profile:
            return ""
        
        constraints = []
        
        # Allergies - STRICT prohibition
        allergies = health_profile.get("food_allergies", [])
        if allergies:
            allergen_list = ", ".join(allergies)
            # Expand allergen synonyms for AI understanding
            expanded_allergens = [allergen.lower() for allergen in allergies]
            for orig_allergen, synonyms in ALLERGEN_SYNONYMS.items():
                if any(orig_allergen.lower() in a.lower() for a in allergies):
                    expanded_allergens.extend([s.lower() for s in synonyms])
            
            expanded_list = ", ".join(set(expanded_allergens))
            constraints.append(f"""**🚫 TUYỆT ĐỐI CẤM - DỊ ỨNG:**
- Danh sách cấm: {allergen_list}
- Tất cả các món ăn trong kế hoạch KHÔNG ĐƯỢC chứa: {expanded_list}
- Nếu không chắc chắn, HÃY BỎ QUA món đó và tạo món mới thay thế""")
        
        # Dietary preferences
        dietary_prefs = health_profile.get("dietary_preferences", [])
        if dietary_prefs:
            pref_rules = []
            for pref in dietary_prefs:
                pref_lower = pref.lower()
                if pref_lower in DIETARY_RESTRICTIONS:
                    rules = DIETARY_RESTRICTIONS[pref_lower]
                    if rules.get("avoid"):
                        avoid_list = ", ".join(rules["avoid"])
                        pref_rules.append(f"- {pref}: KHÔNG chọn các món chứa [{avoid_list}]")
            
            if pref_rules:
                constraints.append(f"""**🍽️ CHẾ ĐỘ ĂN YÊU CẦU:**
{chr(10).join(pref_rules)}""")
        
        # Health conditions
        conditions = health_profile.get("health_conditions", [])
        if conditions:
            cond_tags = []
            for cond in conditions:
                cond_lower = cond.lower()
                for key, tags in HEALTH_CONDITION_TAGS.items():
                    if key in cond_lower:
                        cond_tags.extend(tags)
            
            if cond_tags:
                unique_tags = list(set(cond_tags))
                constraints.append(f"""**🏥 ĐIỀU KIỆN SỨC KHỎE:**
- Ưu tiên các món có tags: {', '.join(unique_tags)}
- Các món nên: Low Fat, Low Sodium, High Protein tùy theo điều kiện""")
        
        if constraints:
            return "**RÀNG BUỘC VỀ THỂ TRẠNG (TUYỆT ĐỐI TUÂN THỦ):**\n\n" + "\n\n".join(constraints)
        
        return ""
    
    def _build_goal_guidance(self, goal_type: str) -> str:
        """Build goal-specific guidance for prompt"""
        guidance = {
            "weight_loss": """**🎯 MỤC TIÊU: GIẢM CÂN**
- Ưu tiên protein cao, carb thấp
- Chọn món ít calo nhưng no lâu (salad, soup, protein)
- Hạn chế món chiên, nhiều dầu mỡ
- Có thể tạo món Low Carb thay thế""",
            
            "weight_gain": """**🎯 MỤC TIÊU: TĂNG CÂN**
- Ưu tiên calorie cao, protein cao
- Chọn món giàu dinh dưỡng (thịt, cá, trứng, gạo)
- Có thể thêm healthy fats (bơ, dầu olive)
- Tăng portion size nếu cần""",
            
            "maintain": """**🎯 MỤC TIÊU: DUY TRÌ CÂN NẶNG**
- Cân bằng dinh dưỡng: protein, carbs, fat đều có
- Ăn đa dạng các nhóm thực phẩm
- Không cần hạn chế quá nhiều""",
            
            "healthy_lifestyle": """**🎯 MỤC TIÊU: SỐNG KHỎE**
- Ưu tiên thực phẩm tươi, ít chế biến
- Cân bằng dinh dưỡng
- Ăn nhiều rau xanh, trái cây
- Hạn chế đồ chế biến sẵn"""
        }
        
        return guidance.get(goal_type, guidance["maintain"])
    
    def _parse_gemini_response(self, response_text: str, min_custom_count: int = 0) -> Dict:
        """Parse Gemini response into structured data with variety enforcement"""

        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = re.sub(r'```', '', cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)

            # Validate structure
            if "days" not in data:
                data = {"days": data.get("meal_plan", [data])}

            # Track all meal names for variety checking
            all_meal_names = []
            custom_count = 0

            # Validate and clean each meal
            for day in data.get("days", []):
                for meal in day.get("meals", []):
                    food_name = meal.get("food_name", "")

                    # Ensure required fields
                    if "is_custom" not in meal:
                        meal["is_custom"] = False

                    if meal["is_custom"]:
                        custom_count += 1
                        if "ingredients" not in meal or not meal["ingredients"]:
                            meal["ingredients"] = ["nguyên liệu chính"]
                    else:
                        # Non-custom meals don't need ingredients
                        meal.pop("ingredients", None)
                        meal.pop("recipe_notes", None)

                    # Ensure numeric fields
                    meal["calories"] = int(meal.get("calories", 0))
                    meal["protein_g"] = float(meal.get("protein_g", 0))
                    meal["carbs_g"] = float(meal.get("carbs_g", 0))
                    meal["fat_g"] = float(meal.get("fat_g", 0))

                    # Track meal names for variety
                    if food_name:
                        all_meal_names.append(food_name.lower())

            # Log variety statistics
            unique_meals = len(set(all_meal_names))
            total_meals = len(all_meal_names)
            logger.info(f"📊 Variety check: {unique_meals} unique / {total_meals} total meals, {custom_count} custom dishes")

            # If not enough custom dishes, convert some meals to custom
            if min_custom_count > 0 and custom_count < min_custom_count:
                logger.warning(f"⚠️ Only {custom_count} custom dishes, need at least {min_custom_count}. Converting non-custom meals to custom...")
                converted = 0
                for day in data.get("days", []):
                    for meal in day.get("meals", []):
                        if not meal.get("is_custom", False) and converted < (min_custom_count - custom_count):
                            meal["is_custom"] = True
                            meal["ingredients"] = ["nguyên liệu chính"]
                            converted += 1
                            logger.info(f"   Converted to custom: {meal.get('food_name', 'Unknown')}")
                custom_count += converted
                logger.info(f"   Now have {custom_count} custom dishes")

            # Check for duplicates and rename if needed
            seen_names = {}
            for day in data.get("days", []):
                for meal in day.get("meals", []):
                    name = meal.get("food_name", "")
                    if name:
                        name_lower = name.lower()
                        if name_lower in seen_names:
                            # Rename with variation
                            variations = [" (Biến tấu)", " (Phiên bản mới)", " (Đặc biệt)"]
                            meal["food_name"] = name + variations[seen_names[name_lower] % len(variations)]
                            seen_names[name_lower] += 1
                            logger.info(f"   Renamed duplicate: {name} -> {meal['food_name']}")
                        else:
                            seen_names[name_lower] = 1

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse failed: {e}")
            logger.error(f"Raw response: {response_text[:500]}")

            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass

            raise ValueError("AI returned invalid format")


# Singleton instance
_service_instance: Optional[MealPlanningAIService] = None


def get_meal_planning_ai_service() -> MealPlanningAIService:
    """Get singleton instance of MealPlanningAIService"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = MealPlanningAIService()
        logger.info("📋 MealPlanningAIService singleton created")
    
    return _service_instance
