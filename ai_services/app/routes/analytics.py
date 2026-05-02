"""
Analytics Routes (Task 10)

API endpoints for AI-powered analytics insights
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, Field

from app.services.analytics_insights_service import get_analytics_insights_service, AnalyticsInsightsService


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics Insights"]
)


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class AnalyticsInsightsRequest(BaseModel):
    """Request model for analytics insights"""
    
    days: Optional[int] = Field(7, ge=7, le=90, description="Number of days to analyze")
    language: Optional[str] = Field("vi", pattern="^(vi|en)$", description="Language for insights (vi/en)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "days": 7,
                "language": "vi"
            }
        }


class WeeklyInsightsResponse(BaseModel):
    """Response model for weekly insights"""
    
    period: str = Field(..., description="Analysis period")
    summary: str = Field(..., description="Overall summary")
    highlights: list = Field(..., description="Positive achievements")
    concerns: list = Field(..., description="Areas for improvement")
    recommendations: list = Field(..., description="Actionable recommendations")
    generated_at: str = Field(..., description="Generated timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "last_7_days",
                "summary": "Tuần qua bạn duy trì tốt chế độ ăn, trung bình 1800 kcal/ngày",
                "highlights": [
                    "Duy trì ăn đủ 3 bữa chính mỗi ngày",
                    "Protein ổn định ở mức 80-90g/ngày",
                    "Giảm được 0.5kg so với đầu tuần"
                ],
                "concerns": [
                    "2 ngày vượt mục tiêu calories (thứ 5 và thứ 7)",
                    "Carbs hơi cao vào buổi tối"
                ],
                "recommendations": [
                    "Giảm carbs buổi tối xuống còn 50-60g",
                    "Tăng rau xanh ở bữa trưa",
                    "Uống đủ 2L nước mỗi ngày"
                ],
                "generated_at": "2026-03-05T10:30:00"
            }
        }


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/weekly-insights", response_model=WeeklyInsightsResponse)
async def get_weekly_insights(
    language: str = "vi",
    authorization: Optional[str] = Header(None),
    service: AnalyticsInsightsService = Depends(get_analytics_insights_service)
):
    """
    Get AI-powered weekly nutrition insights
    
    **Features:**
    - Analyzes last 7 days of nutrition data
    - Generates natural language summary
    - Highlights achievements and concerns
    - Provides actionable recommendations
    
    **Requires:** Valid user JWT token in Authorization header
    
    **Example Request:**
    ```
    POST /analytics/weekly-insights?language=vi
    Headers:
      Authorization: Bearer <jwt_token>
    ```
    
    **Example Response:**
    ```json
    {
      "period": "last_7_days",
      "summary": "Tuần qua bạn duy trì tốt...",
      "highlights": ["Achievement 1", "Achievement 2"],
      "concerns": ["Concern 1"],
      "recommendations": ["Recommendation 1", "Recommendation 2"],
      "generated_at": "2026-03-05T10:30:00"
    }
    ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Provide 'Bearer <token>'"
        )
    
    # Extract token
    token = authorization.replace("Bearer ", "")
    
    try:
        # Generate insights
        insights = await service.generate_weekly_insights(
            user_token=token,
            language=language
        )
        
        # Remove raw data from response (too large)
        insights.pop("data", None)
        
        return insights
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@router.post("/goal-insights")
async def get_goal_progress_insights(
    language: str = "vi",
    authorization: Optional[str] = Header(None),
    service: AnalyticsInsightsService = Depends(get_analytics_insights_service)
):
    """
    Get AI-powered goal progress insights
    
    **Features:**
    - Analyzes goal progress
    - Assesses current status
    - Provides motivational feedback
    - Suggests adjustments if needed
    
    **Requires:** 
    - Valid user JWT token
    - Active goal in backend
    
    **Example Request:**
    ```
    POST /analytics/goal-insights?language=vi
    Headers:
      Authorization: Bearer <jwt_token>
    ```
    
    **Example Response:**
    ```json
    {
      "status_message": "Bạn đang trên đà đạt mục tiêu",
      "progress_assessment": "Sau 15 ngày, bạn đã giảm 2kg...",
      "recommendations": [
        "Tiếp tục duy trì chế độ hiện tại",
        "Tăng protein lên 100g/ngày"
      ],
      "motivation": "Bạn đang làm rất tốt, cố gắng lên!",
      "generated_at": "2026-03-05T10:30:00"
    }
    ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        insights = await service.generate_goal_progress_insights(
            user_token=token,
            language=language
        )
        
        insights.pop("data", None)
        
        return insights
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating goal insights: {str(e)}")


@router.post("/nutrition-trend-insights")
async def get_nutrition_trend_insights(
    days: int = 30,
    language: str = "vi",
    authorization: Optional[str] = Header(None),
    service: AnalyticsInsightsService = Depends(get_analytics_insights_service)
):
    """
    Get AI-powered nutrition trend analysis
    
    **Features:**
    - Analyzes nutrition patterns over time
    - Detects trends (increasing/decreasing/stable)
    - Identifies consistency issues
    - Recommends improvements
    
    **Parameters:**
    - days: Number of days to analyze (7-90, default: 30)
    - language: Output language (vi/en, default: vi)
    
    **Requires:** Valid user JWT token
    
    **Example Request:**
    ```
    POST /analytics/nutrition-trend-insights?days=30&language=vi
    Headers:
      Authorization: Bearer <jwt_token>
    ```
    
    **Example Response:**
    ```json
    {
      "period_days": 30,
      "analysis": {
        "avg_calories": 1850.2,
        "avg_protein": 85.5,
        "calorie_trend": "decreasing",
        "protein_trend": "stable",
        "consistent_days": 25
      },
      "insights": "Trong 30 ngày qua, lượng calories có xu hướng giảm nhẹ...",
      "generated_at": "2026-03-05T10:30:00"
    }
    ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
    
    if days < 7 or days > 90:
        raise HTTPException(
            status_code=400,
            detail="days must be between 7 and 90"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        insights = await service.generate_nutrition_trend_insights(
            user_token=token,
            days=days,
            language=language
        )
        
        insights.pop("data", None)
        
        return insights
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trend insights: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for analytics service
    
    **Returns:**
    - Service status
    - Available endpoints
    
    **Example:**
    ```
    GET /analytics/health
    ```
    """
    return {
        "status": "healthy",
        "service": "Analytics Insights Service",
        "version": "1.0.0",
        "endpoints": [
            "POST /analytics/weekly-insights",
            "POST /analytics/goal-insights",
            "POST /analytics/nutrition-trend-insights",
            "GET /analytics/health"
        ],
        "features": [
            "AI-powered weekly insights",
            "Goal progress analysis",
            "Nutrition trend detection",
            "Multi-language support (vi/en)"
        ]
    }
