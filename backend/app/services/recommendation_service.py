"""
Recommendation Service - Smart Food Suggestions
Rule-based recommendations (NO AI calls - fast <500ms)
Uses NutritionCalculatorCore for all calculations
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import logging

from app.services.nutrition_calculator import NutritionCalculatorCore
from app.models.food import Food

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Real-time meal recommendations based on nutrient gaps
    
    Features:
    - Database-driven only (no AI calls)
    - Fast response (<500ms)
    - Uses NutritionCalculatorCore
    - Vietnamese reason generation
    """
    
    def __init__(self, db: Optional[Session]):
        """
        Initialize recommendation service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.calculator = NutritionCalculatorCore(db) if db is not None else None
        logger.debug("✅ RecommendationService initialized")
    
    async def suggest_next_meal(
        self,
        user_id: UUID,
        meal_type: str,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Suggest foods cho bữa ăn tiếp theo based on remaining nutrients
        
        Algorithm:
        1. Calculate remaining nutrients using NutritionCalculatorCore
        2. Find matching foods using calculator
        3. Generate reasons và serving suggestions
        4. Return top 5 với confidence scores
        
        Args:
            user_id: User ID
            meal_type: breakfast | lunch | dinner | snack
            target_date: Date to calculate (default: today)
        
        Returns:
            {
                "meal_type": str,
                "date": str,
                "remaining_nutrients": dict,
                "suggestions": list[dict]
            }
        
        Raises:
            ValueError: Nếu user không có active goal
        """
        
        start_time = datetime.now()
        
        # Use today nếu không specify date
        if target_date is None:
            target_date = datetime.now().date()
        
        logger.info(
            f"🔍 Getting recommendations for user {user_id}: "
            f"{meal_type} on {target_date}"
        )
        
        try:
            if self.db is None or self.calculator is None:
                raise ValueError("Database session is required for recommendations")

            # === BƯỚC 1: Calculate remaining nutrients ===
            gap = self.calculator.calculate_daily_remaining(
                user_id=user_id,
                target_date=target_date
            )
            
            logger.debug(
                f"📊 Nutrient gap: calories={gap['calories']:.1f}, "
                f"protein={gap['protein']:.1f}g"
            )
            
            # === BƯỚC 2: Find matching foods ===
            candidates = self.calculator.find_foods_matching_gap(
                nutrient_gap=gap,
                meal_type=meal_type,
                top_k=5
            )
            
            logger.debug(f"🍽️ Found {len(candidates)} candidate foods")
            
            # === BƯỚC 3: Format suggestions với confidence, reason, serving ===
            suggestions = []
            
            for food in candidates:
                # Calculate confidence score
                confidence = self._calculate_confidence(food, gap)
                
                # Generate Vietnamese reason
                reason = self._generate_reason(food, gap, meal_type)
                
                # Suggest serving size
                serving = self._suggest_serving(food, gap)
                
                suggestions.append({
                    "food_id": str(food.food_id),
                    "name_vi": food.name_vi,
                    "name_en": food.name_en,
                    "confidence": round(confidence, 2),
                    "reason": reason,
                    "serving_suggestion": serving,
                    "nutrition_per_100g": {
                        "calories": float(food.calories_per_100g or 0),
                        "protein": float(food.protein_per_100g or 0),
                        "carbs": float(food.carbs_per_100g or 0),
                        "fat": float(food.fat_per_100g or 0)
                    },
                    "category": food.category,
                    "is_verified": food.is_verified
                })
            
            # === BƯỚC 4: Return result ===
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(
                f"✅ Generated {len(suggestions)} recommendations "
                f"(time: {elapsed_ms}ms)"
            )
            
            return {
                "meal_type": meal_type,
                "date": target_date.strftime("%Y-%m-%d"),
                "remaining_nutrients": {
                    "calories": round(gap["calories"], 1),
                    "protein": round(gap["protein"], 1),
                    "carbs": round(gap["carbs"], 1),
                    "fat": round(gap["fat"], 1)
                },
                "suggestions": suggestions,
                "processing_time_ms": elapsed_ms
            }
        
        except ValueError as e:
            logger.error(f"❌ Recommendation error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to generate recommendations: {str(e)}")
    
    def _calculate_confidence(self, food: Food, gap: Dict[str, float]) -> float:
        """
        Calculate confidence score (0-1) cho food suggestion
        
        Confidence components:
        - Calorie match: 40% (closer to gap = higher score)
        - Protein match: 40% (protein là priority)
        - Verified status: 20% (verified foods = more trustworthy)
        
        Args:
            food: Food object
            gap: Remaining nutrients dict
        
        Returns:
            Confidence score (0-1)
        """
        
        # Get food nutrition per 100g
        food_calories = float(food.calories_per_100g or 0)
        food_protein = float(food.protein_per_100g or 0)
        
        # Prevent division by zero
        gap_calories = max(gap["calories"], 1)
        gap_protein = max(gap["protein"], 1)
        
        # === COMPONENT 1: Calorie Match (40%) ===
        # Closer to gap calories = higher score
        # Formula: 1 - (absolute_difference / gap)
        cal_diff = abs(gap["calories"] - food_calories)
        cal_match = 1 - (cal_diff / gap_calories)
        cal_match = max(0, min(1, cal_match))  # Clamp to [0, 1]
        
        # === COMPONENT 2: Protein Match (40%) ===
        protein_diff = abs(gap["protein"] - food_protein)
        protein_match = 1 - (protein_diff / gap_protein)
        protein_match = max(0, min(1, protein_match))
        
        # === COMPONENT 3: Verified Bonus (20%) ===
        verified_bonus = 0.2 if food.is_verified else 0.0
        
        # === FINAL CONFIDENCE ===
        confidence = (
            cal_match * 0.4 +
            protein_match * 0.4 +
            verified_bonus
        )
        
        return confidence
    
    def _generate_reason(
        self,
        food: Food,
        gap: Dict[str, float],
        meal_type: str
    ) -> str:
        """
        Generate human-readable reason in Vietnamese
        
        Logic:
        1. Nếu thiếu nhiều protein (>20g) và food giàu protein → reason về protein
        2. Nếu thiếu nhiều calories (>500) → reason về calories
        3. Nếu thiếu carbs (>50g) và food giàu carbs → reason về carbs
        4. Default: cân đối dinh dưỡng
        
        Args:
            food: Food object
            gap: Remaining nutrients
            meal_type: breakfast/lunch/dinner/snack
        
        Returns:
            Vietnamese reason string
        """
        
        # Get food nutrition
        protein = float(food.protein_per_100g or 0)
        calories = float(food.calories_per_100g or 0)
        carbs = float(food.carbs_per_100g or 0)
        fat = float(food.fat_per_100g or 0)
        
        # === RULE 1: High protein need + High protein food ===
        if gap["protein"] > 20 and protein > 15:
            return f"Giàu protein ({protein:.1f}g/100g), còn thiếu {gap['protein']:.0f}g protein"
        
        # === RULE 2: High calorie need ===
        elif gap["calories"] > 500 and calories > 200:
            return f"Cung cấp {calories:.0f} calories, còn thiếu {gap['calories']:.0f} calo"
        
        # === RULE 3: High carbs need + High carbs food ===
        elif gap["carbs"] > 50 and carbs > 20:
            meal_name = {
                "breakfast": "bữa sáng",
                "lunch": "bữa trưa",
                "dinner": "bữa tối",
                "snack": "bữa phụ"
            }.get(meal_type, "bữa ăn")
            
            return f"Giàu carbs ({carbs:.1f}g/100g), phù hợp cho {meal_name}"
        
        # === RULE 4: Low fat food (healthy choice) ===
        elif fat < 5 and gap["protein"] > 10:
            return f"Ít chất béo ({fat:.1f}g/100g), giàu protein - lựa chọn lành mạnh"
        
        # === RULE 5: High fiber (if data available) ===
        elif food.fiber_per_100g and float(food.fiber_per_100g) > 3:
            return f"Giàu chất xơ ({float(food.fiber_per_100g):.1f}g/100g), tốt cho tiêu hóa"
        
        # === DEFAULT: Balanced ===
        else:
            return "Cân đối dinh dưỡng, phù hợp với mục tiêu của bạn"
    
    def _suggest_serving(
        self,
        food: Food,
        gap: Dict[str, float]
    ) -> str:
        """
        Calculate appropriate serving size based on calorie gap
        
        Logic:
        - Tính grams cần thiết để đạt calorie gap
        - Clamp trong khoảng hợp lý (50-300g)
        - Round to readable numbers
        
        Args:
            food: Food object
            gap: Remaining nutrients
        
        Returns:
            Serving size string (VD: "150g", "1 bát (~200g)")
        """
        
        food_calories = float(food.calories_per_100g or 1)  # Prevent division by zero
        
        # Nếu food có 0 calories (unlikely), return default
        if food_calories == 0:
            return "100g"
        
        # Calculate grams needed to fill calorie gap
        # Formula: (gap_calories / calories_per_100g) * 100
        grams_needed = (gap["calories"] / food_calories) * 100
        
        # Clamp to reasonable range (50-300g)
        grams_needed = max(50, min(300, grams_needed))
        
        # Round to nearest 10 or 25
        if grams_needed < 100:
            grams_needed = round(grams_needed / 10) * 10
        else:
            grams_needed = round(grams_needed / 25) * 25
        
        # Format với Vietnamese context
        if 80 <= grams_needed <= 120:
            return f"{int(grams_needed)}g (~1 chén nhỏ)"
        elif 180 <= grams_needed <= 220:
            return f"{int(grams_needed)}g (~1 bát)"
        elif 280 <= grams_needed <= 300:
            return f"{int(grams_needed)}g (~1 bát to)"
        else:
            return f"{int(grams_needed)}g"
    
    def get_meal_timing_suggestions(
        self,
        user_id: UUID,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Suggest which meal type user should eat next based on time and logs
        
        Logic:
        - Check current time
        - Check which meals already logged today
        - Suggest next appropriate meal
        
        Args:
            user_id: User ID
            target_date: Date to check (default: today)
        
        Returns:
            {
                "suggested_meal_type": str,
                "reason": str,
                "already_logged": list[str]
            }
        """
        
        from app.models.food_log import FoodLog
        
        if target_date is None:
            target_date = datetime.now().date()
        
        # Get today's food logs
        logged_meals = self.db.query(FoodLog.meal_type).filter(
            FoodLog.user_id == user_id,
            FoodLog.meal_date == target_date,
            FoodLog.is_deleted == False
        ).distinct().all()
        
        logged_meal_types = {meal[0] for meal in logged_meals}
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # Suggest based on time and what's logged
        if current_hour < 10 and "breakfast" not in logged_meal_types:
            return {
                "suggested_meal_type": "breakfast",
                "reason": "Đã đến giờ ăn sáng",
                "already_logged": list(logged_meal_types)
            }
        
        elif 11 <= current_hour < 14 and "lunch" not in logged_meal_types:
            return {
                "suggested_meal_type": "lunch",
                "reason": "Đã đến giờ ăn trưa",
                "already_logged": list(logged_meal_types)
            }
        
        elif 17 <= current_hour < 21 and "dinner" not in logged_meal_types:
            return {
                "suggested_meal_type": "dinner",
                "reason": "Đã đến giờ ăn tối",
                "already_logged": list(logged_meal_types)
            }
        
        else:
            return {
                "suggested_meal_type": "snack",
                "reason": "Có thể ăn nhẹ nếu cảm thấy đói",
                "already_logged": list(logged_meal_types)
            }