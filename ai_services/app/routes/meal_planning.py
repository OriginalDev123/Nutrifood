"""
Meal Planning Routes

API endpoints for AI-powered meal planning using Gemini.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.meal_planning_ai_service import get_meal_planning_ai_service

router = APIRouter(
    prefix="/meal-planning",
    tags=["Meal Planning"]
)


class HealthProfileInfo(BaseModel):
    """Health profile information for meal planning"""
    health_conditions: List[str] = Field(default_factory=list, description="Health conditions (e.g., diabetes, hypertension)")
    food_allergies: List[str] = Field(default_factory=list, description="Food allergies to avoid (e.g., seafood, peanuts)")
    dietary_preferences: List[str] = Field(default_factory=list, description="Dietary preferences (e.g., Low Carb, Keto, Vegetarian)")


class MealPlanningRequest(BaseModel):
    """Request model for meal planning"""
    
    daily_calorie_target: int = Field(..., ge=500, le=5000, description="Target calories per day")
    days: int = Field(7, ge=1, le=30, description="Number of days in plan")
    goal_type: str = Field("maintain", pattern="^(weight_loss|weight_gain|maintain|healthy_lifestyle)$")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    available_foods: Optional[List[Dict]] = Field(None, description="Available foods from database")
    health_profile: Optional[HealthProfileInfo] = Field(None, description="User's health profile for filtering")
    language: str = Field("vi", pattern="^(vi|en)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "daily_calorie_target": 2000,
                "days": 7,
                "goal_type": "weight_loss",
                "preferences": {"tags": ["healthy", "quick"]},
                "available_foods": [
                    {"name_vi": "Cơm trắng", "calories": 260, "protein": 5, "carbs": 57, "fat": 0.5}
                ],
                "health_profile": {
                    "health_conditions": ["Tiểu đường type 2"],
                    "food_allergies": ["Hải sản", "Tôm"],
                    "dietary_preferences": ["Low Carb"]
                },
                "language": "vi"
            }
        }


class MealResponse(BaseModel):
    """Single meal in plan"""
    meal_type: str = Field(..., description="breakfast, lunch, dinner, or snack")
    food_name: str = Field(..., description="Name of the food/dish")
    calories: int = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)
    is_custom: bool = Field(default=False, description="Whether this is a custom AI-created dish")
    ingredients: Optional[List[str]] = Field(default=None, description="Main ingredients for custom dishes")
    recipe_notes: Optional[str] = Field(default=None, description="Brief cooking instructions for custom dishes")


class DayPlan(BaseModel):
    """Single day plan"""
    date: str
    meals: List[MealResponse]


class MealPlanResponse(BaseModel):
    """Response containing meal plan"""
    days: List[DayPlan]
    
    class Config:
        json_schema_extra = {
            "example": {
                "days": [
                    {
                        "date": "Ngày 1",
                        "meals": [
                            {
                                "meal_type": "breakfast",
                                "food_name": "Bánh mì trứng",
                                "calories": 350,
                                "protein_g": 15,
                                "carbs_g": 40,
                                "fat_g": 12,
                                "is_custom": False
                            },
                            {
                                "meal_type": "lunch",
                                "food_name": "Salad ức gà Keto",
                                "calories": 350,
                                "protein_g": 35,
                                "carbs_g": 8,
                                "fat_g": 20,
                                "is_custom": True,
                                "ingredients": ["ức gà", "xà lách", "bơ", "dầu olive", "trứng"],
                                "recipe_notes": "Nướng ức gà, xé nhỏ, trộn với rau và sốt"
                            }
                        ]
                    }
                ]
            }
        }


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanningRequest):
    """
    Generate AI-powered meal plan.
    
    **Features:**
    - Uses Gemini AI for intelligent meal selection
    - Respects calorie targets and goal type
    - Balances macros across meals
    - Diversifies diet (no repetition within 3 days)
    - Optionally uses available foods from database
    - **CAN CREATE CUSTOM DISHES** not in database when needed
    - Respects health profile (allergies, conditions, dietary preferences)
    
    **Parameters:**
    - daily_calorie_target: Target calories per day (500-5000)
    - days: Number of days (1-30)
    - goal_type: weight_loss, weight_gain, maintain, healthy_lifestyle
    - preferences: Optional filters (tags, categories, etc.)
    - available_foods: List of foods to choose from
    - health_profile: User's health profile for filtering (allergies, conditions, preferences)
    - language: vi (Vietnamese) or en (English)
    
    **Returns:**
    - Complete meal plan with days and meals
    - Custom dishes include ingredients and recipe notes
    """
    try:
        service = get_meal_planning_ai_service()
        
        # Convert health_profile to dict if provided
        health_profile_dict = None
        if request.health_profile:
            health_profile_dict = {
                "health_conditions": request.health_profile.health_conditions or [],
                "food_allergies": request.health_profile.food_allergies or [],
                "dietary_preferences": request.health_profile.dietary_preferences or [],
            }
        
        result = await service.generate_meal_plan(
            daily_calorie_target=request.daily_calorie_target,
            days=request.days,
            goal_type=request.goal_type,
            preferences=request.preferences,
            available_foods=request.available_foods,
            health_profile=health_profile_dict,
            language=request.language
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meal planning error: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check for meal planning service.
    
    Returns service status and available endpoints.
    """
    return {
        "status": "healthy",
        "service": "Meal Planning AI Service",
        "version": "1.1.0",
        "model": "gemini-2.5-flash",
        "features": [
            "AI-powered meal selection",
            "Calorie-based planning",
            "Goal-specific distributions",
            "Macro balancing",
            "Diet diversification",
            "Custom dish creation",
            "Health profile filtering (allergies, conditions, preferences)"
        ]
    }
