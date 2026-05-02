"""
Admin Routes
Endpoints for admin user management, content moderation, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timedelta
from uuid import UUID

from app.database import get_db
from app.models.user import User, UserProfile, UserGoal
from app.models.food import Food
from app.models.recipe import Recipe, RecipeIngredient
from app.models.meal_plan import MealPlan, MealPlanItem
from app.models.food_log import FoodLog
from app.schemas.user import UserResponse
from app.utils.dependencies import require_admin
from pydantic import BaseModel
from sqlalchemy import func, or_, and_

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# ADMIN SCHEMAS
# ==========================================

class UserListResponse(BaseModel):
    """Paginated user list response"""
    total: int
    skip: int
    limit: int
    users: List[UserResponse]


class UserStatusUpdate(BaseModel):
    """Schema for updating user status"""
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    email_verified: Optional[bool] = None


class UserStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    active_users: int
    admin_users: int
    verified_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


# ==========================================
# FOOD ADMIN SCHEMAS
# ==========================================

class FoodAdminResponse(BaseModel):
    """Food response for admin panel"""
    food_id: UUID
    name_vi: str
    name_en: Optional[str]
    category: str
    cuisine_type: Optional[str]
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    barcode: Optional[str]
    image_url: Optional[str]
    source: Optional[str]
    is_verified: bool
    created_by: Optional[UUID]
    creator_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FoodListResponse(BaseModel):
    """Paginated food list response"""
    total: int
    skip: int
    limit: int
    foods: List[FoodAdminResponse]


class FoodVerifyRequest(BaseModel):
    """Schema for verifying food"""
    is_verified: bool


class FoodStatusResponse(BaseModel):
    """Food verification response"""
    food_id: UUID
    name_vi: str
    is_verified: bool
    verified_at: datetime


# ==========================================
# RECIPE ADMIN SCHEMAS
# ==========================================

class RecipeAdminResponse(BaseModel):
    """Recipe response for admin panel"""
    recipe_id: UUID
    name_vi: str
    name_en: Optional[str]
    category: str
    cuisine_type: Optional[str]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: int
    difficulty_level: Optional[str]
    calories_per_serving: Optional[float]
    protein_per_serving: Optional[float]
    carbs_per_serving: Optional[float]
    fat_per_serving: Optional[float]
    image_url: Optional[str]
    source: Optional[str]
    is_verified: bool
    is_public: bool
    created_by: Optional[UUID]
    creator_name: Optional[str]
    view_count: int
    favorite_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecipeListResponse(BaseModel):
    """Paginated recipe list response"""
    total: int
    skip: int
    limit: int
    recipes: List[RecipeAdminResponse]


class RecipeVerifyRequest(BaseModel):
    """Schema for verifying recipe"""
    is_verified: bool


# ==========================================
# MEAL PLAN ADMIN SCHEMAS
# ==========================================

class MealPlanAdminResponse(BaseModel):
    """Meal plan response for admin panel"""
    plan_id: UUID
    user_id: UUID
    user_email: str
    user_name: Optional[str]
    plan_name: str
    start_date: date
    end_date: date
    duration_days: int
    is_active: bool
    is_completed: bool
    total_meals: int
    total_calories: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MealPlanListResponse(BaseModel):
    """Paginated meal plan list response"""
    total: int
    skip: int
    limit: int
    meal_plans: List[MealPlanAdminResponse]


# ==========================================
# ANALYTICS / DASHBOARD SCHEMAS
# ==========================================

class SystemStats(BaseModel):
    """Comprehensive system statistics for admin dashboard"""
    # User stats
    total_users: int
    active_users: int
    admin_users: int
    verified_users: int
    inactive_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    # Content stats
    total_foods: int
    verified_foods: int
    unverified_foods: int
    total_recipes: int
    verified_recipes: int
    unverified_recipes: int
    total_meal_plans: int
    active_meal_plans: int
    # Engagement stats
    total_food_logs: int
    logs_this_week: int
    logs_this_month: int


# ==========================================
# ADMIN ENDPOINTS - USERS
# ==========================================

@router.get("/users", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all users (Admin only)
    """
    query = db.query(User)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    total = query.count()
    
    users = query.order_by(User.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": users
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific user (Admin only)"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format"
        )
    
    user = db.query(User).filter(User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    profile = db.query(UserProfile)\
        .filter(UserProfile.user_id == user_uuid)\
        .first()
    
    active_goal = db.query(UserGoal)\
        .filter(UserGoal.user_id == user_uuid, UserGoal.is_active == True)\
        .first()
    
    # Get stats
    food_logs_count = db.query(FoodLog).filter(FoodLog.user_id == user_uuid).count()
    meal_plans_count = db.query(MealPlan).filter(MealPlan.user_id == user_uuid).count()
    
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "profile": profile,
        "active_goal": active_goal,
        "stats": {
            "food_logs_count": food_logs_count,
            "meal_plans_count": meal_plans_count
        }
    }


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user status (Admin only)"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format"
        )
    
    user = db.query(User).filter(User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.user_id == current_admin.user_id and status_update.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges"
        )
    
    update_data = status_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Permanently delete a user (Admin only)"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format"
        )
    
    if user_uuid == current_admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        db.delete(user)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


