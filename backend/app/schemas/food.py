"""
Food Schemas

Pydantic models for food-related requests and responses
"""

from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ==========================================
# FOOD SERVING SCHEMAS
# ==========================================

class FoodServingResponse(BaseModel):
    """Schema for food serving response"""

    serving_id: UUID
    food_id: UUID
    serving_size_g: Decimal
    serving_unit: str
    description: Optional[str] = None
    is_default: bool

    # Chuyển Decimal sang float cho JSON
    @field_serializer('serving_size_g')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value) if value is not None else 0.0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# FOOD SCHEMAS
# ==========================================

class FoodResponse(BaseModel):
    """Schema for food response"""
    
    food_id: UUID
    name_vi: str
    name_en: Optional[str]
    description: Optional[str]
    category: str
    cuisine_type: Optional[str]
    calories_per_100g: Decimal
    protein_per_100g: Decimal
    carbs_per_100g: Decimal
    fat_per_100g: Decimal
    fiber_per_100g: Optional[Decimal]
    sugar_per_100g: Optional[Decimal]
    sodium_per_100g: Optional[Decimal]
    barcode: Optional[str]
    image_url: Optional[str]
    source: Optional[str]
    created_by: Optional[UUID]
    is_verified: bool
    
    # Tự động chuyển đổi danh sách các trường Decimal sang float
    @field_serializer(
        'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 
        'fat_per_100g', 'fiber_per_100g', 'sugar_per_100g'
    )
    def serialize_decimals(self, value: Optional[Decimal]) -> float:
        return float(value) if value is not None else 0.0

    model_config = ConfigDict(from_attributes=True)


class FoodWithServings(FoodResponse):
    """Food response with servings included"""
    
    servings: List[FoodServingResponse] = []


class FoodSearchResponse(BaseModel):
    """Schema for food search results"""
    
    total: int
    foods: List[FoodResponse]
    page: int
    page_size: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "foods": [],
                "page": 1,
                "page_size": 20
            }
        }


class FoodCreate(BaseModel):
    """Schema for creating food (admin only)"""
    
    name_vi: str = Field(..., max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., max_length=100)
    cuisine_type: Optional[str] = Field(None, max_length=50)
    calories_per_100g: Decimal = Field(..., ge=0)
    protein_per_100g: Decimal = Field(0, ge=0)
    carbs_per_100g: Decimal = Field(0, ge=0)
    fat_per_100g: Decimal = Field(0, ge=0)
    fiber_per_100g: Optional[Decimal] = Field(0, ge=0)
    sugar_per_100g: Optional[Decimal] = Field(0, ge=0)
    sodium_per_100g: Optional[Decimal] = Field(0, ge=0)
    barcode: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=100)
    create_by: Optional[UUID] = None
    image_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name_vi": "Phở bò",
                "name_en": "Beef Pho",
                "category": "soup",
                "cuisine_type": "vietnamese",
                "calories_per_100g": 85.0,
                "protein_per_100g": 5.2,
                "carbs_per_100g": 11.0,
                "fat_per_100g": 2.5
            }
        }