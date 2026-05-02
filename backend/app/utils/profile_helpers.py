# app/utils/profile_helpers.py
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User, UserProfile
from app.models.food_log import WeightLog
from app.services import user_service

def enrich_profile_response(
    db: Session,
    profile: UserProfile,
    user_id: UUID
) -> dict:
    """Add calculated fields to profile response"""
    user_row = db.query(User).filter(User.user_id == user_id).first()

    response_data = {
        "profile_id": str(profile.profile_id),
        "user_id": str(profile.user_id),
        "full_name": user_row.full_name if user_row else None,
        "email": user_row.email if user_row else None,
        "email_verified": user_row.email_verified if user_row else None,
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "activity_level": profile.activity_level,
        "profile_image_url": profile.profile_image_url,
        "timezone": profile.timezone,
        "language": profile.language,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "age": None,
        "bmi": None,
        "bmi_category": None,
    }
    
    # Calculate age
    if profile.date_of_birth:
        try:
            response_data["age"] = user_service.calculate_age(profile.date_of_birth)
        except ValueError:
            pass
    
    # Calculate BMI
    if profile.height_cm:
        latest_weight = db.query(WeightLog)\
            .filter(
                WeightLog.user_id == user_id,
                WeightLog.is_deleted == False
            )\
            .order_by(WeightLog.measured_date.desc())\
            .first()
        
        if latest_weight and latest_weight.weight_kg:
            try:
                bmi = user_service.calculate_bmi(
                    float(profile.height_cm),
                    float(latest_weight.weight_kg)
                )
                response_data["bmi"] = bmi
                response_data["bmi_category"] = user_service.get_bmi_category(bmi)
            except (ValueError, TypeError, ZeroDivisionError):
                pass
    
    return response_data