# ==========================================
# ADMIN ENDPOINTS - FOODS
# ==========================================

@router.get("/foods", response_model=FoodListResponse)
def list_foods_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of all foods (Admin only)"""
    query = db.query(Food)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Food.name_vi.ilike(search_pattern),
                Food.name_en.ilike(search_pattern)
            )
        )
    
    if category:
        query = query.filter(Food.category == category)
    
    if is_verified is not None:
        query = query.filter(Food.is_verified == is_verified)
    
    if source:
        query = query.filter(Food.source == source)
    
    total = query.count()
    
    foods = query.order_by(Food.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Build response with creator name
    result = []
    for food in foods:
        creator_name = None
        if food.created_by:
            creator = db.query(User).filter(User.user_id == food.created_by).first()
            if creator:
                creator_name = creator.full_name or creator.email
        
        result.append({
            "food_id": food.food_id,
            "name_vi": food.name_vi,
            "name_en": food.name_en,
            "category": food.category,
            "cuisine_type": food.cuisine_type,
            "calories_per_100g": float(food.calories_per_100g) if food.calories_per_100g else 0,
            "protein_per_100g": float(food.protein_per_100g) if food.protein_per_100g else 0,
            "carbs_per_100g": float(food.carbs_per_100g) if food.carbs_per_100g else 0,
            "fat_per_100g": float(food.fat_per_100g) if food.fat_per_100g else 0,
            "barcode": food.barcode,
            "image_url": food.image_url,
            "source": food.source,
            "is_verified": food.is_verified,
            "created_by": food.created_by,
            "creator_name": creator_name,
            "created_at": food.created_at
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "foods": result
    }


@router.get("/foods/{food_id}")
def get_food_detail(
    food_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific food (Admin only)"""
    try:
        food_uuid = UUID(food_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid food_id format"
        )
    
    food = db.query(Food).filter(Food.food_id == food_uuid).first()
    
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    creator_name = None
    if food.created_by:
        creator = db.query(User).filter(User.user_id == food.created_by).first()
        if creator:
            creator_name = creator.full_name or creator.email
    
    return {
        "food_id": str(food.food_id),
        "name_vi": food.name_vi,
        "name_en": food.name_en,
        "description": food.description,
        "category": food.category,
        "cuisine_type": food.cuisine_type,
        "calories_per_100g": float(food.calories_per_100g) if food.calories_per_100g else 0,
        "protein_per_100g": float(food.protein_per_100g) if food.protein_per_100g else 0,
        "carbs_per_100g": float(food.carbs_per_100g) if food.carbs_per_100g else 0,
        "fat_per_100g": float(food.fat_per_100g) if food.fat_per_100g else 0,
        "fiber_per_100g": float(food.fiber_per_100g) if food.fiber_per_100g else 0,
        "sugar_per_100g": float(food.sugar_per_100g) if food.sugar_per_100g else 0,
        "sodium_per_100g": float(food.sodium_per_100g) if food.sodium_per_100g else 0,
        "barcode": food.barcode,
        "image_url": food.image_url,
        "source": food.source,
        "is_verified": food.is_verified,
        "created_by": str(food.created_by) if food.created_by else None,
        "creator_name": creator_name,
        "created_at": food.created_at.isoformat() if food.created_at else None,
        "updated_at": food.updated_at.isoformat() if food.updated_at else None
    }


