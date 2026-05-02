"""
Meal Planning AI Service

AI-powered meal plan generation using Gemini.
This service replaces the mock data approach with actual AI-driven meal planning.
"""

import logging
from typing import Dict, List, Optional, Any
import json
import re
import os

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)


class MealPlanningAIService:
    """
    AI Service to generate intelligent meal plans using Gemini.
    
    Features:
    - Analyzes user's nutrition goals
    - Selects appropriate foods from database
    - Balances macros across meals
    - Diversifies diet to avoid repetition
    - Respects dietary preferences
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.temperature = 0.4  # Slightly creative for meal variety
        logger.info("✅ MealPlanningAIService initialized with Gemini")
    
    async def generate_meal_plan(
        self,
        daily_calorie_target: int,
        days: int,
        goal_type: str = "maintain",
        preferences: Optional[Dict] = None,
        available_foods: Optional[List[Dict]] = None,
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
            language: Response language (vi/en)
        
        Returns:
            Dict containing meal plan with days and meals
        """
        
        # Define calorie distribution based on goal type
        if goal_type == "weight_loss":
            meal_distribution = {
                "breakfast": 0.30,  # 30% - Higher morning for metabolism boost
                "lunch": 0.35,     # 35% - Main meal when active
                "dinner": 0.25,    # 25% - Lower evening to avoid fat storage
                "snack": 0.10      # 10% - Healthy snack
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
        
        # Build prompt for Gemini
        prompt = self._build_meal_plan_prompt(
            calorie_targets=meal_calorie_targets,
            days=days,
            goal_type=goal_type,
            preferences=preferences,
            available_foods=available_foods,
            language=language
        )
        
        try:
            # Call Gemini
            response = await self.model.generate_content_async(prompt)
            
            # Parse response
            meal_plan = self._parse_gemini_response(response.text)
            
            logger.info(f"✅ AI generated meal plan: {len(meal_plan.get('days', []))} days")
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
        language: str
    ) -> str:
        """Build detailed prompt for Gemini"""
        
        # Convert foods to text format
        if available_foods and len(available_foods) > 0:
            foods_text = "\n".join([
                f"- {f.get('name_vi', f.get('name', 'Unknown'))}: "
                f"{f.get('calories', 0)} kcal, "
                f"P: {f.get('protein', f.get('protein_g', 0))}g, "
                f"C: {f.get('carbs', f.get('carbs_g', 0))}g, "
                f"F: {f.get('fat', f.get('fat_g', 0))}g"
                for f in available_foods[:60]  # Limit to 60 foods for prompt size
            ])
        else:
            foods_text = """
- Cơm trắng (200g): 260 kcal, P: 5g, C: 57g, F: 0.5g
- Gà rang (100g): 165 kcal, P: 25g, C: 0g, F: 7g
- Rau muống xào (150g): 85 kcal, P: 3g, C: 8g, F: 4g
- Cá kho tộ (150g): 280 kcal, P: 30g, C: 8g, F: 14g
- Phở bò (1 tô): 450 kcal, P: 22g, C: 55g, F: 16g
- Bánh mì trứng (1 cái): 280 kcal, P: 12g, C: 35g, F: 10g
- Sữa tươi (1 ly): 120 kcal, P: 8g, C: 12g, F: 4g
- Trứng (1 quả): 75 kcal, P: 6g, C: 0.5g, F: 5g
- Thịt heo nạc (100g): 140 kcal, P: 21g, C: 0g, F: 6g
- Táo (1 quả): 52 kcal, P: 0.3g, C: 14g, F: 0.2g
"""
        
        preference_text = ""
        if preferences:
            if preferences.get("tags"):
                preference_text += f"\n- Tags: {', '.join(preferences['tags'])}"
            if preferences.get("categories"):
                preference_text += f"\n- Categories: {', '.join(preferences['categories'])}"
            if preferences.get("max_cook_time"):
                preference_text += f"\n- Max cooking time: {preferences['max_cook_time']} minutes"
        
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
        
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI. Nhiệm vụ: tạo kế hoạch ăn uống cân bằng dinh dưỡng.

{lang_instruction}

**YÊU CẦU:**
1. Tạo kế hoạch cho {days} ngày
2. Mỗi ngày phải có đủ: 1 bữa sáng, 1 bữa trưa, 1 bữa tối
3. Có thể thêm 1 bữa phụ (snack) - KHÔNG BẮT BUỘC
4. Đa dạng món ăn, KHÔNG lặp lại cùng một món trong 3 ngày liên tiếp
5. Tổng calo mỗi ngày xấp xỉ {sum(calorie_targets.values())} kcal

**PHÂN BỔ CALO THEO BỮA:**
- Bữa sáng (breakfast): {calorie_targets.get('breakfast', 0)} kcal (~30% daily)
- Bữa trưa (lunch): {calorie_targets.get('lunch', 0)} kcal (~35% daily)
- Bữa tối (dinner): {calorie_targets.get('dinner', 0)} kcal (~25% daily)
- Bữa phụ (snack): {calorie_targets.get('snack', 0)} kcal (~10% daily)

**MỤC TIÊU:** {goal_type}
{prference_text}

**DANH SÁCH MÓN ĂN CÓ SẴN:**
{foods_text}

**QUY TẮC QUAN TRỌNG:**
1. Chỉ chọn món từ danh sách có sẵn
2. Mỗi bữa chính (sáng/trưa/tối) phải có tối thiểu 15g protein
3. Đa dạng: không lặp lại món trong 3 ngày
4. Nếu cần, chọn món gần đúng với target calo nhất
5. Trả lời CHỈ có JSON, không thêm text khác

**ĐỊNH DẠNG TRẢ LỜI (JSON - KHÔNG markdown):**
{{
  "days": [
    {{
      "date": "Ngày 1",
      "meals": [
        {{
          "meal_type": "breakfast",
          "food_name": "Tên món ăn (phải có trong danh sách)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carbs,
          "fat_g": số_fat
        }},
        {{
          "meal_type": "lunch",
          "food_name": "Tên món ăn",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carb,
          "fat_g": số_fat
        }},
        {{
          "meal_type": "dinner",
          "food_name": "Tên món ăn",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carbs,
          "fat_g": số_fat
        }},
        {{
          "meal_type": "snack",
          "food_name": "Tên món ăn (tùy chọn)",
          "calories": số_calo,
          "protein_g": số_protein,
          "carbs_g": số_carbs,
          "fat_g": số_fat
        }}
      ]
    }},
    ...
  ]
}}

BẮT ĐẦU TRẢ LỜI (CHỈ JSON):
"""
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini response into structured data"""
        
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
