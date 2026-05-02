"""
Recipe Routes
API endpoints for recipe management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.food import PortionPreset
from app.schemas import recipe as schemas
from app.services import recipe_service
from app.services.recipe_matcher_service import RecipeMatcherService
from app.utils.dependencies import get_current_active_user, require_admin
from uuid import UUID


router = APIRouter(
    prefix="/recipes",
    tags=["Recipes"]
)


# ==========================================
# RECIPE CRUD
# ==========================================

@router.post("", response_model=schemas.RecipeDetailResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    recipe_data: schemas.RecipeCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create new recipe with ingredients
    
    **Body:**
    - name_vi: Recipe name in Vietnamese (required)
    - category: Recipe category (required)
    - servings: Number of servings (required)
    - ingredients: List of ingredients (required, min 1)
    - instructions: Cooking instructions
    - prep_time_minutes: Preparation time
    - cook_time_minutes: Cooking time
    - difficulty_level: easy/medium/hard
    - tags: Array of tags
    
    **Returns:**
    - Created recipe with calculated nutrition
    
    **Example:**
    ```json
    {
      "name_vi": "Phở bò",
      "category": "Soup",
      "servings": 4,
      "prep_time_minutes": 30,
      "cook_time_minutes": 120,
      "difficulty_level": "medium",
      "ingredients": [
        {
          "ingredient_name": "Beef bones",
          "quantity": 1000,
          "unit": "gram",
          "notes": "For broth"
        },
        {
          "food_id": "uuid-of-rice-noodles",
          "ingredient_name": "Rice noodles",
          "quantity": 400,
          "unit": "gram"
        }
      ],
      "instructions": "1. Boil bones...",
      "tags": ["vietnamese", "soup", "beef"]
    }
    ```
    """
    
    try:
        recipe = recipe_service.create_recipe(
            db=db,
            recipe_data=recipe_data.model_dump(),
            creator_id=current_user.user_id
        )
        
        return recipe
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[schemas.RecipeResponse])
def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None, regex="^(easy|medium|hard)$"),
    max_cook_time: Optional[int] = Query(None, ge=0),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    verified_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get recipes with optional filtering
    
    **Query Parameters:**
    - skip: Pagination offset (default: 0)
    - limit: Number of recipes (1-100, default: 20)
    - category: Filter by category
    - difficulty: Filter by difficulty (easy/medium/hard)
    - max_cook_time: Maximum total cooking time in minutes
    - tags: Comma-separated tags (e.g., "vegetarian,low-carb")
    - verified_only: Only return admin-verified recipes
    
    **Returns:**
    - Array of recipes matching filters
    
    **Example:**
    ```
    GET /recipes?category=Soup&difficulty=easy&max_cook_time=60
    GET /recipes?tags=vegetarian,healthy&verified_only=true
    ```
    """
    
    # Parse tags
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    recipes = recipe_service.get_recipes(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        difficulty=difficulty,
        max_cook_time=max_cook_time,
        tags=tags_list,
        verified_only=verified_only
    )
    
    return recipes


@router.get("/search", response_model=List[schemas.RecipeResponse])
def search_recipes(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search recipes by name or description
    
    **Query Parameters:**
    - q: Search query string (required)
    - limit: Maximum number of results (1-50, default: 20)
    
    **Returns:**
    - Array of recipes matching search query
    
    **Example:**
    ```
    GET /recipes/search?q=phở
    GET /recipes/search?q=chicken&limit=10
    ```
    """
    
    recipes = recipe_service.search_recipes(
        db=db,
        query=q,
        limit=limit
    )
    
    return recipes


@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all recipe categories
    
    **Returns:**
    - Array of unique category names
    
    **Example:**
    ```
    GET /recipes/categories
    ```
    """
    
    categories = recipe_service.get_recipe_categories(db)
    return categories


@router.get("/popular", response_model=List[schemas.RecipeResponse])
def get_popular_recipes(
    limit: int = Query(10, ge=1, le=50),
    time_period: str = Query("all_time", regex="^(all_time|month|week)$"),
    db: Session = Depends(get_db)
):
    """
    Get popular recipes by views and favorites
    
    **Query Parameters:**
    - limit: Number of recipes (1-50, default: 10)
    - time_period: all_time, month, or week (default: all_time)
    
    **Returns:**
    - Array of popular recipes sorted by popularity
    
    **Example:**
    ```
    GET /recipes/popular?limit=10&time_period=week
    ```
    """
    
    recipes = recipe_service.get_popular_recipes(
        db=db,
        limit=limit,
        time_period=time_period
    )
    
    return recipes


@router.get("/recommendations", response_model=List[schemas.RecipeResponse])
def get_recommendations(
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recipe recommendations
    
    Based on user's favorite recipes and preferences
    
    **Query Parameters:**
    - limit: Number of recommendations (1-20, default: 10)
    
    **Returns:**
    - Array of recommended recipes
    
    **Example:**
    ```
    GET /recipes/recommendations?limit=10
    ```
    """
    
    recommendations = recipe_service.get_recipe_recommendations(
        db=db,
        user_id=current_user.user_id,
        limit=limit
    )
    
    return recommendations


