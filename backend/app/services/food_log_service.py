"""
Food Logging Service

Business logic for food logging operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List
from uuid import UUID

from app.models.food_log import FoodLog, WeightLog
from app.models.food import Food, FoodServing
from app.models.user import User


# ==========================================
# DECIMAL HELPERS
# ==========================================

DECIMAL_0 = Decimal("0")
DECIMAL_100 = Decimal("100")


def round_2(value: Decimal) -> Decimal:
    """Round Decimal to 2 decimal places"""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ==========================================
# FOOD LOGGING FUNCTIONS
# ==========================================

def log_meal(
    db: Session,
    user_id: UUID,
    food_id: UUID,
    serving_id: UUID,
    meal_type: str,
    meal_date: date,
    quantity: Decimal = Decimal("1.0"),
    meal_time: Optional[time] = None,
    notes: Optional[str] = None,
    image_url: Optional[str] = None,
    was_ai_recognized: bool = False,
    ai_confidence: Optional[Decimal] = None
) -> FoodLog:
    """
    Log a meal with snapshot nutrition data (Decimal-safe)
    """

    # 1. Fetch food
    food = db.query(Food).filter(Food.food_id == food_id).first()
    if not food:
        raise ValueError(f"Food with id {food_id} not found")

    # 2. Fetch serving
    serving = db.query(FoodServing).filter(
        FoodServing.serving_id == serving_id
    ).first()
    if not serving:
        raise ValueError(f"Serving with id {serving_id} not found")

    # 3. Normalize Decimal
    quantity = Decimal(quantity)
    if quantity <= 0:
        raise ValueError("Số lượng (quantity) phải lớn hơn 0.")
    
    serving_size_g = Decimal(serving.serving_size_g)
    if serving_size_g <= 0:
        raise ValueError("Kích thước phần ăn (serving size) không hợp lệ.")

    # 4. Snapshot calculation
    # value = (nutrition_per_100g / 100) * serving_size_g * quantity
    ratio = serving_size_g * quantity / DECIMAL_100

    calories = round_2(Decimal(food.calories_per_100g) * ratio)
    protein_g = round_2(Decimal(food.protein_per_100g or 0) * ratio)
    carbs_g   = round_2(Decimal(food.carbs_per_100g or 0) * ratio)
    fat_g     = round_2(Decimal(food.fat_per_100g or 0) * ratio)
    
    # # Validate giá trị AI confidence nếu có
    # if ai_confidence is not None:
    #     ai_val = Decimal(ai_confidence)
    #     if not (0 <= ai_val <= 1):
    #         raise ValueError("Độ tin cậy AI phải nằm trong khoảng từ 0 đến 1.")

    # 5. Create FOOD_LOG snapshot
    
    try:
        food_log = FoodLog(
            user_id=user_id,
            food_id=food_id,
            food_name=food.name_vi,
            serving_size_g=serving_size_g,
            serving_id=serving_id,
            quantity=quantity,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            meal_type=meal_type,
            meal_date=meal_date,
            meal_time=meal_time.time() if meal_time else None,
            notes=notes,
            image_url=image_url,
            was_ai_recognized=was_ai_recognized,
            ai_confidence=round_2(ai_confidence) if ai_confidence is not None else None
        )

        db.add(food_log)
        db.commit() 
        db.refresh(food_log)
        return food_log

    except Exception as e:
        db.rollback()
        raise ValueError(f"Không thể lưu nhật ký món ăn: {str(e)}")


def get_daily_summary(
    db: Session,
    user_id: UUID,
    target_date: date
) -> Dict:
    """
    Get daily nutrition summary (Decimal-safe, no NULL)
    """

    summary = db.query(
        func.sum(FoodLog.calories),
        func.sum(FoodLog.protein_g),
        func.sum(FoodLog.carbs_g),
        func.sum(FoodLog.fat_g),
        func.count(FoodLog.log_id)
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date == target_date,
        FoodLog.is_deleted == False
    ).first()

    total_calories = Decimal(summary[0] or DECIMAL_0)
    total_protein  = Decimal(summary[1] or DECIMAL_0)
    total_carbs    = Decimal(summary[2] or DECIMAL_0)
    total_fat      = Decimal(summary[3] or DECIMAL_0)
    meal_count     = summary[4] or 0

    meals_by_type = db.query(
        FoodLog.meal_type,
        func.sum(FoodLog.calories)
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date == target_date,
        FoodLog.is_deleted == False
    ).group_by(FoodLog.meal_type).all()

    meals_breakdown = {
        meal_type: Decimal(calories or DECIMAL_0)
        for meal_type, calories in meals_by_type
    }

    return {
        "date": target_date,
        "total_calories": round_2(total_calories),
        "total_protein_g": round_2(total_protein),
        "total_carbs_g": round_2(total_carbs),
        "total_fat_g": round_2(total_fat),
        "meal_count": meal_count,
        "meals_breakdown": meals_breakdown
    }


def get_food_logs_by_date(
    db: Session,
    user_id: UUID,
    target_date: date
) -> List[FoodLog]:
    """
    Get all food logs for a specific date
    """

    return db.query(FoodLog).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date == target_date,
        FoodLog.is_deleted == False
    ).order_by(
        FoodLog.meal_time.asc(),
        FoodLog.created_at.asc()
    ).all()


def delete_food_log(
    db: Session,
    log_id: UUID,
    user_id: UUID
) -> bool:
    """
    Xóa bản ghi nhật ký món ăn (Soft Delete)
    Bảo mật: Chỉ chủ sở hữu mới có thể xóa
    """

    # 1. Tìm bản ghi chưa bị xóa (is_deleted == False)
    log = db.query(FoodLog).filter(
        FoodLog.log_id == log_id,
        FoodLog.user_id == user_id,
        FoodLog.is_deleted == False
    ).first()

    if not log:
        return False
    

    log.soft_delete() # Tự động cập nhật is_deleted và deleted_at
    
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


# ==========================================
# WEIGHT LOGGING FUNCTIONS
# ==========================================

def log_weight(
    db: Session,
    user_id: UUID,
    weight_kg: Decimal,
    measured_date: date,
    notes: Optional[str] = None
) -> WeightLog:
    """
    Log user weight (Decimal-safe)
    """

    weight_kg = Decimal(weight_kg)

    # Validate CheckConstraint trước khi lưu
    if not (20 <= weight_kg <= 300):
        raise ValueError("Cân nặng phải nằm trong khoảng từ 20kg đến 300kg.")
    
    try:
        # 2. Kiểm tra bản ghi trùng trong ngày
        existing = db.query(WeightLog).filter(
            WeightLog.user_id == user_id,
            WeightLog.measured_date == measured_date,
            WeightLog.is_deleted == False
        ).first()

        if existing:
            # Cập nhật bản ghi cũ
            existing.weight_kg = weight_kg
            existing.notes = notes
            log_to_return = existing
        else:
            # Tạo bản ghi mới
            weight_log = WeightLog(
                user_id=user_id,
                weight_kg=weight_kg,
                measured_date=measured_date,
                notes=notes
            )
            db.add(weight_log)
            log_to_return = weight_log

        # 3. Commit và Refresh (Issue #11)
        db.commit()
        db.refresh(log_to_return)
        return log_to_return

    except Exception as e:
        # 4. Rollback nếu có lỗi bất ngờ (mất điện, rớt mạng DB...)
        db.rollback()
        raise e

def get_weight_history_paginated(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[WeightLog], int]:
    """Lấy lịch sử cân nặng có phân trang"""

    query = db.query(WeightLog).filter(
        WeightLog.user_id == user_id,
        WeightLog.is_deleted == False # Chỉ lấy dữ liệu hiện hữu
    )
    
    total_count = query.count() #  Cần cho Pagination Metadata
    
    items = query.order_by(
        WeightLog.measured_date.desc()
    ).offset(skip).limit(limit).all()
    
    return items, total_count


def get_latest_weight(
    db: Session,
    user_id: UUID
) -> Optional[WeightLog]:
    """
    Get user's latest weight entry
    """

    return db.query(WeightLog).filter(
        WeightLog.user_id == user_id,
        WeightLog.is_deleted == False
    ).order_by(
        WeightLog.measured_date.desc()
    ).first()
