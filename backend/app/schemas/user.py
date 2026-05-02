"""
User Schemas (Pydantic v2)

Pydantic models for user-related requests and responses
"""

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    field_serializer
)
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


# ==========================================
# USER AUTHENTICATION SCHEMAS
# ==========================================

class UserCreate(BaseModel):
    """Schema for user registration"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters)"
    )
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "Nguyễn Văn A",
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""

    user_id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "Nguyễn Văn A",
                "is_active": True,
                "is_admin": False,
                "email_verified": True,
                "created_at": "2024-12-22T10:00:00",
                "last_login": "2024-12-22T15:30:00",
            }
        },
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    
    refresh_token: str = Field(..., description="Refresh token from login")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


# ==========================================
# USER PROFILE SCHEMAS
# ==========================================

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""

    full_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[Decimal] = Field(None, ge=50, le=300)
    activity_level: Optional[str] = Field(
        None,
        pattern="^(sedentary|lightly_active|moderately_active|very_active|extra_active)$",
    )
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    
    profile_image_url: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "height_cm": 175.5,
                "activity_level": "moderately_active",
                "language": "vi",
            }
        }
    )


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""

    profile_id: UUID
    user_id: UUID
    full_name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    date_of_birth: Optional[date]
    gender: Optional[str]
    height_cm: Optional[Decimal]
    activity_level: Optional[str]
    profile_image_url: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    
    # Calculated fields
    age: Optional[int] = Field(None, description="Calculated age from date_of_birth")
    bmi: Optional[float] = Field(None, description="Calculated BMI from height and latest weight")
    bmi_category: Optional[str] = Field(None, description="BMI category (underweight/normal/overweight/obese)")

    @field_serializer('height_cm')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# USER GOAL SCHEMAS
# ==========================================

class UserGoalCreate(BaseModel):
    """Schema for creating user goal"""

    goal_type: str = Field(
        ...,
        pattern="^(weight_loss|weight_gain|maintain|healthy_lifestyle)$",
    )
    current_weight_kg: Decimal = Field(..., gt=0, le=300)
    target_weight_kg: Optional[Decimal] = Field(None, gt=0, le=300)
    target_date: Optional[date] = None
    daily_calorie_target: Optional[int] = Field(None, gt=0)
    protein_target_g: Optional[int] = Field(None, ge=0)
    carbs_target_g: Optional[int] = Field(None, ge=0)
    fat_target_g: Optional[int] = Field(None, ge=0)

    health_conditions: List[str] = Field(default_factory=list)
    food_allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("Target date must be in the future")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goal_type": "weight_loss",
                "current_weight_kg": 80.0,
                "target_weight_kg": 70.0,
                "target_date": "2025-06-01",
                "daily_calorie_target": 2000,
                "protein_target_g": 150,
                "carbs_target_g": 200,
                "fat_target_g": 60,
                "food_allergies": ["peanuts", "shellfish"],
                "dietary_preferences": ["low_carb"],
            }
        }
    )

class UserGoalUpdate(BaseModel):
    """Schema for updating user goal (all fields optional)"""

    goal_type: Optional[str] = Field(
        None,
        pattern="^(weight_loss|weight_gain|maintain|healthy_lifestyle)$",
    )
    current_weight_kg: Optional[Decimal] = Field(None, gt=0, le=300)
    target_weight_kg: Optional[Decimal] = Field(None, gt=0, le=300)
    target_date: Optional[date] = None
    daily_calorie_target: Optional[int] = Field(None, gt=0)
    protein_target_g: Optional[int] = Field(None, ge=0)
    carbs_target_g: Optional[int] = Field(None, ge=0)
    fat_target_g: Optional[int] = Field(None, ge=0)

    health_conditions: Optional[List[str]] = None
    food_allergies: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("Target date must be in the future")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_weight_kg": 75.0,
                "target_weight_kg": 70.0,
                "daily_calorie_target": 1800,
                "is_active": True,
            }
        }
    )

class UserGoalResponse(BaseModel):
    """Schema for user goal response"""

    goal_id: UUID
    user_id: UUID
    goal_type: str
    current_weight_kg: Decimal
    target_weight_kg: Optional[Decimal]
    target_date: Optional[date]
    daily_calorie_target: Optional[int]
    protein_target_g: Optional[int]
    carbs_target_g: Optional[int]
    fat_target_g: Optional[int]

    health_conditions: List[str]
    food_allergies: List[str]
    dietary_preferences: List[str]

    is_active: bool
    created_at: datetime

    @field_serializer('current_weight_kg', 'target_weight_kg')
    def serialize_weight(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# COMBINED SCHEMAS
# ==========================================

class UserWithProfile(UserResponse):
    profile: Optional[UserProfileResponse] = None


class UserComplete(UserResponse):
    profile: Optional[UserProfileResponse] = None
    active_goal: Optional[UserGoalResponse] = None
