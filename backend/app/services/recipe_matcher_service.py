"""
Recipe Matcher Service - Optimized Version
Match user ingredients to available recipes with smart scoring

PERFORMANCE OPTIMIZATIONS:
- Single query for all ingredients (fixes N+1 problem)
- Batch missing ingredient lookups
- Cache UUID string conversions
- Target: <300ms for 100 recipes

Business Logic:
- Excellent match: ≥90% ingredients available
- Good match: ≥75% ingredients available  
- Partial match: ≥50% ingredients available
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Set, Optional
from uuid import UUID
from collections import defaultdict
import logging

from app.models.recipe import Recipe, RecipeIngredient
from app.models.food import Food

logger = logging.getLogger(__name__)


class RecipeMatcherService:
    """
    Optimized recipe matching service
    
    Algorithm:
    1. Query top N popular recipes (limit search space)
    2. Fetch ALL their ingredients in 1 query (fix N+1)
    3. Group ingredients by recipe_id in memory
    4. Calculate match scores without DB queries
    5. Batch query all missing ingredient details ONCE
    6. Return sorted results
    
    Performance:
    - Before: ~150 queries for 100 recipes
    - After: 4 queries total
    """
    
    # Match level thresholds
    EXCELLENT_MATCH = 0.90
    GOOD_MATCH = 0.75
    PARTIAL_MATCH = 0.50
    
    def __init__(self, db: Session):
        """Initialize service with database session"""
        self.db = db
    
    def match_recipes(
        self,
        ingredient_ids: List[UUID],
        min_match_score: float = 0.5,
        limit: int = 20,
        max_recipes_to_scan: int = 200
    ) -> List[Dict]:
        """
        Find recipes matching available ingredients
        
        Args:
            ingredient_ids: List of food IDs user has
            min_match_score: Minimum match score (0.0-1.0)
            limit: Max number of results to return
            max_recipes_to_scan: Max recipes to evaluate (performance limiter)
        
        Returns:
            List of matching recipes sorted by score (best first)
            
        Example:
            >>> matcher = RecipeMatcherService(db)
            >>> matches = matcher.match_recipes(
            ...     ingredient_ids=[uuid1, uuid2, uuid3],
            ...     min_match_score=0.6,
            ...     limit=10
            ... )
            >>> print(matches[0])
            {
                "recipe_id": "...",
                "name_vi": "Phở bò",
                "match_score": 0.85,
                "match_level": "good",
                "total_ingredients": 12,
                "available_ingredients": 10,
                "missing_ingredients": [...]
            }
        """
        
        if not ingredient_ids:
            logger.warning("No ingredients provided for matching")
            return []
        
        # Convert to string set once (avoid repeated UUID->str conversions)
        available_set = {str(id) for id in ingredient_ids}
        
        logger.info(
            f"🔍 Matching recipes with {len(available_set)} ingredients "
            f"(min_score: {min_match_score})"
        )
        
        # ============================================
        # STEP 1: Get top recipes (limit search space)
        # ============================================
        # Query only popular/verified recipes to improve performance
        
        recipes = self.db.query(Recipe).filter(
            Recipe.is_deleted == False,
            Recipe.is_public == True
        ).order_by(
            Recipe.view_count.desc()  # Popular recipes first
        ).limit(max_recipes_to_scan).all()
        
        if not recipes:
            logger.warning("No recipes found in database")
            return []
        
        recipe_ids = [r.recipe_id for r in recipes]
        
        logger.debug(f"📊 Scanning {len(recipes)} recipes")
        
        # ============================================
        # STEP 2: Get ALL ingredients in 1 query (FIX N+1!)
        # ============================================
        
        all_ingredients = self.db.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id.in_(recipe_ids),
            RecipeIngredient.is_deleted == False  # Fix: was using deleted_at
        ).all()
        
        logger.debug(f"📦 Loaded {len(all_ingredients)} total ingredients")
        
        # ============================================
        # STEP 3: Group ingredients by recipe (Python dict)
        # ============================================
        
        ingredients_by_recipe = defaultdict(list)
        for ingredient in all_ingredients:
            ingredients_by_recipe[ingredient.recipe_id].append(ingredient)
        
        # ============================================
        # STEP 4: Calculate match scores (NO queries in loop!)
        # ============================================
        
        matches = []
        all_missing_ids = set()  # Collect all missing IDs for batch query
        
        for recipe in recipes:
            recipe_ingredients = ingredients_by_recipe[recipe.recipe_id]
            
            if not recipe_ingredients:
                continue  # Skip recipes with no ingredients
            
            # Calculate match score
            total = len(recipe_ingredients)
            required_ids = {str(ing.food_id) for ing in recipe_ingredients if ing.food_id}
            available_count = len(required_ids & available_set)
            match_score = available_count / total if total > 0 else 0.0
            
            # Filter by minimum score
            if match_score >= min_match_score:
                missing_ids = required_ids - available_set
                all_missing_ids.update(missing_ids)
                
                # Store recipe_ingredients for later (to get quantity/unit)
                matches.append({
                    "recipe_id": str(recipe.recipe_id),
                    "name_vi": recipe.name_vi,
                    "name_en": recipe.name_en,
                    "category": recipe.category,
                    "difficulty_level": recipe.difficulty_level,
                    "prep_time_minutes": recipe.prep_time_minutes,
                    "cook_time_minutes": recipe.cook_time_minutes,
                    "total_time_minutes": (recipe.prep_time_minutes or 0) + (recipe.cook_time_minutes or 0),
                    "servings": recipe.servings,
                    "description": recipe.description,
                    "match_score": round(match_score, 3),
                    "match_level": self._get_match_level(match_score),
                    "matched_count": available_count,  # Schema expects this name
                    "total_count": total,              # Schema expects this name
                    "missing_count": len(missing_ids),
                    "_missing_ids": missing_ids,  # Temp storage (removed later)
                    "_recipe_ingredients": recipe_ingredients,  # Store for missing ingredient details
                    "nutrition": {
                        "calories": float(recipe.calories_per_serving or 0),
                        "protein_g": float(recipe.protein_per_serving or 0),
                        "carbs_g": float(recipe.carbs_per_serving or 0),
                        "fat_g": float(recipe.fat_per_serving or 0)
                    },
                    "image_url": recipe.image_url,
                    "view_count": recipe.view_count,
                    "is_verified": recipe.is_verified
                })
        
        logger.info(f"✅ Found {len(matches)} recipes matching criteria")
        
        # ============================================
        # STEP 5: Query ALL missing ingredients ONCE
        # ============================================
        # Fix: Previously queried in loop (inefficient)
        
        if all_missing_ids:
            logger.debug(f"🔍 Looking up {len(all_missing_ids)} missing ingredients")
            
            missing_foods = self.db.query(Food).filter(
                Food.food_id.in_([UUID(id) for id in all_missing_ids]),
                Food.is_deleted == False
            ).all()
            
            # Create lookup dict for O(1) access
            missing_lookup = {str(f.food_id): f for f in missing_foods}
            
            # Fill in missing ingredient details with quantity/unit from recipe
            for match in matches:
                missing_ingredients = []
                for recipe_ing in match['_recipe_ingredients']:
                    if str(recipe_ing.food_id) in match['_missing_ids']:
                        food_id_str = str(recipe_ing.food_id)
                        if food_id_str in missing_lookup:
                            food = missing_lookup[food_id_str]
                            missing_ingredients.append({
                                "ingredient_name": food.name_vi,  # Schema expects this field name
                                "quantity": float(recipe_ing.quantity),  # From recipe_ingredients
                                "unit": recipe_ing.unit,  # From recipe_ingredients
                                "food_id": food_id_str
                            })
                
                match['missing_ingredients'] = missing_ingredients
                del match['_missing_ids']  # Clean up temp fields
                del match['_recipe_ingredients']  
        else:
            # All ingredients available for all matches
            for match in matches:
                match['missing_ingredients'] = []
                del match['_missing_ids']
                if '_recipe_ingredients' in match:
                    del match['_recipe_ingredients']
        
        # ============================================
        # STEP 6: Sort and limit results
        # ============================================
        
        # Primary sort: match_score (descending)
        # Secondary sort: view_count (descending) for same scores
        matches.sort(key=lambda x: (x['match_score'], x['view_count']), reverse=True)
        
        return matches[:limit]
    
    def _get_match_level(self, score: float) -> str:
        """
        Convert numeric score to match level
        
        Args:
            score: Match score (0.0-1.0)
        
        Returns:
            "excellent" | "good" | "partial"
        """
        if score >= self.EXCELLENT_MATCH:
            return "excellent"
        elif score >= self.GOOD_MATCH:
            return "good"
        else:
            return "partial"
    
    def generate_shopping_list(
        self,
        recipe_ids: List[UUID],
        available_ingredient_ids: List[UUID]
    ) -> Dict:
        """
        Generate shopping list for selected recipes
        
        Args:
            recipe_ids: List of recipe IDs to cook
            available_ingredient_ids: Ingredients user already has
        
        Returns:
            {
                "recipes_count": 3,
                "shopping_list": [
                    {
                        "food_id": "...",
                        "name_vi": "Cà rốt",
                        "quantity": 500,
                        "unit": "gram",
                        "used_in_recipes": ["Phở bò", "Canh chua"]
                    }
                ],
                "total_items": 12,
                "estimated_cost": null
            }
        """
        
        if not recipe_ids:
            return {
                "recipes_count": 0,
                "shopping_list": [],
                "total_items": 0
            }
        
        # Convert to sets for O(1) lookup
        available_set = {str(id) for id in available_ingredient_ids}
        
        # Query all ingredients for selected recipes
        ingredients = self.db.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id.in_(recipe_ids),
            RecipeIngredient.is_deleted == False
        ).all()
        
        # Query recipe names for reference
        recipes = self.db.query(Recipe).filter(
            Recipe.recipe_id.in_(recipe_ids)
        ).all()
        recipe_names = {str(r.recipe_id): r.name_vi for r in recipes}
        
        # Group by food_id and aggregate quantities
        shopping_dict = defaultdict(lambda: {
            "quantity": 0,
            "unit": None,
            "recipes": []
        })
        
        for ing in ingredients:
            if not ing.food_id:
                continue  # Skip non-food ingredients
            
            food_id_str = str(ing.food_id)
            recipe_name = recipe_names.get(str(ing.recipe_id), "Unknown")
            
            # Skip if user already has this ingredient
            if food_id_str in available_set:
                continue
            
            shopping_dict[food_id_str]["quantity"] += float(ing.quantity or 0)
            shopping_dict[food_id_str]["unit"] = ing.unit
            shopping_dict[food_id_str]["recipes"].append(recipe_name)
        
        # Query food details
        if shopping_dict:
            food_ids = [UUID(fid) for fid in shopping_dict.keys()]
            foods = self.db.query(Food).filter(
                Food.food_id.in_(food_ids)
            ).all()
            
            shopping_list = []
            for food in foods:
                fid = str(food.food_id)
                data = shopping_dict[fid]
                
                shopping_list.append({
                    "ingredient_name": food.name_vi,  # Schema expects this name
                    "total_quantity": round(data["quantity"], 1),  # Schema expects this name
                    "unit": data["unit"],
                    "food_id": fid,
                    "recipe_names": list(set(data["recipes"]))  # Schema expects this name
                })
            
            # Sort by ingredient name
            shopping_list.sort(key=lambda x: x["ingredient_name"])
        else:
            shopping_list = []
        
        return {
            "recipes_count": len(recipe_ids),
            "shopping_list": shopping_list,
            "total_items": len(shopping_list)
        }
    
    def get_recipe_substitutions(
        self,
        recipe_id: UUID,
        missing_ingredient_ids: Optional[List[UUID]] = None
    ) -> Dict:
        """
        Suggest ingredient substitutions for a recipe
        
        Args:
            recipe_id: Recipe to find substitutions for
            missing_ingredient_ids: Ingredients to find substitutes for (if None, get ALL recipe ingredients)
        
        Returns:
            {
                "recipe_id": "...",
                "substitutions": [
                    {
                        "original": {"name_vi": "Bò", ...},
                        "alternatives": [
                            {"name_vi": "Gà", "similarity": 0.8},
                            {"name_vi": "Heo", "similarity": 0.7}
                        ]
                    }
                ]
            }
        
        Note: Basic implementation - can enhance with category-based matching
        """
        
        # If no specific ingredients provided, get all ingredients from the recipe
        if missing_ingredient_ids is None:
            recipe_ingredients = self.db.query(RecipeIngredient).filter(
                RecipeIngredient.recipe_id == recipe_id,
                RecipeIngredient.is_deleted == False
            ).all()
            
            # Get food IDs from recipe ingredients
            missing_ingredient_ids = [
                ing.food_id for ing in recipe_ingredients 
                if ing.food_id is not None
            ]
            
            if not missing_ingredient_ids:
                return {
                    "recipe_id": str(recipe_id),
                    "substitutions": []
                }
        
        # Query ingredients details
        missing_foods = self.db.query(Food).filter(
            Food.food_id.in_(missing_ingredient_ids),
            Food.is_deleted == False
        ).all()
        
        substitutions = []
        
        for food in missing_foods:
            # Find alternatives in same category
            alternatives = self.db.query(Food).filter(
                Food.category == food.category,
                Food.food_id != food.food_id,
                Food.is_deleted == False
            ).limit(5).all()
            
            if alternatives:
                substitutions.append({
                    "original_ingredient": food.name_vi,  # Schema expects string name
                    "substitution_options": [
                        {
                            "food_id": str(alt.food_id),
                            "name_vi": alt.name_vi,
                            "name_en": alt.name_en,
                            "reason": f"Same category ({alt.category})"  # Schema expects reason string
                        }
                        for alt in alternatives
                    ]
                })
        
        return {
            "recipe_id": str(recipe_id),
            "substitutions": substitutions
        }


# ==========================================
# HELPER FUNCTIONS
# ==========================================
# FACTORY FUNCTION
# ==========================================

def get_recipe_matcher(db: Session) -> RecipeMatcherService:
    """
    Factory function to get RecipeMatcherService instance
    
    Usage:
        matcher = get_recipe_matcher(db)
        results = matcher.match_recipes(ingredient_ids=[...])
    """
    return RecipeMatcherService(db)
