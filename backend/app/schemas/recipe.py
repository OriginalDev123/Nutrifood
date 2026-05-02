from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Union, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# ==========================================
# INSTRUCTION STEP SCHEMA
# ==========================================

class InstructionStep(BaseModel):
    """Structured instruction step"""
    step: int
    text: str

# ==========================================
# INGREDIENT SCHEMAS
# ==========================================

class RecipeIngredientBase(BaseModel):
    ingredient_name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    unit: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None
    food_id: Optional[UUID] = None
    order_index: Optional[int] = Field(0, ge=0)
class RecipeIngredientCreate(RecipeIngredientBase):
    pass

class RecipeIngredientResponse(RecipeIngredientBase):
    ingredient_id: UUID

    class Config:
        from_attributes = True

# ==========================================
# RECIPE SCHEMAS
# ==========================================

class RecipeBase(BaseModel):
    name_vi: str = Field(..., min_length=2, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=2, max_length=100)
    cuisine_type: Optional[str] = None
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    servings: int = Field(..., gt=0)
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    instructions: Optional[str] = None
    instructions_steps: Optional[Union[List[str], List[InstructionStep], List[Dict[str, Any]]]] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_public: bool = True
    tags: Optional[List[str]] = []

class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = Field(..., min_items=1)

class RecipeUpdate(BaseModel):
    name_vi: Optional[str] = None
    category: Optional[str] = None
    servings: Optional[int] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None
    # Thêm các trường khác tùy nhu cầu

class RecipeResponse(RecipeBase):
    recipe_id: UUID
    calories_per_serving: Optional[Decimal] = None
    protein_per_serving: Optional[Decimal] = None
    carbs_per_serving: Optional[Decimal] = None
    fat_per_serving: Optional[Decimal] = None
    fiber_per_serving: Optional[Decimal] = None
    view_count: int
    favorite_count: int
    is_verified: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecipeDetailResponse(RecipeResponse):
    ingredients: List[RecipeIngredientResponse]
    is_favorited: bool = False # Field động từ Service

# ==========================================
# FAVORITE SCHEMAS
# ==========================================

class RecipeFavoriteCreate(BaseModel):
    notes: Optional[str] = None

class RecipeFavoriteResponse(BaseModel):
    favorite_id: UUID
    user_id: UUID
    recipe_id: UUID
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# RECIPE MATCHER SCHEMAS
# ==========================================

class MatchIngredientsRequest(BaseModel):
    ingredient_ids: List[UUID] = Field(..., min_items=1, description="List of ingredient food IDs user has")
    min_match_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum match score (0.0-1.0)")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of recipes to return")
    category: Optional[str] = Field(None, description="Filter by recipe category")

class MissingIngredient(BaseModel):
    ingredient_name: str
    quantity: Decimal
    unit: str
    food_id: Optional[UUID] = None

class RecipeMatch(BaseModel):
    recipe_id: UUID
    name_vi: str
    name_en: Optional[str]
    category: str
    match_score: float = Field(..., ge=0.0, le=1.0, description="How well ingredients match (0.0-1.0)")
    match_level: str = Field(..., pattern="^(excellent|good|partial)$")
    matched_count: int = Field(..., ge=0, description="Number of ingredients user has")
    total_count: int = Field(..., gt=0, description="Total ingredients required")
    missing_count: int = Field(..., ge=0, description="Number of missing ingredients")
    missing_ingredients: List[MissingIngredient]
    image_url: Optional[str]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    difficulty_level: Optional[str]

class MatchIngredientsResponse(BaseModel):
    matches: List[RecipeMatch]
    total_count: int
    user_ingredient_count: int

class ShoppingListRequest(BaseModel):
    recipe_ids: List[UUID] = Field(..., min_items=1, description="List of recipe IDs to shop for")
    available_ingredient_ids: List[UUID] = Field(default_factory=list, description="Ingredients user already has")

class ShoppingListItem(BaseModel):
    ingredient_name: str
    total_quantity: Decimal
    unit: str
    food_id: Optional[UUID] = None
    recipe_names: List[str] = Field(..., description="Recipes requiring this ingredient")

class ShoppingListResponse(BaseModel):
    shopping_list: List[ShoppingListItem]
    total_items: int
    recipes_count: int

class SubstitutionOption(BaseModel):
    food_id: UUID
    name_vi: str
    name_en: Optional[str]
    reason: str = Field(..., description="Why this is a good substitute")

class IngredientSubstitution(BaseModel):
    original_ingredient: str
    substitution_options: List[SubstitutionOption]

class RecipeSubstitutionsResponse(BaseModel):
    recipe_id: UUID
    recipe_name: str
    substitutions: List[IngredientSubstitution]