"""
Pydantic Schemas Package

Schemas for request/response validation and serialization
"""

from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserProfileResponse,
    UserGoalCreate, UserGoalResponse
)
from app.schemas.food import (
    FoodResponse, FoodServingResponse, FoodSearchResponse
)
from app.schemas.food_log import (
    FoodLogCreate, FoodLogResponse, DailySummaryResponse,
    WeightLogCreate, WeightLogResponse
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserProfileResponse",
    "UserGoalCreate",
    "UserGoalResponse",
    
    # Food schemas
    "FoodResponse",
    "FoodServingResponse",
    "FoodSearchResponse",
    
    # Food logging schemas
    "FoodLogCreate",
    "FoodLogResponse",
    "DailySummaryResponse",
    "WeightLogCreate",
    "WeightLogResponse",
]