"""
Meal Planning Routes V2
Complete meal planning with AI-like generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.meal_plan import MealPlan
from app.schemas import meal_plan as schemas

# Re-export for convenience
MealPlanWithItems = schemas.MealPlanWithItems
MealPlanWithDays = schemas.MealPlanWithDays

from app.services import (
    get_user_meal_plans,
    get_meal_plan_with_items,
    delete_meal_plan,
    create_meal_plan,
    add_meal_plan_item,
    generate_shopping_list,
    analyze_meal_plan,
    regenerate_day
)
from app.services.meal_plan_generator import generate_meal_plan as generate_meal_plan_service
from app.utils.dependencies import get_current_active_user


router = APIRouter(
    prefix="/meal-plans",
    tags=["Meal Planning"]
)


# ==========================================
# GENERATE MEAL PLAN (NEW)
# ==========================================

@router.post("/generate", response_model=schemas.MealPlanWithDays, status_code=status.HTTP_201_CREATED)
def generate_meal_plan(
    plan_name: str = Query(..., min_length=1, max_length=255),
    days: int = Query(7, ge=1, le=30),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    tags: Optional[str] = Query(None, description="Comma-separated tags (e.g., vegetarian,low-carb)"),
    max_cook_time: Optional[int] = Query(None, ge=0, description="Maximum cooking time in minutes"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate intelligent meal plan from recipes
    
    **Algorithm:**
    1. Gets user's active goal (calorie target)
    2. Calculates calories per meal type (breakfast 25%, lunch 35%, dinner 30%, snack 10%)
    3. Finds recipes matching preferences & calorie range
    4. Distributes recipes across days
    5. Balances macros based on goal type
    6. Avoids repetition
    
    **Query Parameters:**
    - plan_name: Name for the meal plan (required)
    - days: Number of days (1-30, default: 7)
    - categories: Filter recipes by categories (comma-separated)
    - tags: Filter by tags like "vegetarian,low-carb"
    - max_cook_time: Maximum total cooking time per recipe
    
    **Requires:**
    - Active goal with calorie target
    - At least 10-20 recipes in database
    
    **Returns:**
    - Complete meal plan with items for each day
    
    **Example:**
    ```
    POST /meal-plans/generate?plan_name=My Week&days=7&tags=healthy,quick&max_cook_time=45
    ```
    """
    
    try:
        preferences = {}
        if categories:
            preferences["categories"] = [c.strip() for c in categories.split(",")]
        if tags:
            preferences["tags"] = [t.strip() for t in tags.split(",")]
        if max_cook_time:
            preferences["max_cook_time"] = max_cook_time

        plan = generate_meal_plan_service(
            db=db,
            user_id=current_user.user_id,
            plan_name=plan_name,
            days=days,
            preferences=preferences if preferences else None
        )
        # Convert to days format for frontend
        return schemas.MealPlanWithDays.from_meal_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# SHOPPING LIST & ANALYSIS
# ==========================================

@router.get("/{plan_id}/shopping-list")
def api_get_shopping_list(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    plan = get_meal_plan_with_items(db, current_user.user_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
        
    shopping_data = generate_shopping_list(db, plan_id)
    return {
        "plan_name": plan.plan_name,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "shopping_list": shopping_data
    }

@router.get("/{plan_id}/analysis")
def api_analyze_meal_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        return analyze_meal_plan(db, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{plan_id}/regenerate-day", response_model=List[schemas.MealPlanItemResponse])
def api_regenerate_day(
    plan_id: UUID,
    target_date: date = Query(..., description="Date to regenerate (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        return regenerate_day(db, plan_id, target_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# CRUD OPERATIONS
# ==========================================

@router.get("", response_model=List[schemas.MealPlanResponse])
def api_get_my_plans(
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return get_user_meal_plans(db, current_user.user_id, active_only)

@router.get("/{plan_id}", response_model=schemas.MealPlanWithDays)
def api_get_plan_detail(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    plan = get_meal_plan_with_items(db, current_user.user_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return schemas.MealPlanWithDays.from_meal_plan(plan)

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success = delete_meal_plan(db, current_user.user_id, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return None


@router.patch("/{plan_id}", response_model=schemas.MealPlanResponse)
def api_update_plan(
    plan_id: UUID,
    plan_update: schemas.MealPlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update meal plan (partial update)
    
    - Can update plan_name, status
    - Plan must belong to current user
    """
    from app.models.meal_plan import MealPlan
    
    plan = db.query(MealPlan).filter(
        MealPlan.plan_id == plan_id,
        MealPlan.user_id == current_user.user_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Update only provided fields
    update_data = plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan



"""
    Dưới đây là sơ đồ cách các Route này bao quát toàn bộ logic của bạn:
    POST /generate: Gộp logic của create_meal_plan (Service) + generate_meal_plan (Generator) + _find_matching_recipe + _calculate_quantity. Chỉ cần 1 nút bấm, toàn bộ máy móc bên dưới sẽ chạy.
    GET /{plan_id}/shopping-list: Gọi hàm generate_shopping_list.
    GET /{plan_id}/analysis: Gọi hàm analyze_meal_plan.
    POST /{plan_id}/regenerate-day: Gọi hàm regenerate_day.
    GET / (Lấy danh sách): Gọi hàm get_user_meal_plans.
    GET /{plan_id} (Chi tiết): Gọi hàm get_meal_plan_with_items.
    DELETE /{plan_id}: Gọi hàm delete_meal_plan.
"""

"""
    Các hàm như add_meal_plan_item hay update_meal_plan vẫn tồn tại trong Service nhưng tôi không đưa ra Route vì:
    Tính tự động hóa: Khi bạn dùng AI Generate, các món ăn đã tự động được thêm vào rồi.
    Tính gọn nhẹ: Nếu người dùng muốn sửa, họ thường dùng tính năng "Regenerate Day" thay vì sửa thủ công từng món (vốn rất phức tạp cho người dùng).
    Hàm nội bộ: Các hàm bắt đầu bằng dấu gạch dưới (_) là hàm hỗ trợ, không được phép gọi trực tiếp từ bên ngoài để đảm bảo bảo mật.
"""