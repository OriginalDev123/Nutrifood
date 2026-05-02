"""
Food Logging Routes
Endpoints for logging meals and tracking weight
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from uuid import UUID
import math

from app.schemas.base import PaginatedResponse
from app.database import get_db
from app.models.user import User
from app.schemas import food_log as schemas
from app.services import food_log_service as service
from app.utils.dependencies import get_current_active_user


router = APIRouter(
    prefix="/food-logs",
    tags=["Food & Weight Logging"]
)


# ==========================================
# FOOD LOGGING ENDPOINTS
# ==========================================

@router.post("/", response_model=schemas.FoodLogResponse, status_code=status.HTTP_201_CREATED)
def log_food(
    log_data: schemas.FoodLogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Log a meal (Snapshot-based)

    - Nutrition values are calculated at log time
    - Uses Decimal-safe service logic
    - If serving_id not provided, uses serving_size_g or default serving
    """
    try:
        # Determine serving_id if not provided
        serving_id = log_data.serving_id
        serving_size_g = log_data.serving_size_g
        
        if not serving_id:
            # If no serving_id, try to find or create one
            from app.models.food import FoodServing
            
            if serving_size_g:
                # Find serving with matching size, or use closest one
                servings = db.query(FoodServing).filter(
                    FoodServing.food_id == log_data.food_id
                ).all()
                
                if servings:
                    # Find exact match or closest
                    exact_match = next((s for s in servings if abs(float(s.serving_size_g) - float(serving_size_g)) < 0.1), None)
                    if exact_match:
                        serving_id = exact_match.serving_id
                    else:
                        # Use first serving and adjust quantity proportionally
                        first_serving = servings[0]
                        serving_id = first_serving.serving_id
                        log_data.quantity = log_data.quantity * (serving_size_g / first_serving.serving_size_g)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No servings found for food {log_data.food_id}"
                    )
            else:
                # Use default serving (usually 100g or first available)
                from app.models.food import FoodServing
                default_serving = db.query(FoodServing).filter(
                    FoodServing.food_id == log_data.food_id
                ).first()
                
                if not default_serving:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No servings found for food {log_data.food_id}"
                    )
                serving_id = default_serving.serving_id
        
        food_log = service.log_meal(
            db=db,
            user_id=current_user.user_id,
            food_id=log_data.food_id,
            serving_id=serving_id,
            meal_type=log_data.meal_type,
            meal_date=log_data.meal_date,
            quantity=log_data.quantity,
            meal_time=log_data.meal_time,
            notes=log_data.notes,
            image_url=log_data.image_url
        )
        return food_log

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/summary", response_model=schemas.DailySummaryResponse)
def get_daily_summary(
    meal_date: date = Query(..., description="Date to get summary for (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get daily nutrition summary (Decimal-safe)

    - No JOINs
    - Uses snapshot data from FOOD_LOG
    """
    summary = service.get_daily_summary(
        db=db,
        user_id=current_user.user_id,
        target_date=meal_date
    )
    return summary


@router.get("/", response_model=List[schemas.FoodLogResponse])
def get_food_logs_by_date(
    meal_date: date = Query(..., description="Date to get logs for (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all food logs for a specific date
    """
    return service.get_food_logs_by_date(
        db=db,
        user_id=current_user.user_id,
        target_date=meal_date
    )


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_log(
    log_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a food log entry

    Security: user can only delete their own logs
    """
    deleted = service.delete_food_log(
        db=db,
        log_id=log_id,
        user_id=current_user.user_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food log not found"
        )

    return None


# ==========================================
# UPDATE FOOD LOG ENDPOINTS
# ==========================================

@router.put("/{log_id}", response_model=schemas.FoodLogResponse)
def update_food_log(
    log_id: UUID,
    log_update: schemas.FoodLogUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Full update a food log entry
    
    - Updates all fields provided
    - Recalculates nutrition values if quantity changes
    - User can only update their own logs
    """
    from app.models.food_log import FoodLog
    
    # Find the food log
    food_log = db.query(FoodLog).filter(
        FoodLog.log_id == log_id,
        FoodLog.user_id == current_user.user_id,
        FoodLog.is_deleted == False
    ).first()
    
    if not food_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food log not found"
        )
    
    # Update fields
    update_data = log_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(food_log, field, value)
    
    # If quantity changed, recalculate nutrition
    if 'quantity' in update_data:
        from app.services.nutrition_calculator import NutritionCalculatorCore
        calc = NutritionCalculatorCore()
        nutrition = calc.calculate_from_serving(
            food_id=food_log.food_id,
            serving_id=food_log.serving_id,
            quantity=food_log.quantity
        )
        food_log.calories = nutrition.calories
        food_log.protein_g = nutrition.protein
        food_log.carbs_g = nutrition.carbs
        food_log.fat_g = nutrition.fat
    
    db.commit()
    db.refresh(food_log)
    
    return food_log


@router.patch("/{log_id}", response_model=schemas.FoodLogResponse)
def partial_update_food_log(
    log_id: UUID,
    log_update: schemas.FoodLogUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Partial update a food log entry
    
    - Only updates provided fields
    - Recalculates nutrition if quantity changes
    - User can only update their own logs
    """
    from app.models.food_log import FoodLog
    
    # Find the food log
    food_log = db.query(FoodLog).filter(
        FoodLog.log_id == log_id,
        FoodLog.user_id == current_user.user_id,
        FoodLog.is_deleted == False
    ).first()
    
    if not food_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food log not found"
        )
    
    # Update only provided fields (exclude_unset=True makes this partial)
    update_data = log_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(food_log, field, value)
    
    # If quantity changed, recalculate nutrition
    if 'quantity' in update_data:
        from app.services.nutrition_calculator import NutritionCalculatorCore
        calc = NutritionCalculatorCore()
        nutrition = calc.calculate_from_serving(
            food_id=food_log.food_id,
            serving_id=food_log.serving_id,
            quantity=food_log.quantity
        )
        food_log.calories = nutrition.calories
        food_log.protein_g = nutrition.protein
        food_log.carbs_g = nutrition.carbs
        food_log.fat_g = nutrition.fat
    
    db.commit()
    db.refresh(food_log)
    
    return food_log


# ==========================================
# FOOD LOG HISTORY
# ==========================================

@router.get("/history")
def get_food_log_history(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get food log history for date range (weekly/monthly)
    
    - Returns all logs within date range
    - Can filter by meal type
    - Useful for weekly/monthly reports
    """
    from app.models.food_log import FoodLog
    
    query = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.user_id,
        FoodLog.meal_date >= start_date,
        FoodLog.meal_date <= end_date,
        FoodLog.is_deleted == False
    )
    
    if meal_type:
        query = query.filter(FoodLog.meal_type == meal_type)
    
    logs = query.order_by(FoodLog.meal_date.desc(), FoodLog.meal_time.desc()).all()
    
    # Group by date
    logs_by_date = {}
    for log in logs:
        date_str = log.meal_date.strftime('%Y-%m-%d')
        if date_str not in logs_by_date:
            logs_by_date[date_str] = []
        logs_by_date[date_str].append(log)
    
    return {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "total_logs": len(logs),
        "logs_by_date": logs_by_date
    }


# ==========================================
# WEIGHT LOGGING ENDPOINTS
# ==========================================

@router.post("/weight", response_model=schemas.WeightLogResponse, status_code=status.HTTP_201_CREATED)
def log_weight(
    weight_data: schemas.WeightLogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Log user weight

    - One entry per day
    - Existing entry will be updated
    """
    try:
        return service.log_weight(
            db=db,
            user_id=current_user.user_id,
            weight_kg=weight_data.weight_kg,
            measured_date=weight_data.measured_date,
            notes=weight_data.notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/weight", response_model=PaginatedResponse[schemas.WeightLogResponse])
def get_weight_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lấy lịch sử cân nặng với đầy đủ Metadata phân trang
    """
    # 1. Gọi hàm service trả về tuple (items, total_count)
    items, total = service.get_weight_history_paginated(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )

    # 2. Tính toán metadata cho Frontend
    current_page = (skip // limit) + 1
    total_pages = math.ceil(total / limit) if total > 0 else 0

    # 3. Trả về đúng format của PaginatedResponse
    return {
        "items": items,
        "total": total,
        "page": current_page,
        "page_size": limit,
        "pages": total_pages
    }


@router.get("/weight/latest", response_model=schemas.WeightLogResponse)
def get_latest_weight(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get latest weight entry
    """
    latest = service.get_latest_weight(
        db=db,
        user_id=current_user.user_id
    )

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weight logs found"
        )

    return latest
