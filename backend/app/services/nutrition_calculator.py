"""
Nutrition Calculator Core
Shared logic for Module 3 (Recommendations) and Module 5 (AI Meal Planner)

Provides:
- Daily remaining nutrient calculations
- Food matching based on nutrient gaps
- Meal nutrient aggregation
- Meal rebalancing logic
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.models.user import UserGoal
from app.models.food_log import FoodLog
from app.models.food import Food


class NutritionCalculatorCore:
    """
    Core nutrition calculation service
    
    Used by:
    - RecommendationService (Module 3): Real-time meal suggestions
    - AI Meal Planner (Module 5): Week plan generation and validation
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_daily_remaining(
        self, 
        user_id: UUID, 
        target_date: date
    ) -> Dict[str, float]:
        """
        Calculate remaining nutrients for a specific date
        
        Formula: Target - Consumed = Remaining
        
        Args:
            user_id: User UUID
            target_date: Date to calculate for
        
        Returns:
            Dictionary with remaining nutrients:
            {
                "calories": 800.0,
                "protein": 45.5,
                "carbs": 80.0,
                "fat": 25.0,
                "fiber": 10.0
            }
        
        Raises:
            ValueError: If user has no active goal
        
        Example:
            >>> calculator = NutritionCalculatorCore(db)
            >>> remaining = calculator.calculate_daily_remaining(user_id, date.today())
            >>> print(f"Còn thiếu {remaining['calories']} calories")
        """
        
        # 1. Get user's active goal
        goal = self.db.query(UserGoal).filter(
            UserGoal.user_id == user_id,
            UserGoal.is_active == True,
            UserGoal.is_deleted == False
        ).first()
        
        if not goal:
            raise ValueError("No active goal found. User must create a goal first.")
        
        if not goal.daily_calorie_target:
            raise ValueError("Goal must have daily_calorie_target set.")
        
        # 2. Sum consumed nutrients for the date
        consumed = self.db.query(
            func.coalesce(func.sum(FoodLog.calories), 0).label('calories'),
            func.coalesce(func.sum(FoodLog.protein_g), 0).label('protein'),
            func.coalesce(func.sum(FoodLog.carbs_g), 0).label('carbs'),
            func.coalesce(func.sum(FoodLog.fat_g), 0).label('fat')
        ).filter(
            FoodLog.user_id == user_id,
            FoodLog.meal_date == target_date,
            FoodLog.is_deleted == False
        ).first()
        
        # 3. Calculate remaining (target - consumed)
        remaining = {
            "calories": float(goal.daily_calorie_target - (consumed.calories or 0)),
            "protein": float((goal.protein_target_g or 0) - (consumed.protein or 0)),
            "carbs": float((goal.carbs_target_g or 0) - (consumed.carbs or 0)),
            "fat": float((goal.fat_target_g or 0) - (consumed.fat or 0))
        }
        
        return remaining
    
    def find_foods_matching_gap(
        self,
        nutrient_gap: Dict[str, float],
        meal_type: str,
        top_k: int = 5
    ) -> List[Food]:
        """
        Find foods that best match the nutrient gap
        
        Algorithm:
        1. Filter foods by meal_type category (breakfast: dairy/grains, lunch: meat/grains, etc.)
        2. Score each food based on how well it fills the gap
        3. Return top K highest scoring foods
        
        Scoring:
        - Calorie match: 40% weight
        - Protein match: 40% weight
        - Verified status: 20% bonus
        
        Args:
            nutrient_gap: Remaining nutrients (from calculate_daily_remaining)
            meal_type: "breakfast" | "lunch" | "dinner" | "snack"
            top_k: Number of foods to return
        
        Returns:
            List of Food objects sorted by match score
        
        Example:
            >>> gap = {"calories": 600, "protein": 30, "carbs": 80, "fat": 15}
            >>> foods = calculator.find_foods_matching_gap(gap, "dinner", top_k=5)
            >>> print(f"Top suggestion: {foods[0].name_vi}")
        """
        
        # Import constants (created in task 3)
        from app.utils.constants import MEAL_CATEGORY_MAP
        
        # 1. Get suitable categories for meal_type
        suitable_categories = MEAL_CATEGORY_MAP.get(meal_type, [])
        
        if not suitable_categories:
            # Fallback: query all foods
            foods = self.db.query(Food).filter(
                Food.is_deleted == False
            ).all()
        else:
            # Query foods by category
            foods = self.db.query(Food).filter(
                Food.category.in_(suitable_categories),
                Food.is_deleted == False
            ).all()
        
        if not foods:
            return []
        
        # 2. Score each food
        scored_foods: List[Tuple[Food, float]] = []
        
        for food in foods:
            score = self._calculate_match_score(food, nutrient_gap)
            
            if score > 0.3:  # Minimum 30% match to be considered
                scored_foods.append((food, score))
        
        # 3. Sort by score descending
        scored_foods.sort(key=lambda x: x[1], reverse=True)
        
        # 4. Return top K foods only (not scores)
        return [food for food, score in scored_foods[:top_k]]
    
    def _calculate_match_score(
        self, 
        food: Food, 
        gap: Dict[str, float]
    ) -> float:
        """
        Calculate how well a food matches nutrient gap
        
        Score formula:
        - Calorie match: 1 - |gap - food| / gap     (40% weight)
        - Protein match: 1 - |gap - food| / gap     (40% weight)
        - Verified bonus: +20% if food.is_verified
        
        Returns: Score between 0.0 and 1.0
        """
        
        # Get food nutrition per 100g
        food_cal = float(food.calories_per_100g or 0)
        food_protein = float(food.protein_per_100g or 0)
        
        # Avoid division by zero
        gap_cal = max(gap.get("calories", 0), 1)
        gap_protein = max(gap.get("protein", 0), 1)
        
        # Calculate individual match scores (0-1 range)
        # Score is high when food value is close to gap value
        cal_match = 1 - abs(gap_cal - food_cal) / gap_cal
        protein_match = 1 - abs(gap_protein - food_protein) / gap_protein
        
        # Clamp to 0-1 range
        cal_match = max(0, min(1, cal_match))
        protein_match = max(0, min(1, protein_match))
        
        # Weighted sum (40% cal + 40% protein)
        base_score = cal_match * 0.4 + protein_match * 0.4
        
        # Add verified bonus (20%)
        verified_bonus = 0.2 if food.is_verified else 0
        
        return base_score + verified_bonus
    
    def calculate_meal_nutrients(
        self,
        meal_items: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate total nutrients for a list of meal items
        
        Args:
            meal_items: List of dicts with keys:
                - food_id: UUID (optional)
                - calories: Decimal
                - protein_g: Decimal
                - carbs_g: Decimal
                - fat_g: Decimal
        
        Returns:
            Total nutrients:
            {
                "calories": 1500.0,
                "protein": 80.0,
                "carbs": 180.0,
                "fat": 50.0
            }
        
        Example:
            >>> items = [
            ...     {"calories": Decimal("500"), "protein_g": Decimal("30")},
            ...     {"calories": Decimal("300"), "protein_g": Decimal("20")}
            ... ]
            >>> total = calculator.calculate_meal_nutrients(items)
            >>> print(f"Total calories: {total['calories']}")
        """
        
        total = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0
        }
        
        for item in meal_items:
            total["calories"] += float(item.get("calories") or 0)
            total["protein"] += float(item.get("protein_g") or 0)
            total["carbs"] += float(item.get("carbs_g") or 0)
            total["fat"] += float(item.get("fat_g") or 0)
        
        return total
    
    def rebalance_meals(
        self,
        meals: List[Dict],
        goal: UserGoal,
        tolerance: float = 0.1
    ) -> List[Dict]:
        """
        Adjust meal portions to meet daily calorie target
        
        Algorithm:
        1. Calculate total calories from all meals
        2. If within tolerance (±10%), return as-is
        3. If over/under, scale all meal quantities proportionally
        
        Args:
            meals: List of meal dicts with "calories" and "quantity" keys
            goal: UserGoal object with daily_calorie_target
            tolerance: Acceptable deviation (0.1 = ±10%)
        
        Returns:
            Adjusted meals with updated quantities
        
        Example:
            >>> meals = [
            ...     {"calories": 600, "quantity": 1.0},
            ...     {"calories": 800, "quantity": 1.0}
            ... ]
            >>> goal = UserGoal(daily_calorie_target=2000)
            >>> balanced = calculator.rebalance_meals(meals, goal)
            >>> # Meals scaled to total 2000 calories
        """
        
        if not goal.daily_calorie_target:
            return meals  # Cannot rebalance without target
        
        # 1. Calculate current total
        current_total = sum(float(meal.get("calories", 0)) for meal in meals)
        
        if current_total == 0:
            return meals  # Avoid division by zero
        
        target = float(goal.daily_calorie_target)
        
        # 2. Check if within tolerance
        deviation = abs(current_total - target) / target
        
        if deviation <= tolerance:
            return meals  # Already balanced
        
        # 3. Calculate scaling factor
        scale_factor = target / current_total
        
        # 4. Scale all meals
        rebalanced = []
        for meal in meals:
            adjusted = meal.copy()
            
            # Scale quantity
            current_qty = float(meal.get("quantity", 1.0))
            adjusted["quantity"] = current_qty * scale_factor
            
            # Recalculate nutrients
            adjusted["calories"] = float(meal.get("calories", 0)) * scale_factor
            adjusted["protein_g"] = float(meal.get("protein_g", 0)) * scale_factor
            adjusted["carbs_g"] = float(meal.get("carbs_g", 0)) * scale_factor
            adjusted["fat_g"] = float(meal.get("fat_g", 0)) * scale_factor
            
            rebalanced.append(adjusted)
        
        return rebalanced
    
    def get_active_goal(self, user_id: UUID) -> Optional[UserGoal]:
        """
        Get user's active goal
        
        Args:
            user_id: User UUID
        
        Returns:
            UserGoal object or None if not found
        """
        
        return self.db.query(UserGoal).filter(
            UserGoal.user_id == user_id,
            UserGoal.is_active == True,
            UserGoal.is_deleted == False
        ).first()
    
    def validate_daily_total(
        self,
        daily_nutrients: Dict[str, float],
        goal: UserGoal,
        tolerance: float = 0.15
    ) -> bool:
        """
        Check if daily nutrients are within acceptable range of target
        
        Args:
            daily_nutrients: Total nutrients for the day
            goal: UserGoal with targets
            tolerance: Acceptable deviation (0.15 = ±15%)
        
        Returns:
            True if within tolerance, False otherwise
        
        Example:
            >>> nutrients = {"calories": 2100, "protein": 125}
            >>> goal = UserGoal(daily_calorie_target=2000, target_protein=120)
            >>> is_valid = calculator.validate_daily_total(nutrients, goal)
            >>> print(f"Plan is valid: {is_valid}")
        """
        
        if not goal.daily_calorie_target:
            return False
        
        target_cal = float(goal.daily_calorie_target)
        actual_cal = daily_nutrients.get("calories", 0)
        
        # Check calorie deviation
        cal_deviation = abs(actual_cal - target_cal) / target_cal
        
        if cal_deviation > tolerance:
            return False
        
        # Optional: Check protein if target set
        if goal.protein_target_g:
            target_protein = float(goal.protein_target_g)
            actual_protein = daily_nutrients.get("protein", 0)
            protein_deviation = abs(actual_protein - target_protein) / target_protein
            
            if protein_deviation > tolerance * 1.5:  # More lenient for protein
                return False
        
        return True


# Singleton instance (optional, can also instantiate in services)
def get_nutrition_calculator(db: Session) -> NutritionCalculatorCore:
    """Factory function to create calculator instance"""
    return NutritionCalculatorCore(db)