@router.patch("/foods/{food_id}/verify")
def verify_food(
    food_id: str,
    request: FoodVerifyRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verify or unverify a food (Admin only)"""
    try:
        food_uuid = UUID(food_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid food_id format"
        )
    
    food = db.query(Food).filter(Food.food_id == food_uuid).first()
    
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    food.is_verified = request.is_verified
    food.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(food)
    
    return {
        "food_id": str(food.food_id),
        "name_vi": food.name_vi,
        "is_verified": food.is_verified,
        "verified_at": datetime.utcnow().isoformat()
    }


@router.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(
    food_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a food (Admin only)"""
    try:
        food_uuid = UUID(food_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid food_id format"
        )
    
    food = db.query(Food).filter(Food.food_id == food_uuid).first()
    
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    db.delete(food)
    db.commit()
    return None


# ==========================================
# ADMIN ENDPOINTS - RECIPES
# ==========================================

@router.get("/recipes", response_model=RecipeListResponse)
def list_recipes_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    difficulty: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of all recipes (Admin only)"""
    query = db.query(Recipe)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Recipe.name_vi.ilike(search_pattern),
                Recipe.name_en.ilike(search_pattern)
            )
        )
    
    if category:
        query = query.filter(Recipe.category == category)
    
    if is_verified is not None:
        query = query.filter(Recipe.is_verified == is_verified)
    
    if difficulty:
        query = query.filter(Recipe.difficulty_level == difficulty)
    
    total = query.count()
    
    recipes = query.order_by(Recipe.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Build response with creator name
    result = []
    for recipe in recipes:
        creator_name = None
        if recipe.created_by:
            creator = db.query(User).filter(User.user_id == recipe.created_by).first()
            if creator:
                creator_name = creator.full_name or creator.email
        
        result.append({
            "recipe_id": recipe.recipe_id,
            "name_vi": recipe.name_vi,
            "name_en": recipe.name_en,
            "category": recipe.category,
            "cuisine_type": recipe.cuisine_type,
            "prep_time_minutes": recipe.prep_time_minutes,
            "cook_time_minutes": recipe.cook_time_minutes,
            "servings": recipe.servings,
            "difficulty_level": recipe.difficulty_level,
            "calories_per_serving": float(recipe.calories_per_serving) if recipe.calories_per_serving else None,
            "protein_per_serving": float(recipe.protein_per_serving) if recipe.protein_per_serving else None,
            "carbs_per_serving": float(recipe.carbs_per_serving) if recipe.carbs_per_serving else None,
            "fat_per_serving": float(recipe.fat_per_serving) if recipe.fat_per_serving else None,
            "image_url": recipe.image_url,
            "source": recipe.source,
            "is_verified": recipe.is_verified,
            "is_public": recipe.is_public,
            "created_by": recipe.created_by,
            "creator_name": creator_name,
            "view_count": recipe.view_count,
            "favorite_count": recipe.favorite_count,
            "created_at": recipe.created_at
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "recipes": result
    }


@router.get("/recipes/{recipe_id}")
def get_recipe_detail(
    recipe_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific recipe (Admin only)"""
    try:
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipe_id format"
        )
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_uuid).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    creator_name = None
    if recipe.created_by:
        creator = db.query(User).filter(User.user_id == recipe.created_by).first()
        if creator:
            creator_name = creator.full_name or creator.email
    
    # Get ingredients
    ingredients = db.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe_uuid
    ).order_by(RecipeIngredient.order_index).all()
    
    return {
        "recipe_id": str(recipe.recipe_id),
        "name_vi": recipe.name_vi,
        "name_en": recipe.name_en,
        "description": recipe.description,
        "category": recipe.category,
        "cuisine_type": recipe.cuisine_type,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "difficulty_level": recipe.difficulty_level,
        "instructions": recipe.instructions,
        "instructions_steps": recipe.instructions_steps,
        "calories_per_serving": float(recipe.calories_per_serving) if recipe.calories_per_serving else None,
        "protein_per_serving": float(recipe.protein_per_serving) if recipe.protein_per_serving else None,
        "carbs_per_serving": float(recipe.carbs_per_serving) if recipe.carbs_per_serving else None,
        "fat_per_serving": float(recipe.fat_per_serving) if recipe.fat_per_serving else None,
        "fiber_per_serving": float(recipe.fiber_per_serving) if recipe.fiber_per_serving else None,
        "image_url": recipe.image_url,
        "video_url": recipe.video_url,
        "source": recipe.source,
        "is_verified": recipe.is_verified,
        "is_public": recipe.is_public,
        "created_by": str(recipe.created_by) if recipe.created_by else None,
        "creator_name": creator_name,
        "tags": recipe.tags or [],
        "view_count": recipe.view_count,
        "favorite_count": recipe.favorite_count,
        "ingredients": [
            {
                "ingredient_id": str(i.ingredient_id),
                "ingredient_name": i.ingredient_name,
                "quantity": float(i.quantity) if i.quantity else 0,
                "unit": i.unit,
                "notes": i.notes
            }
            for i in ingredients
        ],
        "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
        "updated_at": recipe.updated_at.isoformat() if recipe.updated_at else None
    }


