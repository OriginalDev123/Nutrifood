"""
Recipe Service
Business logic for recipe management
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal

from app.models.recipe import Recipe, RecipeIngredient, RecipeFavorite
from app.models.food import Food


# ==========================================
# RECIPE CRUD
# ==========================================

def create_recipe(
    db: Session,
    recipe_data: dict,
    creator_id: Optional[UUID] = None
) -> Recipe:
    """
    Create new recipe with ingredients
    
    Args:
        recipe_data: Dict containing recipe fields
        creator_id: User who created the recipe
    
    Returns:
        Created recipe object
    """
    
    # Extract ingredients separately
    ingredients_data = recipe_data.pop('ingredients', [])
    
    # Create recipe
    recipe = Recipe(
        **recipe_data,
        created_by=creator_id,
        source='user_submitted' if creator_id else 'admin'
    )
    
    db.add(recipe)
    db.flush()  # Get recipe_id
    
    # Add ingredients
    for idx, ingredient in enumerate(ingredients_data):
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.recipe_id,
            food_id=ingredient.get('food_id'),
            ingredient_name=ingredient['ingredient_name'],
            quantity=ingredient['quantity'],
            unit=ingredient['unit'],
            notes=ingredient.get('notes'),
            order_index=idx
        )
        db.add(recipe_ingredient)
    
    # Calculate nutrition if ingredients have food_id
    calculate_recipe_nutrition(db, recipe)
    
    db.commit()
    db.refresh(recipe)
    
    return recipe


def get_recipes(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    max_cook_time: Optional[int] = None,
    tags: Optional[List[str]] = None,
    verified_only: bool = False,
    public_only: bool = True
) -> List[Recipe]:
    """
    Get recipes with filtering
    
    Args:
        skip: Pagination offset
        limit: Number of recipes to return
        category: Filter by category
        difficulty: Filter by difficulty level
        max_cook_time: Maximum cooking time in minutes
        tags: Filter by tags (ANY match)
        verified_only: Only return verified recipes
        public_only: Only return public recipes
    
    Returns:
        List of recipes matching filters
    """
    
    query = db.query(Recipe).filter(Recipe.is_deleted == False)
    
    if category:
        query = query.filter(Recipe.category == category)
    
    if difficulty:
        query = query.filter(Recipe.difficulty_level == difficulty)
    
    if max_cook_time:
        query = query.filter(
            (Recipe.prep_time_minutes + Recipe.cook_time_minutes) <= max_cook_time
        )
    
    if tags:
        # Match any of the provided tags
        query = query.filter(Recipe.tags.overlap(tags))
    
    if verified_only:
        query = query.filter(Recipe.is_verified == True)
    
    if public_only:
        query = query.filter(Recipe.is_public == True)
    
    return query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit).all()


def get_recipe_by_id(
    db: Session,
    recipe_id: UUID,
    increment_view: bool = True
) -> Optional[Recipe]:
    """
    Get recipe by ID with optional view count increment
    
    Args:
        recipe_id: Recipe UUID
        increment_view: Whether to increment view count
    
    Returns:
        Recipe object or None
    """
    
    recipe = db.query(Recipe).filter(
        Recipe.recipe_id == recipe_id,
        Recipe.is_deleted == False
    ).first()
    
    if recipe and increment_view:
        recipe.view_count += 1
        db.commit()
    
    return recipe


def search_recipes(
    db: Session,
    query: str,
    limit: int = 20
) -> List[Recipe]:
    """
    Search recipes by name or description
    
    Args:
        query: Search query string
        limit: Maximum number of results
    
    Returns:
        List of matching recipes
    """
    
    search_pattern = f"%{query}%"
    
    return db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        or_(
            Recipe.name_vi.ilike(search_pattern),
            Recipe.name_en.ilike(search_pattern),
            Recipe.description.ilike(search_pattern)
        )
    ).limit(limit).all()


def update_recipe(
    db: Session,
    recipe_id: UUID,
    recipe_data: dict,
    user_id: UUID
) -> Recipe:
    """
    Update recipe (only by creator or admin)
    
    Args:
        recipe_id: Recipe UUID
        recipe_data: Updated fields
        user_id: User attempting update
    
    Returns:
        Updated recipe object
    
    Raises:
        ValueError: If recipe not found or user not authorized
    """
    
    recipe = db.query(Recipe).filter(
        Recipe.recipe_id == recipe_id,
        Recipe.is_deleted == False
    ).first()
    
    if not recipe:
        raise ValueError("Recipe not found")
    
    # Check authorization (creator or admin)
    # Note: Admin check should be done in route layer
    if recipe.created_by != user_id:
        raise ValueError("Not authorized to update this recipe")
    
    # Update fields
    for field, value in recipe_data.items():
        if field != 'ingredients' and hasattr(recipe, field):
            setattr(recipe, field, value)
    
    # Update ingredients if provided
    if 'ingredients' in recipe_data:
        # Delete existing ingredients
        db.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).delete()
        
        # Add new ingredients
        for idx, ingredient in enumerate(recipe_data['ingredients']):
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe_id,
                food_id=ingredient.get('food_id'),
                ingredient_name=ingredient['ingredient_name'],
                quantity=ingredient['quantity'],
                unit=ingredient['unit'],
                notes=ingredient.get('notes'),
                order_index=idx
            )
            db.add(recipe_ingredient)
        
        # Recalculate nutrition
        calculate_recipe_nutrition(db, recipe)
    
    db.commit()
    db.refresh(recipe)
    
    return recipe


def delete_recipe(
    db: Session,
    recipe_id: UUID,
    user_id: UUID,
    soft_delete: bool = True
) -> bool:
    """
    Delete recipe (soft or hard delete)
    
    Args:
        recipe_id: Recipe UUID
        user_id: User attempting delete
        soft_delete: Whether to soft delete (default) or hard delete
    
    Returns:
        True if deleted successfully
    
    Raises:
        ValueError: If recipe not found or user not authorized
    """
    
    recipe = db.query(Recipe).filter(
        Recipe.recipe_id == recipe_id,
        Recipe.is_deleted == False
    ).first()
    
    if not recipe:
        raise ValueError("Recipe not found")
    
    if recipe.created_by != user_id:
        raise ValueError("Not authorized to delete this recipe")
    
    if soft_delete:
        recipe.soft_delete() # Sử dụng mixin thay vì gán thủ công
    else:
        db.delete(recipe)
    
    db.commit()
    return True


# ==========================================
# NUTRITION CALCULATION
# ==========================================

def calculate_recipe_nutrition(db: Session, recipe: Recipe) -> None:
    """
    Calculate recipe nutrition from ingredients
    
    Updates recipe nutrition fields based on linked foods
    Only calculates if ingredients have food_id references
    
    Args:
        recipe: Recipe object to calculate nutrition for
    """
    
    ingredients = db.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.recipe_id
    ).all()
    
    total_calories = Decimal('0')
    total_protein = Decimal('0')
    total_carbs = Decimal('0')
    total_fat = Decimal('0')
    total_fiber = Decimal('0')
    
    calculated_count = 0
    
    for ingredient in ingredients:
        if not ingredient.food_id:
            continue
        
        food = db.query(Food).filter(Food.food_id == ingredient.food_id).first()
        if not food:
            continue
        
        # Convert quantity to grams (simplified - assumes unit is grams)
        # In production, you'd need unit conversion logic
        quantity_g = Decimal(ingredient.quantity)
        
        # Calculate nutrition based on per-100g values
        ratio = quantity_g / Decimal('100')
        
        total_calories += Decimal(food.calories_per_100g) * ratio
        total_protein += Decimal(food.protein_per_100g or 0) * ratio
        total_carbs += Decimal(food.carbs_per_100g or 0) * ratio
        total_fat += Decimal(food.fat_per_100g or 0) * ratio
        total_fiber += Decimal(food.fiber_per_100g or 0) * ratio
        
        calculated_count += 1
    
    # Only update if we successfully calculated from ingredients
    if calculated_count > 0 and recipe.servings > 0:
        servings = Decimal(recipe.servings)
        
        # Helper để làm tròn
        def r2(val): return (val / servings).quantize(Decimal("0.01"))

        recipe.calories_per_serving = r2(total_calories)
        recipe.protein_per_serving  = r2(total_protein)
        recipe.carbs_per_serving    = r2(total_carbs)
        recipe.fat_per_serving      = r2(total_fat)
        recipe.fiber_per_serving    = r2(total_fiber)


# ==========================================
# FAVORITES
# ==========================================

def add_favorite(
    db: Session,
    user_id: UUID,
    recipe_id: UUID,
    notes: Optional[str] = None
) -> RecipeFavorite:
    """
    Add recipe to user's favorites
    
    Args:
        user_id: User UUID
        recipe_id: Recipe UUID
        notes: Optional user notes
    
    Returns:
        RecipeFavorite object
    
    Raises:
        ValueError: If recipe not found or already favorited
    """
    
    # Check if recipe exists
    recipe = get_recipe_by_id(db, recipe_id, increment_view=False)
    if not recipe:
        raise ValueError("Recipe not found")
    
    # Check if already favorited
    existing = db.query(RecipeFavorite).filter(
        RecipeFavorite.user_id == user_id,
        RecipeFavorite.recipe_id == recipe_id
    ).first()
    
    if existing:
        raise ValueError("Recipe already in favorites")
    
    # Create favorite
    favorite = RecipeFavorite(
        user_id=user_id,
        recipe_id=recipe_id,
        notes=notes
    )
    
    db.add(favorite)
    
    # Increment favorite count
    recipe.favorite_count += 1
    
    db.commit()
    db.refresh(favorite)
    
    return favorite


def remove_favorite(
    db: Session,
    user_id: UUID,
    recipe_id: UUID
) -> bool:
    """
    Remove recipe from user's favorites
    
    Args:
        user_id: User UUID
        recipe_id: Recipe UUID
    
    Returns:
        True if removed successfully
    """
    
    favorite = db.query(RecipeFavorite).filter(
        RecipeFavorite.user_id == user_id,
        RecipeFavorite.recipe_id == recipe_id
    ).first()
    
    if not favorite:
        return False
    
    # Decrement favorite count
    recipe = get_recipe_by_id(db, recipe_id, increment_view=False)
    if recipe and recipe.favorite_count > 0:
        recipe.favorite_count -= 1
    
    db.delete(favorite)
    db.commit()
    
    return True


def get_user_favorites(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> List[Recipe]:
    """
    Get user's favorite recipes
    
    Args:
        user_id: User UUID
        skip: Pagination offset
        limit: Number of recipes to return
    
    Returns:
        List of favorited recipes
    """
    
    favorites = db.query(Recipe).join(RecipeFavorite).filter(
        RecipeFavorite.user_id == user_id,
        Recipe.is_deleted == False
    ).order_by(RecipeFavorite.created_at.desc()).offset(skip).limit(limit).all()
    
    return favorites


def is_favorited(
    db: Session,
    user_id: UUID,
    recipe_id: UUID
) -> bool:
    """
    Check if user has favorited a recipe
    
    Args:
        user_id: User UUID
        recipe_id: Recipe UUID
    
    Returns:
        True if favorited, False otherwise
    """
    
    favorite = db.query(RecipeFavorite).filter(
        RecipeFavorite.user_id == user_id,
        RecipeFavorite.recipe_id == recipe_id
    ).first()
    
    return favorite is not None


# ==========================================
# STATISTICS
# ==========================================

def get_recipe_categories(db: Session) -> List[str]:
    """Get all recipe categories"""
    
    result = db.query(Recipe.category).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True
    ).distinct().all()
    
    return [row[0] for row in result]


def get_popular_recipes(
    db: Session,
    limit: int = 10,
    time_period: str = "all_time"  # all_time, month, week
) -> List[Recipe]:
    """
    Get popular recipes by view count or favorites
    
    Args:
        limit: Number of recipes to return
        time_period: Filter by time period
    
    Returns:
        List of popular recipes
    """
    
    query = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True
    )
    
    if time_period == "week":
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Recipe.created_at >= cutoff)
    elif time_period == "month":
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Recipe.created_at >= cutoff)
    
    # Order by combination of views and favorites
    query = query.order_by(
        (Recipe.view_count + Recipe.favorite_count * 5).desc()
    )
    
    return query.limit(limit).all()


def get_recipe_recommendations(
    db: Session,
    user_id: UUID,
    limit: int = 10
) -> List[Recipe]:
    """
    Get personalized recipe recommendations
    
    Simple algorithm:
    1. Get user's favorite recipe categories
    2. Recommend popular recipes from those categories
    3. Exclude already favorited recipes
    
    Args:
        user_id: User UUID
        limit: Number of recommendations
    
    Returns:
        List of recommended recipes
    """
    
    # Get user's favorite categories
    favorite_categories = db.query(Recipe.category).join(RecipeFavorite).filter(
        RecipeFavorite.user_id == user_id
    ).group_by(Recipe.category).order_by(
        func.count(Recipe.recipe_id).desc()
    ).limit(3).all()
    
    categories = [cat[0] for cat in favorite_categories]
    
    # Get favorited recipe IDs to exclude
    favorited_ids = db.query(RecipeFavorite.recipe_id).filter(
        RecipeFavorite.user_id == user_id
    ).all()
    favorited_ids = [fav[0] for fav in favorited_ids]
    
    # Query recommendations
    query = db.query(Recipe).filter(
        Recipe.is_deleted == False,
        Recipe.is_public == True,
        Recipe.recipe_id.notin_(favorited_ids) if favorited_ids else True
    )
    
    # Prioritize user's favorite categories
    if categories:
        query = query.filter(Recipe.category.in_(categories))
    
    # Order by popularity
    query = query.order_by(
        (Recipe.view_count + Recipe.favorite_count * 5).desc()
    )
    
    return query.limit(limit).all()