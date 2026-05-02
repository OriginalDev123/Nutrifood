"""
Recommendation API Routes - Smart Food Suggestions
Fast, database-driven recommendations (NO AI calls)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import logging

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_active_user
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/next-meal")
async def suggest_next_meal(
    meal_type: str = Query(
        ...,
        regex="^(breakfast|lunch|dinner|snack)$",
        description="Meal type: breakfast | lunch | dinner | snack"
    ),
    date: Optional[date] = Query(
        None,
        description="Target date (YYYY-MM-DD). Default: today"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **Get smart food recommendations for next meal**
    
    ### Fast Response (<500ms)
    - Database-driven only (no AI calls)
    - Uses NutritionCalculatorCore
    - Rule-based confidence scoring
    
    ### Algorithm:
    1. Calculate remaining nutrients for the day
    2. Find foods matching nutrient gap
    3. Generate confidence scores & Vietnamese reasons
    4. Return top 5 suggestions with serving sizes
    
    ### Use Cases:
    - User opens app → "What should I eat for lunch?"
    - User finished breakfast → Show dinner suggestions
    - Meal planning assistant
    
    ### Request:
    ```
    GET /api/recommendations/next-meal?meal_type=dinner&date=2026-02-22
    ```
    
    ### Response:
    ```json
    {
      "meal_type": "dinner",
      "date": "2026-02-22",
      "remaining_nutrients": {
        "calories": 800,
        "protein": 45.5,
        "carbs": 80.0,
        "fat": 25.0
      },
      "suggestions": [
        {
          "food_id": "uuid",
          "name_vi": "Ức gà nướng",
          "name_en": "Grilled chicken breast",
          "confidence": 0.88,
          "reason": "Giàu protein (31g/100g), còn thiếu 45.5g protein",
          "serving_suggestion": "150g (~1 bát nhỏ)",
          "nutrition_per_100g": {
            "calories": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6
          }
        }
      ],
      "processing_time_ms": 234
    }
    ```
    
    ### Error Codes:
    - **400**: Invalid meal_type or no active goal
    - **401**: Not authenticated
    - **500**: Server error
    """
    
    try:
        logger.info(
            f"➡️  Recommendation request: user_id={current_user.user_id}, "
            f"meal_type={meal_type}, date={date or 'today'}"
        )
        
        # Initialize service
        service = RecommendationService(db)
        
        # Get recommendations
        result = await service.suggest_next_meal(
            user_id=current_user.user_id,
            meal_type=meal_type,
            target_date=date
        )
        
        logger.info(
            f"✅ Returned {len(result['suggestions'])} suggestions "
            f"(time: {result['processing_time_ms']}ms)"
        )
        
        return result
    
    except ValueError as e:
        # Business logic errors (no active goal, etc.)
        logger.warning(f"⚠️ Recommendation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/meal-timing")
async def suggest_meal_timing(
    date: Optional[date] = Query(None, description="Target date (default: today)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **Suggest which meal to eat next based on time & logged meals**
    
    ### Logic:
    - Check current time of day
    - Check which meals already logged
    - Suggest next appropriate meal
    
    ### Use Case:
    User opens app → "What meal should I log?"
    
    ### Response:
    ```json
    {
      "suggested_meal_type": "lunch",
      "reason": "Đã đến giờ ăn trưa",
      "already_logged": ["breakfast"]
    }
    ```
    """
    
    try:
        service = RecommendationService(db)
        
        result = service.get_meal_timing_suggestions(
            user_id=current_user.user_id,
            target_date=date
        )
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Meal timing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest meal timing"
        )


@router.get("/health")
async def recommendation_health_check():
    """
    Health check for recommendation service
    
    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "Recommendation Service",
        "type": "rule-based",
        "features": [
            "Next meal suggestions",
            "Meal timing suggestions",
            "Confidence scoring",
            "Vietnamese reasons"
        ]
    }