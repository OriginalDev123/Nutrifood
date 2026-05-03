"""
Health Profile Schemas
Pydantic models for user health profile (dietary preferences, allergies, health conditions)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


# ==========================================
# HEALTH PROFILE SCHEMAS
# ==========================================

class HealthProfileInput(BaseModel):
    """Schema for health profile input (used when creating/updating)"""
    
    health_conditions: List[str] = Field(
        default_factory=list,
        description="Danh sách các bệnh đang mắc (e.g., 'Tiểu đường', 'Huyết áp cao')"
    )
    food_allergies: List[str] = Field(
        default_factory=list,
        description="Danh sách dị ứng thực phẩm (e.g., 'Hải sản', 'Đậu phộng', 'Gluten')"
    )
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Chế độ ăn ưu tiên (e.g., 'Low Carb', 'Keto', 'Eat Clean', 'Vegetarian')"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "health_conditions": ["Tiểu đường type 2", "Huyết áp cao"],
                "food_allergies": ["Hải sản", "Đậu phộng", "Gluten"],
                "dietary_preferences": ["Low Carb", "Eat Clean"]
            }
        }
    )


class HealthProfileResponse(BaseModel):
    """Schema for health profile response"""
    
    health_conditions: List[str] = Field(default_factory=list)
    food_allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "health_conditions": ["Tiểu đường type 2", "Huyết áp cao"],
                "food_allergies": ["Hải sản", "Đậu phộng", "Gluten"],
                "dietary_preferences": ["Low Carb", "Eat Clean"],
                "updated_at": "2024-12-22T10:00:00"
            }
        }
    )


# ==========================================
# MEAL PLAN WITH HEALTH PROFILE
# ==========================================

class GenerateMealPlanWithHealthParams(BaseModel):
    """Schema for meal plan generation with health profile"""
    
    plan_name: str = Field(..., min_length=1, max_length=255)
    days: int = Field(default=7, ge=1, le=30)
    categories: Optional[str] = Field(None, description="Comma-separated categories")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    max_cook_time: Optional[int] = Field(None, ge=0, description="Maximum cooking time in minutes")
    health_profile: Optional[HealthProfileInput] = Field(
        None,
        description="Health profile for personalized meal planning"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan_name": "Kế hoạch giảm cân tuần này",
                "days": 7,
                "health_profile": {
                    "health_conditions": ["Tiểu đường type 2"],
                    "food_allergies": ["Hải sản", "Đậu phộng"],
                    "dietary_preferences": ["Low Carb", "Eat Clean"]
                }
            }
        }
    )
