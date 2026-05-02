"""
Food Logging Schemas

Pydantic models for food logging requests and responses
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from typing import Optional, Dict
from datetime import date, time, datetime
from uuid import UUID
from decimal import Decimal


# ==========================================
# FOOD LOG SCHEMAS
# ==========================================

class FoodLogCreate(BaseModel):
    """Schema for creating food log"""
    
    food_id: UUID
    serving_id: Optional[UUID] = Field(None, description="Serving size ID (optional, will use default if not provided)")
    meal_type: str = Field(
        ...,
        pattern="^(breakfast|lunch|dinner|snack)$"
    )
    meal_date: date
    quantity: Decimal = Field(default=1.0, gt=0)
    serving_size_g: Optional[Decimal] = Field(None, gt=0, description="Manual serving size in grams (alternative to serving_id)")
    meal_time: Optional[time] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    ai_prediction_correct: Optional[bool] = None
    was_ai_recognized: bool = Field(default=False)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "food_id": "123e4567-e89b-12d3-a456-426614174000",
                "serving_id": "123e4567-e89b-12d3-a456-426614174001",
                "meal_type": "breakfast",
                "meal_date": "2024-12-22",
                "quantity": 1.0,
                "meal_time": "08:30:00",
                "notes": "Bữa sáng ngon"
            }
        }
    }


class FoodLogResponse(BaseModel):
    """Schema for food log response"""
    
    log_id: UUID
    food_name: str
    serving_size_g: Decimal
    quantity: Decimal
    calories: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    meal_type: str
    meal_date: date
    meal_time: Optional[time]
    notes: Optional[str]
    ai_prediction_correct: Optional[bool]
    was_ai_recognized: bool
    ai_confidence: Optional[Decimal]
    created_at: datetime
    
    
    @field_serializer(
        'serving_size_g', 'quantity', 'calories', 
        'protein_g', 'carbs_g', 'fat_g', 'ai_confidence'
    )
    def serialize_decimal(self, value: Decimal) -> Optional[float]:
        return float(value) if value is not None else 0.0
    
    model_config = ConfigDict(from_attributes=True)


class DailySummaryResponse(BaseModel):
    """Schema for daily nutrition summary"""
    
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    meal_count: int
    meals_breakdown: Dict[str, float]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2024-12-22",
                "total_calories": 1850.5,
                "total_protein_g": 92.3,
                "total_carbs_g": 215.7,
                "total_fat_g": 58.2,
                "meal_count": 4,
                "meals_breakdown": {
                    "breakfast": 450.0,
                    "lunch": 700.0,
                    "dinner": 600.0,
                    "snack": 100.5
                }
            }
        }
    }


# ==========================================
# WEIGHT LOG SCHEMAS
# ==========================================

class WeightLogCreate(BaseModel):
    """Schema for creating weight log"""
    
    weight_kg: Decimal = Field(..., gt=0, le=300)
    measured_date: date
    notes: Optional[str] = None
    
    @field_validator('weight_kg')
    @classmethod
    def validate_weight(cls, v):
        """Validate weight is reasonable"""
        if v < 20 or v > 300:
            raise ValueError('Weight must be between 20 and 300 kg')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "weight_kg": 70.5,
                "measured_date": "2024-12-22",
                "notes": "Cân buổi sáng"
            }
        }
    }


class WeightLogResponse(BaseModel):
    """Schema for weight log response"""
    
    weight_log_id: UUID
    user_id: UUID
    weight_kg: Decimal
    measured_date: date
    notes: Optional[str]
    created_at: datetime
    
    @field_serializer('weight_kg')
    def serialize_weight(self, value: Decimal) -> float:
        return float(value) if value is not None else 0.0
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# FOOD LOG UPDATE SCHEMA
# ==========================================

class FoodLogUpdate(BaseModel):
    """Schema for updating food log (partial or full)"""
    
    quantity: Optional[Decimal] = Field(None, gt=0, description="Number of servings")
    meal_type: Optional[str] = Field(None, pattern="^(breakfast|lunch|dinner|snack)$")
    meal_date: Optional[date] = None
    meal_time: Optional[time] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quantity": 2.0,
                "notes": "Cập nhật ghi chú"
            }
        }
    )