@router.patch("/recipes/{recipe_id}/verify")
def verify_recipe(
    recipe_id: str,
    request: RecipeVerifyRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verify or unverify a recipe (Admin only)"""
    try:
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipe_id format"
        )
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_uuid).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    recipe.is_verified = request.is_verified
    recipe.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(recipe)
    
    return {
        "recipe_id": str(recipe.recipe_id),
        "name_vi": recipe.name_vi,
        "is_verified": recipe.is_verified,
        "verified_at": datetime.utcnow().isoformat()
    }


@router.patch("/recipes/{recipe_id}/visibility")
def toggle_recipe_visibility(
    recipe_id: str,
    is_public: bool,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle recipe visibility (Admin only)"""
    try:
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipe_id format"
        )
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_uuid).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    recipe.is_public = is_public
    recipe.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(recipe)
    
    return {
        "recipe_id": str(recipe.recipe_id),
        "name_vi": recipe.name_vi,
        "is_public": recipe.is_public
    }


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a recipe (Admin only)"""
    try:
        recipe_uuid = UUID(recipe_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipe_id format"
        )
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_uuid).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    db.delete(recipe)
    db.commit()
    return None


# ==========================================
# ADMIN ENDPOINTS - MEAL PLANS
# ==========================================

@router.get("/meal-plans", response_model=MealPlanListResponse)
def list_meal_plans_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by plan name"),
    is_active: Optional[bool] = Query(None),
    user_id: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of all meal plans (Admin only)"""
    query = db.query(MealPlan)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(MealPlan.plan_name.ilike(search_pattern))
    
    if is_active is not None:
        query = query.filter(MealPlan.is_active == is_active)
    
    if user_id:
        try:
            user_uuid = UUID(user_id)
            query = query.filter(MealPlan.user_id == user_uuid)
        except ValueError:
            pass
    
    total = query.count()
    
    meal_plans = query.order_by(MealPlan.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Build response with user info
    result = []
    for plan in meal_plans:
        user = db.query(User).filter(User.user_id == plan.user_id).first()
        user_email = user.email if user else "Unknown"
        user_name = user.full_name if user else None
        
        # Get total meals and calories
        items = db.query(MealPlanItem).filter(MealPlanItem.meal_plan_id == plan.plan_id).all()
        total_meals = len(items)
        total_calories = sum(float(i.calories or 0) for i in items)
        duration = (plan.end_date - plan.start_date).days + 1
        
        result.append({
            "plan_id": plan.plan_id,
            "user_id": plan.user_id,
            "user_email": user_email,
            "user_name": user_name,
            "plan_name": plan.plan_name,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "duration_days": duration,
            "is_active": plan.is_active,
            "is_completed": plan.is_completed,
            "total_meals": total_meals,
            "total_calories": total_calories,
            "created_at": plan.created_at
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "meal_plans": result
    }


@router.get("/meal-plans/{plan_id}")
def get_meal_plan_detail(
    plan_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific meal plan (Admin only)"""
    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan_id format"
        )
    
    plan = db.query(MealPlan).filter(MealPlan.plan_id == plan_uuid).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    user = db.query(User).filter(User.user_id == plan.user_id).first()
    
    # Get all items
    items = db.query(MealPlanItem).filter(
        MealPlanItem.meal_plan_id == plan_uuid
    ).order_by(MealPlanItem.day_date, MealPlanItem.order_index).all()
    
    total_calories = sum(float(i.calories or 0) for i in items)
    duration = (plan.end_date - plan.start_date).days + 1
    
    return {
        "plan_id": str(plan.plan_id),
        "user_id": str(plan.user_id),
        "user_email": user.email if user else "Unknown",
        "user_name": user.full_name if user else None,
        "plan_name": plan.plan_name,
        "start_date": str(plan.start_date),
        "end_date": str(plan.end_date),
        "duration_days": duration,
        "prep_time_minutes": plan.prep_time_minutes,
        "cook_time_minutes": plan.cook_time_minutes,
        "servings": plan.servings,
        "difficulty_level": plan.difficulty_level,
        "preferences": plan.preferences,
        "is_active": plan.is_active,
        "is_completed": plan.is_completed,
        "total_meals": len(items),
        "total_calories": total_calories,
        "items": [
            {
                "item_id": str(i.item_id),
                "day_date": str(i.day_date),
                "meal_type": i.meal_type,
                "serving_size_g": float(i.serving_size_g) if i.serving_size_g else 0,
                "quantity": float(i.quantity) if i.quantity else 1,
                "unit": i.unit,
                "calories": float(i.calories) if i.calories else None,
                "protein_g": float(i.protein_g) if i.protein_g else None,
                "carbs_g": float(i.carbs_g) if i.carbs_g else None,
                "fat_g": float(i.fat_g) if i.fat_g else None,
                "notes": i.notes
            }
            for i in items
        ],
        "created_at": plan.created_at.isoformat() if plan.created_at else None
    }


@router.delete("/meal-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_plan(
    plan_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a meal plan (Admin only)"""
    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan_id format"
        )
    
    plan = db.query(MealPlan).filter(MealPlan.plan_id == plan_uuid).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    
    db.delete(plan)
    db.commit()
    return None


# ==========================================
# ADMIN ENDPOINTS - STATS & ANALYTICS
# ==========================================

@router.get("/stats", response_model=UserStats)
def get_admin_stats(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    
    new_today = db.query(User)\
        .filter(User.created_at >= datetime.combine(today, datetime.min.time()))\
        .count()
    
    new_week = db.query(User)\
        .filter(User.created_at >= datetime.combine(week_ago, datetime.min.time()))\
        .count()
    
    new_month = db.query(User)\
        .filter(User.created_at >= datetime.combine(month_ago, datetime.min.time()))\
        .count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "verified_users": verified_users,
        "new_users_today": new_today,
        "new_users_this_week": new_week,
        "new_users_this_month": new_month
    }


@router.get("/analytics/overview", response_model=SystemStats)
def get_system_stats(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive system statistics for admin dashboard"""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    inactive_users = db.query(User).filter(User.is_active == False).count()
    
    new_today = db.query(User)\
        .filter(User.created_at >= datetime.combine(today, datetime.min.time()))\
        .count()
    new_week = db.query(User)\
        .filter(User.created_at >= datetime.combine(week_ago, datetime.min.time()))\
        .count()
    new_month = db.query(User)\
        .filter(User.created_at >= datetime.combine(month_ago, datetime.min.time()))\
        .count()
    
    # Food stats
    total_foods = db.query(Food).count()
    verified_foods = db.query(Food).filter(Food.is_verified == True).count()
    unverified_foods = total_foods - verified_foods
    
    # Recipe stats
    total_recipes = db.query(Recipe).count()
    verified_recipes = db.query(Recipe).filter(Recipe.is_verified == True).count()
    unverified_recipes = total_recipes - verified_recipes
    
    # Meal plan stats
    total_meal_plans = db.query(MealPlan).count()
    active_meal_plans = db.query(MealPlan).filter(MealPlan.is_active == True).count()
    
    # Engagement stats
    total_food_logs = db.query(FoodLog).count()
    logs_this_week = db.query(FoodLog)\
        .filter(FoodLog.created_at >= datetime.combine(week_ago, datetime.min.time()))\
        .count()
    logs_this_month = db.query(FoodLog)\
        .filter(FoodLog.created_at >= datetime.combine(month_ago, datetime.min.time()))\
        .count()
    
    return {
        # User stats
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "verified_users": verified_users,
        "inactive_users": inactive_users,
        "new_users_today": new_today,
        "new_users_this_week": new_week,
        "new_users_this_month": new_month,
        # Content stats
        "total_foods": total_foods,
        "verified_foods": verified_foods,
        "unverified_foods": unverified_foods,
        "total_recipes": total_recipes,
        "verified_recipes": verified_recipes,
        "unverified_recipes": unverified_recipes,
        "total_meal_plans": total_meal_plans,
        "active_meal_plans": active_meal_plans,
        # Engagement stats
        "total_food_logs": total_food_logs,
        "logs_this_week": logs_this_week,
        "logs_this_month": logs_this_month
    }