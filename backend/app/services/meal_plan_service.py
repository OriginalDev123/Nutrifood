"""
Meal Plan Service - CRUD Operations
Handles database operations for meal plans and items
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta

from app.models.meal_plan import MealPlan, MealPlanItem
from app.models.food import Food
from app.models.recipe import Recipe
from app.schemas.meal_plan import MealPlanCreate, MealPlanItemCreate


# ==========================================
# DECIMAL HELPERS
# ==========================================

DECIMAL_0 = Decimal("0")
DECIMAL_100 = Decimal("100")


def round_2(value: Decimal) -> Decimal:
    """
    Round Decimal to 2 decimal places
    
    Args:
        value: Decimal value to round
    
    Returns:
        Rounded Decimal value
    """
    if value is None:
        return DECIMAL_0
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==========================================
# MEAL PLAN CRUD
# ==========================================

def create_meal_plan(
    db: Session,
    user_id: UUID,
    plan_data: MealPlanCreate
) -> MealPlan:
    """
    Create new meal plan
    
    Validates date range and creates empty meal plan.
    Items should be added separately via add_meal_plan_item().
    
    Args:
        db: Database session
        user_id: User UUID
        plan_data: Meal plan creation data
    
    Returns:
        Created MealPlan object
    
    Raises:
        ValueError: If date validation fails
        IntegrityError: If database constraint violated
    """
    
    # Validate date range
    if plan_data.end_date < plan_data.start_date:
        raise ValueError("End date must be after or equal to start date")
    
    # Calculate duration
    duration = (plan_data.end_date - plan_data.start_date).days + 1
    
    if duration > 90:
        raise ValueError("Meal plan cannot exceed 90 days")
    
    try:
        # Create meal plan
        meal_plan = MealPlan(
            user_id=user_id,
            plan_name=plan_data.plan_name,
            start_date=plan_data.start_date,
            end_date=plan_data.end_date,
            prep_time_minutes=plan_data.prep_time_minutes,
            cook_time_minutes=plan_data.cook_time_minutes,
            servings=plan_data.servings,
            difficulty_level=plan_data.difficulty_level,
            preferences=plan_data.preferences or {},
            is_active=True,
            is_completed=False
        )
        
        db.add(meal_plan)
        db.commit()
        db.refresh(meal_plan)
        
        return meal_plan
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database error: {str(e)}")


def add_meal_plan_item(
    db: Session,
    user_id: UUID,
    plan_id: UUID,
    item_data: MealPlanItemCreate
) -> MealPlanItem:
    """
    Add meal item to plan with snapshot nutrition
    
    SNAPSHOT PATTERN: Nutrition values are calculated and stored at creation time.
    This prevents historical data changes if food/recipe database is updated later.
    
    Supports both Food-based and Recipe-based items:
    - If food_id is provided: Calculate from Food nutrition per 100g
    - If notes contains "Recipe: {name}": Extract from Recipe nutrition per serving
    
    Args:
        db: Database session
        user_id: User UUID (for authorization check)
        plan_id: Meal plan UUID
        item_data: Meal plan item creation data
    
    Returns:
        Created MealPlanItem with snapshot nutrition
    
    Raises:
        ValueError: If plan not found, not owned by user, or food/recipe not found
    """
    
    # 1. Verify meal plan exists and belongs to user
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found or access denied")
    
    # 2. Validate date is within plan range
    if item_data.day_date < meal_plan.start_date or item_data.day_date > meal_plan.end_date:
        raise ValueError(
            f"Date must be between {meal_plan.start_date} and {meal_plan.end_date}"
        )
    
    # 3. Calculate snapshot nutrition
    calories = DECIMAL_0
    protein_g = DECIMAL_0
    carbs_g = DECIMAL_0
    fat_g = DECIMAL_0
    
    if item_data.food_id:
        # Food-based item: Calculate from Food nutrition per 100g
        food = db.query(Food).filter(Food.food_id == item_data.food_id).first()
        
        if not food:
            raise ValueError(f"Food with id {item_data.food_id} not found")
        
        # Convert inputs to Decimal
        serving_size_g = Decimal(str(item_data.serving_size_g))
        quantity = Decimal(str(item_data.quantity))
        
        # Calculate nutrition: (nutrition_per_100g / 100) * serving_size_g * quantity
        ratio = (serving_size_g * quantity) / DECIMAL_100
        
        calories = round_2(Decimal(str(food.calories_per_100g)) * ratio)
        protein_g = round_2(Decimal(str(food.protein_per_100g or 0)) * ratio)
        carbs_g = round_2(Decimal(str(food.carbs_per_100g or 0)) * ratio)
        fat_g = round_2(Decimal(str(food.fat_per_100g or 0)) * ratio)
        
    else:
        # Recipe-based item (if notes contains recipe reference)
        # For generated meal plans, nutrition should be pre-calculated
        # For manual items without food_id, nutrition must be provided
        if item_data.calories:
            calories = round_2(Decimal(str(item_data.calories)))
        if item_data.protein_g:
            protein_g = round_2(Decimal(str(item_data.protein_g)))
        if item_data.carbs_g:
            carbs_g = round_2(Decimal(str(item_data.carbs_g)))
        if item_data.fat_g:
            fat_g = round_2(Decimal(str(item_data.fat_g)))
    
    # 4. Create meal plan item with snapshot
    try:
        item = MealPlanItem(
            meal_plan_id=plan_id,
            food_id=item_data.food_id,
            day_date=item_data.day_date,
            meal_type=item_data.meal_type,
            serving_size_g=Decimal(str(item_data.serving_size_g)),
            quantity=Decimal(str(item_data.quantity)),
            unit=item_data.unit,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            order_index=item_data.order_index if hasattr(item_data, 'order_index') else 0,
            notes=item_data.notes
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return item
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database error: {str(e)}")


def get_user_meal_plans(
    db: Session,
    user_id: UUID,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[MealPlan]:
    """
    Get user's meal plans with soft delete filtering
    
    Args:
        db: Database session
        user_id: User UUID
        active_only: If True, only return active plans (is_active=True)
        skip: Pagination offset
        limit: Maximum number of results
    
    Returns:
        List of MealPlan objects (excluding soft-deleted)
    """
    
    query = db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False  # Soft delete filter
    )
    
    if active_only:
        query = query.filter(MealPlan.is_active == True)
    
    # Order by most recent first
    query = query.order_by(MealPlan.created_at.desc())
    
    return query.offset(skip).limit(limit).all()


def get_meal_plan_with_items(
    db: Session,
    user_id: UUID,
    plan_id: UUID
) -> Optional[MealPlan]:
    """
    Get meal plan with all items (eager loading)
    
    Uses joinedload to fetch items in single query for performance.
    
    Args:
        db: Database session
        user_id: User UUID (for authorization)
        plan_id: Meal plan UUID
    
    Returns:
        MealPlan with items relationship loaded, or None if not found
    """
    
    from sqlalchemy.orm import joinedload
    
    meal_plan = db.query(MealPlan).options(
        joinedload(MealPlan.items)
    ).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    return meal_plan


def delete_meal_plan(
    db: Session,
    user_id: UUID,
    plan_id: UUID,
    soft_delete: bool = True
) -> bool:
    """
    Delete meal plan (soft or hard delete)
    
    SOFT DELETE (default): Sets is_deleted=True, deleted_at=now
    HARD DELETE: Permanently removes from database (CASCADE deletes items)
    
    Args:
        db: Database session
        user_id: User UUID (for authorization)
        plan_id: Meal plan UUID
        soft_delete: If True, perform soft delete (default)
    
    Returns:
        True if deleted successfully, False if not found
    
    Raises:
        ValueError: If authorization fails
    """
    
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        return False
    
    try:
        if soft_delete:
            #  Sử dụng phương thức từ Mixin để đảm bảo tính nhất quán
            meal_plan.soft_delete() 
            # Vô hiệu hóa kế hoạch ngay cả khi chỉ xóa mềm
            meal_plan.is_active = False
        else:
            # Hard delete: Remove from database
            # CASCADE will automatically delete all MealPlanItem records
            db.delete(meal_plan)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Delete failed: {str(e)}")


def update_meal_plan(
    db: Session,
    user_id: UUID,
    plan_id: UUID,
    update_data: dict
) -> MealPlan:
    """
    Update meal plan fields
    
    Args:
        db: Database session
        user_id: User UUID (for authorization)
        plan_id: Meal plan UUID
        update_data: Dictionary of fields to update
    
    Returns:
        Updated MealPlan object
    
    Raises:
        ValueError: If plan not found or validation fails
    """
    
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found or access denied")
    
    # Validate date range if dates are being updated
    start_date = update_data.get('start_date', meal_plan.start_date)
    end_date = update_data.get('end_date', meal_plan.end_date)
    
    if end_date < start_date:
        raise ValueError("End date must be after or equal to start date")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(meal_plan, field) and field not in ['plan_id', 'user_id', 'created_at']:
            setattr(meal_plan, field, value)
    
    try:
        db.commit()
        db.refresh(meal_plan)
        return meal_plan
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Update failed: {str(e)}")


def delete_meal_plan_item(
    db: Session,
    user_id: UUID,
    item_id: UUID
) -> bool:
    """
    Delete a meal plan item
    
    Args:
        db: Database session
        user_id: User UUID (for authorization via meal plan)
        item_id: Meal plan item UUID
    
    Returns:
        True if deleted, False if not found
    """
    
    # Verify ownership via meal plan
    item = db.query(MealPlanItem).join(MealPlan).filter(
        MealPlanItem.item_id == item_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not item:
        return False
    
    try:
        db.delete(item)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Delete failed: {str(e)}")


def mark_plan_completed(
    db: Session,
    user_id: UUID,
    plan_id: UUID
) -> MealPlan:
    """
    Mark meal plan as completed
    
    Args:
        db: Database session
        user_id: User UUID
        plan_id: Meal plan UUID
    
    Returns:
        Updated MealPlan
    """
    
    meal_plan = db.query(MealPlan).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found")
    
    meal_plan.is_completed = True
    meal_plan.is_active = False
    
    db.commit()
    db.refresh(meal_plan)
    
    return meal_plan


def apply_meal_plan_to_logs(
    db: Session,
    user_id: UUID,
    plan_id: UUID,
    start_date: date
) -> dict:
    """
    Apply meal plan items to user's food logs
    
    Creates FoodLog entries directly (not via log_meal service) to preserve
    snapshot nutrition data and handle Recipe-based items (food_id = null).
    
    Args:
        db: Database session
        user_id: User UUID (for authorization)
        plan_id: Meal plan UUID
        start_date: Date to start applying (in food log)
    
    Returns:
        Dict with success status, counts, and date range
    
    Raises:
        ValueError: If plan not found, not owned by user, or validation fails
    """
    from app.models.food_log import FoodLog
    
    # 1. Lấy meal plan với items (eager load để tránh N+1)
    meal_plan = db.query(MealPlan).options(
        joinedload(MealPlan.items)
    ).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == user_id,
        MealPlan.is_deleted == False
    ).first()
    
    if not meal_plan:
        raise ValueError("Meal plan not found or access denied")
    
    # 2. Validate start_date
    if start_date < date.today():
        raise ValueError("Start date cannot be in the past")
    
    # 3. Tính offset ngày giữa start_date và plan.start_date
    plan_start = meal_plan.start_date or date.today()
    offset_days = (start_date - plan_start).days
    
    # 4. Xử lý từng item
    items = list(meal_plan.items) if meal_plan.items else []
    applied_count = 0
    skipped_count = 0
    
    for item in items:
        try:
            # Tính ngày mới cho food log
            item_date = item.day_date + timedelta(days=offset_days) if offset_days != 0 else item.day_date
            
            # Extract food_name - quan trọng để tránh lỗi NOT NULL constraint
            food_name = None
            
            # Ưu tiên 1: Extract từ notes
            if item.notes:
                if item.notes.startswith("Recipe: "):
                    food_name = item.notes.replace("Recipe: ", "")
                elif item.notes.startswith("Custom: "):
                    custom_part = item.notes.replace("Custom: ", "")
                    pipe_index = custom_part.find(" | ")
                    food_name = custom_part[:pipe_index] if pipe_index > 0 else custom_part
            
            # Ưu tiên 2: Query từ food table nếu có food_id
            if not food_name and item.food_id:
                food = db.query(Food).filter(Food.food_id == item.food_id).first()
                if food:
                    food_name = food.name_vi
            
            # Fallback: tạo tên mặc định (đảm bảo NOT NULL constraint)
            if not food_name:
                food_name = "Món ăn từ kế hoạch"
            
            # Tạo FoodLog entry với snapshot data từ MealPlanItem
            food_log = FoodLog(
                user_id=user_id,
                food_id=item.food_id,
                serving_id=None,
                food_name=food_name,
                serving_size_g=item.serving_size_g if item.serving_size_g else Decimal("100"),
                quantity=item.quantity if item.quantity else Decimal("1"),
                calories=item.calories if item.calories else Decimal("0"),
                protein_g=item.protein_g if item.protein_g else Decimal("0"),
                carbs_g=item.carbs_g if item.carbs_g else Decimal("0"),
                fat_g=item.fat_g if item.fat_g else Decimal("0"),
                meal_type=item.meal_type,
                meal_date=item_date,
                meal_time=None,
                was_ai_recognized=False,
                notes=f"Áp dụng từ kế hoạch: {meal_plan.plan_name}"
            )
            
            db.add(food_log)
            applied_count += 1
            
        except Exception:
            skipped_count += 1
            continue
    
    # 5. Commit tất cả trong một transaction
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to apply meal plan: {str(e)}")
    
    # 6. Tính date range cho response
    if items:
        dates = [item.day_date for item in items if item.day_date]
        if dates:
            first_date = min(dates) + timedelta(days=offset_days)
            last_date = max(dates) + timedelta(days=offset_days)
        else:
            first_date = start_date
            last_date = start_date
    else:
        first_date = start_date
        last_date = start_date
    
    return {
        "success": True,
        "applied_items": applied_count,
        "skipped_items": skipped_count,
        "date_range": {
            "start": first_date.strftime("%Y-%m-%d"),
            "end": last_date.strftime("%Y-%m-%d")
        },
        "message": f"Đã áp dụng kế hoạch '{meal_plan.plan_name}' vào Nhật ký ăn"
    }