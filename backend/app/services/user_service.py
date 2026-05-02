"""
User Profile Service
Business logic for user profile management
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date

from app.models.user import User, UserProfile
from app.schemas.user import UserProfileUpdate


def get_user_profile(db: Session, user_id: UUID) -> Optional[UserProfile]:
    """Get user profile by user_id"""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def update_user_profile(
    db: Session, 
    user_id: UUID, 
    profile_data: UserProfileUpdate
) -> UserProfile:
    """Update user profile"""
    profile = get_user_profile(db, user_id)
    
    if not profile:
        raise ValueError("Profile not found")
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)

    if "full_name" in update_data:
        fn = update_data.pop("full_name")
        user_row = db.query(User).filter(User.user_id == user_id).first()
        if user_row is not None:
            user_row.full_name = fn
    
    if "height_cm" in update_data and update_data["height_cm"] is not None:
        height = float(update_data["height_cm"])
        if height < 50 or height > 300:
            raise ValueError("Chiều cao phải nằm trong khoảng 50cm - 300cm")
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    try:
        db.commit()
        db.refresh(profile)
        return profile
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database error: {str(e)}")


def calculate_bmi(height_cm: Optional[float], weight_kg: Optional[float]) -> Optional[float]:
    """
    Calculate BMI (Body Mass Index) an toàn.
    """
    # 1. Kiểm tra Null và các giá trị không hợp lệ ngay lập tức
    if height_cm is None or weight_kg is None:
        return None
        
    try:
        # 2. Ép kiểu sang float để tính toán (Xử lý trường hợp nhận Decimal từ DB)
        h_float = float(height_cm)
        w_float = float(weight_kg)

        # 3. Chiều cao phải lớn hơn 0 để tránh chia cho 0
        if h_float <= 0 or w_float <= 0:
            return None
            
        height_m = h_float / 100
        bmi = w_float / (height_m ** 2)
        
        return round(bmi, 2)
        
    except (ZeroDivisionError, TypeError, ValueError):
        # 4. Chặn đứng mọi lỗi phát sinh ngoài dự kiến
        return None


def calculate_age(date_of_birth: date) -> int:
    """
    Tính tuổi từ ngày sinh với cơ chế chống dữ liệu âm và không hợp lệ.
    """
    from datetime import date as dt_date
    today = dt_date.today()
    
    # ✅ Lớp bảo vệ 1: Chặn ngày sinh ở tương lai
    if date_of_birth > today:
        raise ValueError("Ngày sinh không thể nằm trong tương lai.")

    age = today.year - date_of_birth.year
    
    # Điều chỉnh nếu chưa đến ngày sinh nhật trong năm nay
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    
    # ✅ Lớp bảo vệ 2: Kiểm tra an toàn cuối cùng
    if age < 0:
        raise ValueError("Ngày sinh không hợp lệ.")
        
    return age

def get_bmi_category(bmi: float) -> str:
    """Get BMI category (WHO standards)"""
    if bmi is None:
        return "Not available"
    
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"