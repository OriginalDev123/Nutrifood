"""
User Profile Routes
Endpoints for managing user profiles
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services import user_service
from app.utils.dependencies import get_current_active_user
from app.utils.profile_helpers import enrich_profile_response

router = APIRouter(prefix="/users/me", tags=["User Profile"])


# ==========================================
# HELPER FUNCTION (TRÁNH LẶP CODE)
# ==========================================

def _prepare_profile_response(db: Session, profile, user_id: UUID):
    """
    Hàm bổ trợ để tính toán Age và BMI cho response.
    Giải quyết Soft Delete và Decimal.
    """
    # Map các trường cơ bản từ profile object
    response_data = {
        "profile_id": str(profile.profile_id),
        "user_id": str(profile.user_id),
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "activity_level": profile.activity_level,
        "profile_image_url": profile.profile_image_url,
        "timezone": profile.timezone,
        "language": profile.language,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "bmi": None,
        "bmi_category": None,
        "age": None
    }
    
    # 1. Tính tuổi nếu có ngày sinh
    if profile.date_of_birth:
        response_data["age"] = user_service.calculate_age(profile.date_of_birth)
    
    # 2. Tính BMI nếu có chiều cao
    if profile.height_cm:
        from app.models.food_log import WeightLog
        # Chỉ lấy cân nặng chưa bị xóa mềm (is_deleted == False)
        latest_weight = db.query(WeightLog)\
            .filter(
                WeightLog.user_id == user_id,
                WeightLog.is_deleted == False
            )\
            .order_by(WeightLog.measured_date.desc())\
            .first()
        
        # Thêm try-except và kiểm tra dữ liệu kỹ lưỡng
        if latest_weight and latest_weight.weight_kg:
            try:
                # Ép kiểu an toàn và tính toán
                h_cm = float(profile.height_cm)
                w_kg = float(latest_weight.weight_kg)
                
                if h_cm > 0: 
                    bmi = user_service.calculate_bmi(h_cm, w_kg)
                    response_data["bmi"] = bmi
                    response_data["bmi_category"] = user_service.get_bmi_category(bmi)
            except (ValueError, TypeError, ZeroDivisionError): pass
    
    return response_data


@router.get("/profile", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile
    
    Returns profile with calculated fields:
    - age (from date_of_birth)
    - bmi (from height & latest weight)
    - bmi_category
    """
    profile = user_service.get_user_profile(db, current_user.user_id)
    

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return enrich_profile_response(db, profile, current_user.user_id)

    # # Calculate additional fields
    # response_data = {
    #     "profile_id": str(profile.profile_id),
    #     "user_id": str(profile.user_id),
    #     "date_of_birth": profile.date_of_birth,
    #     "gender": profile.gender,
    #     "height_cm": profile.height_cm,
    #     "activity_level": profile.activity_level,
    #     "profile_image_url": profile.profile_image_url,
    #     "timezone": profile.timezone,
    #     "language": profile.language,
    #     "created_at": profile.created_at,
    #     "updated_at": profile.updated_at,
    # }
    
    # # Calculate age if DOB exists
    # if profile.date_of_birth:
    #     response_data["age"] = user_service.calculate_age(profile.date_of_birth)
    
    # # Calculate BMI if height exists
    # if profile.height_cm:
    #     from app.models.food_log import WeightLog
    #     latest_weight = db.query(WeightLog)\
    #         .filter(WeightLog.user_id == current_user.user_id)\
    #         .order_by(WeightLog.measured_date.desc())\
    #         .first()
        
    #     if latest_weight:
    #         bmi = user_service.calculate_bmi(profile.height_cm, float(latest_weight.weight_kg))
    #         response_data["bmi"] = bmi
    #         response_data["bmi_category"] = user_service.get_bmi_category(bmi)
    
    # return _prepare_profile_response(db, profile, current_user.user_id)


@router.patch("/profile", response_model=UserProfileResponse)
def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    
    Only provided fields will be updated (partial update)
    """
    try:
        updated_profile = user_service.update_user_profile(
            db, 
            current_user.user_id, 
            profile_update
        )

        return enrich_profile_response(db, updated_profile, current_user.user_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
