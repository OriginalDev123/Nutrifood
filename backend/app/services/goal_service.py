from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date

from app.models.user import UserGoal, UserProfile
from app.schemas.user import UserGoalCreate, UserGoalUpdate

# Ngưỡng thay đổi cân/tuần được coi là thực tế (có thể điều chỉnh theo chính sách sản phẩm)
MAX_SAFE_WEIGHT_CHANGE_KG_PER_WEEK = 1.5


def validate_goal_realism(
    goal_type: str,
    current_weight_kg: float,
    target_weight_kg: Optional[float],
    target_date: Optional[date],
) -> None:
    """
    Từ chối mục tiêu không thực tế (ví dụ thay đổi ~10 kg trong vài ngày).
    Chỉ áp kiểm tra tốc độ khi có đủ cân đích + ngày đích và có chênh lệch cân đáng kể.
    """
    if goal_type in ("weight_loss", "weight_gain"):
        if target_weight_kg is None or target_date is None:
            raise ValueError(
                "Với mục tiêu giảm/tăng cân, vui lòng nhập cân nặng đích và thời gian (ngày đích)."
            )
        delta = float(target_weight_kg) - float(current_weight_kg)
        if goal_type == "weight_loss" and delta >= 0:
            raise ValueError(
                "Mục tiêu giảm cân yêu cầu cân nặng đích nhỏ hơn cân nặng hiện tại. "
                "Vui lòng nhập lại mục tiêu hợp lệ."
            )
        if goal_type == "weight_gain" and delta <= 0:
            raise ValueError(
                "Mục tiêu tăng cân yêu cầu cân nặng đích lớn hơn cân nặng hiện tại. "
                "Vui lòng nhập lại mục tiêu hợp lệ."
            )
    else:
        # maintain / healthy_lifestyle: chỉ kiểm tốc độ nếu người dùng đặt cả cân đích và ngày đích
        if target_weight_kg is None or target_date is None:
            return

    abs_delta = abs(float(target_weight_kg) - float(current_weight_kg))
    if abs_delta < 0.05:
        return

    if target_date is None:
        return

    today = date.today()
    days = (target_date - today).days
    if days < 1:
        raise ValueError(
            "Thời gian đạt mục tiêu phải ít nhất là ngày mai. "
            "Vui lòng nhập lại mục tiêu hợp lệ."
        )

    weeks = days / 7.0
    kg_per_week = abs_delta / weeks
    if kg_per_week > MAX_SAFE_WEIGHT_CHANGE_KG_PER_WEEK:
        raise ValueError(
            "Mục tiêu thay đổi cân nặng quá nhanh so với thời gian đã chọn (không khả thể/an toàn). "
            f"Vui lòng nhập lại mục tiêu hợp lệ — gợi ý: không vượt quá khoảng "
            f"{MAX_SAFE_WEIGHT_CHANGE_KG_PER_WEEK:.1f} kg mỗi tuần."
        )


def validate_goal_create_payload(goal_data: UserGoalCreate) -> None:
    tw = float(goal_data.target_weight_kg) if goal_data.target_weight_kg is not None else None
    validate_goal_realism(
        goal_data.goal_type,
        float(goal_data.current_weight_kg),
        tw,
        goal_data.target_date,
    )


def create_user_goal(
    db: Session,
    user_id: UUID,
    goal_data: UserGoalCreate
) -> UserGoal:
    """Create new user goal (deactivates old active goals)"""
    
    try:
        validate_goal_create_payload(goal_data)

        # 1. Hủy kích hoạt các mục tiêu cũ đang hoạt động
        # synchronize_session=False giúp tăng hiệu suất khi update hàng loạt
        db.query(UserGoal)\
            .filter(UserGoal.user_id == user_id, UserGoal.is_active == True)\
            .update({"is_active": False}, synchronize_session=False)

        # 2. Tính toán các chỉ số (Calorie, Macros)
        # Logic tính toán tự động nếu không cung cấp
        if not goal_data.daily_calorie_target:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile and profile.height_cm:
                # Use profile activity_level or default to lightly_active
                activity_level = profile.activity_level or "lightly_active"
                
                bmr = calculate_bmr(
                    goal_data.current_weight_kg,
                    profile.height_cm,
                    profile.date_of_birth,
                    profile.gender
                )
                tdee = calculate_tdee(bmr, activity_level)
                goal_data.daily_calorie_target = calculate_calorie_target(tdee, goal_data.goal_type)
        
        # Calculate macros if not provided and we have calorie target
        if not goal_data.protein_target_g and goal_data.daily_calorie_target:
            macros = calculate_macro_targets(goal_data.daily_calorie_target, goal_data.goal_type)
            goal_data.protein_target_g = macros["protein_target_g"]
            goal_data.carbs_target_g = macros["carbs_target_g"]
            goal_data.fat_target_g = macros["fat_target_g"]

        # 3. Tạo mục tiêu mới
        new_goal = UserGoal(
            user_id=user_id,
            **goal_data.model_dump()
        )
        db.add(new_goal)

        # 4. CHỐT CHẶN CUỐI: Commit cả hai thao tác cùng lúc
        db.commit()
        db.refresh(new_goal)
        return new_goal

    except (IntegrityError, Exception) as e:
        # 5. HOÀN TÁC: Nếu lỗi, khôi phục lại trạng thái cũ (Issue #13)
        db.rollback()
        if isinstance(e, IntegrityError) and "one_active_goal_per_user" in str(e):
            raise ValueError("Người dùng đã có một mục tiêu đang hoạt động.")
        raise ValueError(f"Lỗi khi thiết lập mục tiêu: {str(e)}")


