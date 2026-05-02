"""
Analytics Routes
API endpoints for nutrition analytics and progress tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional
import httpx

from app.database import get_db
from app.models.user import User
from app.services import analytics_service
from app.utils.dependencies import get_current_active_user
from app.config import settings


router = APIRouter(
    tags=["Analytics"]
)


# ==========================================
# NUTRITION TRENDS
# ==========================================

@router.get("/nutrition-trends")
def get_nutrition_trends(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Group by day, week, or month"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get nutrition trends over time period
    
    **Parameters:**
    - start_date: Beginning of date range
    - end_date: End of date range (max 1 year from start)
    - group_by: Aggregation level (day/week/month)
    
    **Returns:**
    - Array of nutrition data points grouped by time period
    - Each point contains: date, calories, protein, carbs, fat, meal_count
    
    **Example:**
    ```
    GET /analytics/nutrition-trends?start_date=2024-01-01&end_date=2024-01-31&group_by=day
    ```
    """
    
    try:
        trends = analytics_service.get_nutrition_trends(
            db=db,
            user_id=current_user.user_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        return {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "group_by": group_by,
            "data_points": len(trends),
            "trends": trends
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# WEIGHT PROGRESS
# ==========================================

@router.get("/weight-progress")
def get_weight_progress(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weight progress with trend analysis
    
    **Parameters:**
    - days: Number of days to look back (7-365)
    
    **Returns:**
    - Weight history with dates
    - Starting weight vs current weight
    - Change in kg and percentage
    - Trend analysis (gaining/losing/stable)
    
    **Example:**
    ```
    GET /analytics/weight-progress?days=30
    ```
    """
    
    try:
        progress = analytics_service.get_weight_progress(
            db=db,
            user_id=current_user.user_id,
            days=days
        )
        
        return progress
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# MACRO DISTRIBUTION
# ==========================================

@router.get("/macro-distribution")
def get_macro_distribution(
    target_date: date = Query(default_factory=date.today, description="Date to analyze (default: today)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get macronutrient distribution for a specific date
    
    **Parameters:**
    - target_date: Date to analyze (default: today)
    
    **Returns:**
    - Breakdown of calories from protein/carbs/fat
    - Grams, calories, and percentage for each macro
    
    **Example:**
    ```
    GET /analytics/macro-distribution?target_date=2024-01-15
    ```
    """
    
    distribution = analytics_service.get_macro_distribution(
        db=db,
        user_id=current_user.user_id,
        target_date=target_date
    )
    
    return distribution


# ==========================================
# CALORIE COMPARISON
# ==========================================

@router.get("/calorie-comparison")
def get_calorie_comparison(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Compare actual calories vs target over date range
    
    **Parameters:**
    - start_date: Beginning of comparison period
    - end_date: End of comparison period
    
    **Returns:**
    - Daily comparison of target vs actual calories
    - Overall adherence statistics
    - Days on track vs over/under target
    
    **Requires:** Active goal with calorie target
    
    **Example:**
    ```
    GET /analytics/calorie-comparison?start_date=2024-01-01&end_date=2024-01-31
    ```
    """
    
    comparison = analytics_service.get_calorie_comparison(
        db=db,
        user_id=current_user.user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if "error" in comparison:
        raise HTTPException(status_code=404, detail=comparison["error"])
    
    return comparison


# ==========================================
# MEAL PATTERNS
# ==========================================

@router.get("/meal-patterns")
def get_meal_patterns(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze meal timing patterns
    
    **Parameters:**
    - days: Number of days to analyze (7-90)
    
    **Returns:**
    - Distribution of meals by type (breakfast/lunch/dinner/snack)
    - Average calories per meal type
    - Most frequently logged meal type
    
    **Example:**
    ```
    GET /analytics/meal-patterns?days=30
    ```
    """
    
    patterns = analytics_service.get_meal_patterns(
        db=db,
        user_id=current_user.user_id,
        days=days
    )
    
    return patterns


# ==========================================
# GOAL PROGRESS
# ==========================================

@router.get("/goal-progress")
def get_goal_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get progress towards active goal
    
    **Returns:**
    - Current weight vs starting weight
    - Progress towards target weight
    - Days elapsed and days remaining
    - Progress percentage
    - Status (on_track/behind)
    
    **Requires:** Active goal
    
    **Example:**
    ```
    GET /analytics/goal-progress
    ```
    """
    
    progress = analytics_service.get_goal_progress(
        db=db,
        user_id=current_user.user_id
    )
    
    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])
    
    return progress


# ==========================================
# FOOD FREQUENCY
# ==========================================

@router.get("/food-frequency")
def get_food_frequency(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=5, le=50, description="Number of top foods to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get most frequently logged foods
    
    **Parameters:**
    - days: Number of days to look back (7-90)
    - limit: Number of top foods to return (5-50)
    
    **Returns:**
    - Array of most frequently logged foods
    - Times logged, total calories, average calories per serving
    
    **Example:**
    ```
    GET /analytics/food-frequency?days=30&limit=10
    ```
    """
    
    frequency = analytics_service.get_food_frequency(
        db=db,
        user_id=current_user.user_id,
        days=days,
        limit=limit
    )
    
    return {
        "days_analyzed": days,
        "top_foods": frequency
    }


# ==========================================
# WEEKLY SUMMARY (Bonus)
# ==========================================

@router.get("/weekly-summary")
def get_weekly_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive weekly summary (last 7 days)
    
    Combines multiple analytics endpoints into one summary
    
    **Returns:**
    - Nutrition trends (7 days)
    - Weight change
    - Average calories vs target
    - Meal logging consistency
    
    **Example:**
    ```
    GET /analytics/weekly-summary
    ```
    """
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    # Get nutrition trends
    trends = analytics_service.get_nutrition_trends(
        db=db,
        user_id=current_user.user_id,
        start_date=week_ago,
        end_date=today,
        group_by="day"
    )
    
    # Get weight progress
    weight = analytics_service.get_weight_progress(
        db=db,
        user_id=current_user.user_id,
        days=7
    )
    
    # Get meal patterns
    patterns = analytics_service.get_meal_patterns(
        db=db,
        user_id=current_user.user_id,
        days=7
    )
    
    # Calculate averages
    if trends:
        avg_calories = sum(t['total_calories'] for t in trends) / len(trends)
        days_logged = len(trends)
    else:
        avg_calories = 0
        days_logged = 0
    
    return {
        "period": "last_7_days",
        "start_date": week_ago.strftime('%Y-%m-%d'),
        "end_date": today.strftime('%Y-%m-%d'),
        "summary": {
            "days_logged": days_logged,
            "avg_daily_calories": round(avg_calories, 1),
            "total_meals": patterns.get("total_meals", 0),
            "weight_change_kg": weight.get("change_kg", 0),
            "weight_trend": weight.get("trend", "no_data")
        },
        "daily_nutrition": trends,
        "meal_patterns": patterns.get("patterns", {})
    }


# ==========================================
# AI NUTRITION ADVICE (calls AI Service)
# ==========================================

@router.post("/nutrition-advice")
async def get_nutrition_advice(
    days: int = Query(7, ge=1, le=90, description="Số ngày phân tích"),
    period: str = Query("week", regex="^(day|week|month)$", description="Khung thời gian"),
    language: str = Query("vi", description="Ngôn ngữ (vi/en)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy lời khuyên dinh dưỡng cá nhân hóa từ AI.

    AI phân tích:
    - Tổng quan dinh dưỡng (calories, protein, carbs, fat)
    - Cân nặng + thay đổi theo ngày/tuần/tháng
    - Mẫu bữa ăn
    - Xu hướng

    **Returns:**
    - summary: Tổng kết ngắn
    - highlights: Điểm sáng tích cực
    - concerns: Vấn đề cần cải thiện
    - recommendations: Lời khuyên cụ thể
    - motivational_tip: Động lực
    """
    ai_service_url = settings.AI_SERVICE_URL or "http://ai_service:8001"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ai_service_url}/api/v1/advice/full",
                json={
                    "days": days,
                    "period": period,
                    "language": language
                },
                headers={
                    "Authorization": f"Bearer {current_user.user_id}"
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI Service error: {response.text}"
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="AI Service hiện không khả dụng. Vui lòng thử lại sau."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="AI Service timeout. Vui lòng thử lại."
            )


@router.post("/quick-advice")
async def get_quick_advice(
    target_date: Optional[str] = Query(None, description="Ngày cần lời khuyên (YYYY-MM-DD)"),
    language: str = Query("vi", description="Ngôn ngữ"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy lời khuyên NHANH cho bữa ăn tiếp theo.

    Dựa trên:
    - Calories đã ăn / còn lại hôm nay
    - Protein đã đạt / còn thiếu
    - Gợi ý bữa tiếp theo

    **Returns:**
    - quick_tip: Lời khuyên 1 câu
    - action: Hành động cụ thể
    - why: Tại sao nên làm
    """
    ai_service_url = settings.AI_SERVICE_URL or "http://ai_service:8001"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ai_service_url}/api/v1/advice/quick",
                json={
                    "target_date": target_date,
                    "language": language
                },
                headers={
                    "Authorization": f"Bearer {current_user.user_id}"
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI Service error: {response.text}"
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="AI Service hiện không khả dụng."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="AI Service timeout."
            )


@router.post("/progress-report")
async def get_progress_report(
    period: str = Query("week", regex="^(week|month)$", description="Khung thời gian"),
    language: str = Query("vi", description="Ngôn ngữ"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy báo cáo tiến độ (tuần/tháng).

    **Returns:**
    - overall_score: Điểm tổng thể (0-100)
    - weight_analysis: Phân tích cân nặng
    - nutrition_analysis: Phân tích dinh dưỡng
    - achievements: Thành tựu
    - areas_for_improvement: Cần cải thiện
    - next_week_tips: Tips cho thời gian tới
    - motivation: Động lực
    """
    ai_service_url = settings.AI_SERVICE_URL or "http://ai_service:8001"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ai_service_url}/api/v1/advice/progress",
                json={
                    "period": period,
                    "language": language
                },
                headers={
                    "Authorization": f"Bearer {current_user.user_id}"
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI Service error: {response.text}"
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="AI Service hiện không khả dụng."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="AI Service timeout."
            )