@router.get("/{recipe_id}", response_model=schemas.RecipeDetailResponse)
def get_recipe_detail(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed recipe information
    
    Includes ingredients, instructions, and nutrition
    Automatically increments view count
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Returns:**
    - Detailed recipe information with ingredients
    
    **Example:**
    ```
    GET /recipes/{recipe_id}
    ```
    """
    
    try:
        from uuid import UUID
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe = recipe_service.get_recipe_by_id(
        db=db,
        recipe_id=recipe_uuid,
        increment_view=True
    )
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Check if user has favorited this recipe
    is_favorited = recipe_service.is_favorited(
        db=db,
        user_id=current_user.user_id,
        recipe_id=recipe_uuid
    )
    
    response = schemas.RecipeDetailResponse.model_validate(recipe, from_attributes=True)
    response.is_favorited = is_favorited

    return response


@router.get("/{recipe_id}/portions")
async def get_recipe_portion_presets(
    recipe_id: str,
    db: Session = Depends(get_db)
):
    """
    Get portion presets for a recipe
    
    Returns list of available portion sizes (small/medium/large)
    for Vision AI integration.
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Returns:**
    - Array of portion presets
    
    **Example response:**
    ```json
    [
        {
            "preset_id": "uuid",
            "size_label": "medium",
            "display_name_vi": "Phần vừa",
            "display_name_en": "Medium portion",
            "unit_type": "plate",
            "unit_display_vi": "dĩa",
            "grams": 350,
            "is_default": true,
            "sort_order": 2,
            "item_type": "recipe",
            "recipe_id": "uuid",
            "recipe_name": "Ức gà nướng hương thảo"
        }
    ]
    ```
    """
    # Validate recipe_id format
    try:
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipe ID format"
        )
    
    # Check if recipe exists
    recipe = recipe_service.get_recipe_by_id(
        db=db,
        recipe_id=recipe_uuid,
        increment_view=False
    )
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Get portion presets
    presets = db.query(PortionPreset).filter(
        PortionPreset.recipe_id == recipe_uuid
    ).order_by(PortionPreset.sort_order).all()
    
    # Convert to dict
    return [preset.to_dict() for preset in presets]


@router.patch("/{recipe_id}", response_model=schemas.RecipeDetailResponse)
def update_recipe(
    recipe_id: str,
    recipe_data: schemas.RecipeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update recipe (only by creator)
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Body:**
    - Any recipe fields to update (all optional)
    
    **Returns:**
    - Updated recipe
    
    **Example:**
    ```json
    PATCH /recipes/{recipe_id}
    {
      "difficulty_level": "easy",
      "prep_time_minutes": 20,
      "tags": ["quick", "easy", "healthy"]
    }
    ```
    """
    
    try:
        from uuid import UUID
        recipe_uuid = UUID(recipe_id)
        
        updated_recipe = recipe_service.update_recipe(
            db=db,
            recipe_id=recipe_uuid,
            recipe_data=recipe_data.model_dump(exclude_unset=True),
            user_id=current_user.user_id
        )
        
        return updated_recipe
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        elif "not authorized" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete recipe (soft delete, only by creator)
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Returns:**
    - 204 No Content on success
    
    **Example:**
    ```
    DELETE /recipes/{recipe_id}
    ```
    """
    
    try:
        from uuid import UUID
        recipe_uuid = UUID(recipe_id)
        
        recipe_service.delete_recipe(
            db=db,
            recipe_id=recipe_uuid,
            user_id=current_user.user_id,
            soft_delete=True
        )
        
        return None
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        elif "not authorized" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# FAVORITES
# ==========================================

@router.post("/{recipe_id}/favorite", response_model=schemas.RecipeFavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(
    recipe_id: str,
    favorite_data: schemas.RecipeFavoriteCreate = schemas.RecipeFavoriteCreate(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add recipe to favorites
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Body (optional):**
    - notes: Personal notes about the recipe
    
    **Returns:**
    - Favorite record
    
    **Example:**
    ```json
    POST /recipes/{recipe_id}/favorite
    {
      "notes": "My mom's version is better!"
    }
    ```
    """
    
    try:
        from uuid import UUID
        recipe_uuid = UUID(recipe_id)
        
        favorite = recipe_service.add_favorite(
            db=db,
            user_id=current_user.user_id,
            recipe_id=recipe_uuid,
            notes=favorite_data.notes
        )
        
        return favorite
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        elif "already" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove recipe from favorites
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Returns:**
    - 204 No Content on success
    
    **Example:**
    ```
    DELETE /recipes/{recipe_id}/favorite
    ```
    """
    
    try:
        from uuid import UUID
        recipe_uuid = UUID(recipe_id)
        
        removed = recipe_service.remove_favorite(
            db=db,
            user_id=current_user.user_id,
            recipe_id=recipe_uuid
        )
        
        if not removed:
            raise HTTPException(status_code=404, detail="Recipe not in favorites")
        
        return None
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")


@router.get("/favorites/my", response_model=List[schemas.RecipeResponse])
def get_my_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite recipes
    
    **Query Parameters:**
    - skip: Pagination offset (default: 0)
    - limit: Number of recipes (1-100, default: 20)
    
    **Returns:**
    - Array of favorited recipes
    
    **Example:**
    ```
    GET /recipes/favorites/my?limit=20
    ```
    """
    
    favorites = recipe_service.get_user_favorites(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return favorites


# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@router.patch("/{recipe_id}/verify", response_model=schemas.RecipeDetailResponse)
def verify_recipe(
    recipe_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Verify recipe (admin only)
    
    **Path Parameters:**
    - recipe_id: Recipe UUID
    
    **Returns:**
    - Updated recipe with is_verified=True
    
    **Example:**
    ```
    PATCH /recipes/{recipe_id}/verify
    ```
    """
    from uuid import UUID
    recipe_uuid = UUID(recipe_id)
    
    recipe = recipe_service.get_recipe_by_id(db, recipe_uuid, increment_view=False)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe.is_verified = True
    db.commit()
    db.refresh(recipe)
    
    return recipe


# ==========================================
# RECIPE MATCHER ENDPOINTS
# ==========================================

@router.post("/match-ingredients", 
             response_model=schemas.MatchIngredientsResponse,
             summary="Match recipes based on available ingredients",
             description="Find recipes that can be made with the ingredients you have. Returns recipes sorted by match quality.")
async def match_recipes_by_ingredients(
    request: schemas.MatchIngredientsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Match recipes based on user's available ingredients.
    
    **Match Levels:**
    - **excellent**: ≥90% ingredients match
    - **good**: ≥75% ingredients match  
    - **partial**: ≥50% ingredients match (or custom min_match_score)
    
    **Parameters:**
    - **ingredient_ids**: List of food IDs the user has
    - **min_match_score**: Minimum match threshold (0.0-1.0, default 0.5)
    - **limit**: Max recipes to return (1-100, default 20)
    - **category**: Optional category filter
    
    **Returns:**
    - List of matching recipes with scores and missing ingredients
    """
    try:
        matcher_service = RecipeMatcherService(db)
        matches = matcher_service.match_recipes(
            ingredient_ids=request.ingredient_ids,
            min_match_score=request.min_match_score,
            limit=request.limit
        )
        
        return schemas.MatchIngredientsResponse(
            matches=matches,
            total_count=len(matches),
            user_ingredient_count=len(request.ingredient_ids)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching recipes: {str(e)}")


@router.post("/shopping-list",
             response_model=schemas.ShoppingListResponse,
             summary="Generate shopping list for multiple recipes",
             description="Create aggregated shopping list for selected recipes, excluding ingredients you already have.")
async def generate_shopping_list(
    request: schemas.ShoppingListRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a consolidated shopping list for multiple recipes.
    
    **Features:**
    - Aggregates quantities for duplicate ingredients
    - Excludes ingredients user already has
    - Groups by ingredient with recipe references
    
    **Parameters:**
    - **recipe_ids**: List of recipe IDs to shop for (1-20 recipes)
    - **available_ingredient_ids**: Food IDs user already has (optional)
    
    **Returns:**
    - Aggregated shopping list with quantities and recipe associations
    """
    if len(request.recipe_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 recipes allowed per shopping list")
    
    try:
        matcher_service = RecipeMatcherService(db)
        result = matcher_service.generate_shopping_list(
            recipe_ids=request.recipe_ids,
            available_ingredient_ids=request.available_ingredient_ids
        )
        
        return schemas.ShoppingListResponse(
            shopping_list=result["shopping_list"],
            total_items=result["total_items"],
            recipes_count=result["recipes_count"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating shopping list: {str(e)}")


@router.get("/{recipe_id}/substitutions",
            response_model=schemas.RecipeSubstitutionsResponse,
            summary="Get ingredient substitution suggestions",
            description="Suggest alternative ingredients for a recipe based on nutritional similarity.")
async def get_recipe_substitutions(
    recipe_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get substitution suggestions for recipe ingredients.
    
    **Substitution Logic:**
    - Finds alternatives from same food category
    - Matches similar nutritional profile
    - Returns up to 3 options per ingredient
    - Provides reasoning for each suggestion
    
    **Parameters:**
    - **recipe_id**: UUID of the recipe
    
    **Returns:**
    - List of ingredients with substitution options
    """
    try:
        matcher_service = RecipeMatcherService(db)
        result = matcher_service.get_recipe_substitutions(
            recipe_id=recipe_id
        )
        
        # Get recipe name for response
        recipe = recipe_service.get_recipe_by_id(db, recipe_id, increment_view=False)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return schemas.RecipeSubstitutionsResponse(
            recipe_id=recipe_id,
            recipe_name=recipe.name_vi,
            substitutions=result["substitutions"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting substitutions: {str(e)}")