def get_user_goals(
    db: Session,
    user_id: UUID,
    active_only: bool = False
) -> List[UserGoal]:
    """Get all user goals"""
    query = db.query(UserGoal).filter(UserGoal.user_id == user_id, UserGoal.is_deleted == False)    
    
    if active_only:
        query = query.filter(UserGoal.is_active == True)
    
    return query.order_by(UserGoal.created_at.desc()).all()


def get_active_goal(db: Session, user_id: UUID) -> Optional[UserGoal]:
    """Get user's active goal"""
    return db.query(UserGoal)\
        .filter(UserGoal.user_id == user_id, UserGoal.is_active == True, UserGoal.is_deleted == False)\
        .first()


def update_goal(
    db: Session,
    user_id: UUID,
    goal_id: UUID,
    goal_data: UserGoalUpdate
) -> UserGoal:
    """Update user goal"""
    goal = db.query(UserGoal)\
        .filter(UserGoal.goal_id == goal_id, UserGoal.user_id == user_id, UserGoal.is_deleted == False)\
        .first()
    
    if not goal:
        raise ValueError("Goal not found")
    
    # Update only provided fields
    update_data = goal_data.model_dump(exclude_unset=True)

    merged_type = update_data.get("goal_type", goal.goal_type)
    merged_cw = update_data.get("current_weight_kg", goal.current_weight_kg)
    merged_tw = update_data.get("target_weight_kg", goal.target_weight_kg)
    merged_td = update_data.get("target_date", goal.target_date)
    if merged_cw is not None:
        validate_goal_realism(
            merged_type,
            float(merged_cw),
            float(merged_tw) if merged_tw is not None else None,
            merged_td,
        )

    for field, value in update_data.items():
        setattr(goal, field, value)
    
    try:
        db.commit()
        db.refresh(goal)
        return goal
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database error: {str(e)}")


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    date_of_birth: date,
    gender: str
) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
    BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + s
    where s = +5 for males, -161 for females
    """
    from app.services.user_service import calculate_age
    age = calculate_age(date_of_birth)
    
    # Mifflin-St Jeor Equation: (10 × weight) + (6.25 × height) - (5 × age) + s
    bmr = (10 * float(weight_kg)) + (6.25 * float(height_cm)) - (5 * age)
    
    if gender == "male":
        bmr += 5
    elif gender == "female":
        bmr -= 161
    else:
        bmr -= 78  # Trung bình cho 'other'
    
    return round(bmr, 2)


def calculate_tdee(bmr: float, activity_level: str) -> int:
    """
    Calculate Total Daily Energy Expenditure
    TDEE = BMR × Activity Factor
    """
    activity_multipliers = {
        "sedentary": 1.2,           # Little or no exercise
        "lightly_active": 1.375,    # Exercise 1-3 days/week
        "moderately_active": 1.55,  # Exercise 3-5 days/week
        "very_active": 1.725,       # Exercise 6-7 days/week
        "extra_active": 1.9         # Physical job or training twice/day
    }
    
    multiplier = activity_multipliers.get(activity_level, 1.375)
    tdee = bmr * multiplier
    
    return round(tdee)


def calculate_calorie_target(tdee: int, goal_type: str) -> int:
    """
    Calculate daily calorie target based on goal
    
    - weight_loss: TDEE - 500 (lose ~0.5kg/week)
    - weight_gain: TDEE + 500 (gain ~0.5kg/week)
    - maintain: TDEE
    - healthy_lifestyle: TDEE
    """
    adjustments = {
        "weight_loss": -500,
        "weight_gain": 500,
        "maintain": 0,
        "healthy_lifestyle": 0
    }
    
    adjustment = adjustments.get(goal_type, 0)
    target = tdee + adjustment
    
    # Ensure minimum 1200 calories for safety
    return max(1200, target)


def calculate_macro_targets(
    daily_calories: int,
    goal_type: str
) -> dict:
    """
    Calculate protein, carbs, fat targets (in grams)
    
    Standard ratios:
    - weight_loss: 40% protein, 30% carbs, 30% fat
    - weight_gain: 25% protein, 50% carbs, 25% fat
    - maintain/healthy: 30% protein, 40% carbs, 30% fat
    """
    # 1. Tránh tính toán với calo không hợp lệ
    if not daily_calories or daily_calories <= 0:
        return {
            "protein_target_g": 0,
            "carbs_target_g": 0,
            "fat_target_g": 0
        }
        
    ratios = {
        "weight_loss": {"protein": 0.40, "carbs": 0.30, "fat": 0.30},
        "weight_gain": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
        "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
        "healthy_lifestyle": {"protein": 0.30, "carbs": 0.40, "fat": 0.30}
    }
    
    ratio = ratios.get(goal_type, ratios["maintain"])
    
    # Calculate grams (4 cal/g for protein & carbs, 9 cal/g for fat)
    protein_g = round((daily_calories * ratio["protein"]) / 4)
    carbs_g = round((daily_calories * ratio["carbs"]) / 4)
    fat_g = round((daily_calories * ratio["fat"]) / 9)
    
    return {
        "protein_target_g": protein_g,
        "carbs_target_g": carbs_g,
        "fat_target_g": fat_g
    }


def deactivate_goal(db: Session, user_id: UUID, goal_id: UUID) -> None:
    """Deactivate a user goal (soft delete)"""
    goal = db.query(UserGoal)\
        .filter(UserGoal.goal_id == goal_id, UserGoal.user_id == user_id, UserGoal.is_deleted == False)\
        .first()
    
    if not goal:
        raise ValueError("Goal not found")
    
    goal.is_active = False
    goal.soft_delete()
    
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database error: {str(e)}")