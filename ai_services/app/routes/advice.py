"""
Nutrition Advice API Routes
Endpoints cho AI-powered nutrition advice:
- POST /advice/full - Lời khuyên đầy đủ dựa trên analytics
- POST /advice/quick - Lời khuyên nhanh cho bữa tiếp theo
- POST /advice/progress - Báo cáo tiến độ (tuần/tháng)
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
import logging

from app.services.nutrition_advice_service import get_nutrition_advice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advice", tags=["Nutrition Advice"])


# === REQUEST SCHEMAS ===

class FullAdviceRequest(BaseModel):
    """Request cho full nutrition advice."""

    days: int = Field(
        7,
        ge=1,
        le=90,
        description="Số ngày phân tích (1-90). 7 = tuần, 30 = tháng"
    )
    period: Literal["day", "week", "month"] = Field(
        "week",
        description="Khung thời gian phân tích"
    )
    language: str = Field(
        "vi",
        description="Ngôn ngữ trả lời (vi/en)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "days": 7,
                "period": "week",
                "language": "vi"
            }
        }


class QuickAdviceRequest(BaseModel):
    """Request cho quick advice."""

    target_date: Optional[str] = Field(
        None,
        description="Ngày cần lời khuyên (ISO format, default: hôm nay)"
    )
    language: str = Field(
        "vi",
        description="Ngôn ngữ trả lời (vi/en)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_date": "2026-04-11",
                "language": "vi"
            }
        }


class ProgressReportRequest(BaseModel):
    """Request cho progress report."""

    period: Literal["week", "month"] = Field(
        "week",
        description="Khung thời gian báo cáo"
    )
    language: str = Field(
        "vi",
        description="Ngôn ngữ trả lời (vi/en)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "period": "week",
                "language": "vi"
            }
        }


# === RESPONSE SCHEMAS ===

class NutritionAdviceResponse(BaseModel):
    """Response cho full nutrition advice."""

    summary: str = Field(description="Tổng kết ngắn 2-3 câu")
    highlights: list[str] = Field(description="Điểm sáng tích cực")
    concerns: list[str] = Field(description="Vấn đề cần lưu ý")
    recommendations: list[str] = Field(description="Lời khuyên cụ thể")
    motivational_tip: str = Field(description="Động lực ngắn")
    period: str = Field(description="Khung thời gian phân tích")
    days_analyzed: int = Field(description="Số ngày đã phân tích")
    generated_at: str = Field(description="Thời gian tạo")


class QuickAdviceResponse(BaseModel):
    """Response cho quick advice."""

    quick_tip: str = Field(description="Lời khuyên 1 câu")
    action: str = Field(description="Hành động cụ thể")
    why: str = Field(description="Tại sao nên làm")
    date: str = Field(description="Ngày áp dụng")
    generated_at: str = Field(description="Thời gian tạo")


class ProgressReportResponse(BaseModel):
    """Response cho progress report."""

    period: str = Field(description="Khung thời gian báo cáo")
    overall_score: int = Field(description="Điểm tổng thể (0-100)")
    summary: str = Field(description="Tổng kết 2-3 câu")
    weight_analysis: dict = Field(description="Phân tích cân nặng")
    nutrition_analysis: dict = Field(description="Phân tích dinh dưỡng")
    achievements: list[str] = Field(description="Thành tựu đạt được")
    areas_for_improvement: list[str] = Field(description="Cần cải thiện")
    next_week_tips: list[str] = Field(description="Tips cho thời gian tới")
    motivation: str = Field(description="Động lực")
    days_analyzed: int = Field(description="Số ngày đã phân tích")
    generated_at: str = Field(description="Thời gian tạo")


# === ENDPOINTS ===

@router.post("/full", response_model=NutritionAdviceResponse)
async def get_full_nutrition_advice(
    request: FullAdviceRequest,
    authorization: str = Header(..., description="Bearer JWT token")
):
    """
    **Lời khuyên dinh dưỡng đầy đủ**

    Phân tích toàn diện dựa trên:
    - Tổng quan dinh dưỡng (calories, protein, carbs, fat)
    - Cân nặng + thay đổi theo ngày/tuần/tháng
    - Mẫu bữa ăn
    - Xu hưỏng

    ### Use Cases:
    1. Hiển thị trên trang Analytics/Phân tích
    2. Panel lời khuyên AI trong dashboard
    3. Báo cáo tuần/tháng

    ### Request:
    ```json
    {
        "days": 7,
        "period": "week",
        "language": "vi"
    }
    ```

    ### Response:
    ```json
    {
        "summary": "Bạn đã kiểm soát tốt lượng calories trong tuần qua...",
        "highlights": [
            "Protein đạt 95% mục tiêu",
            "Ăn uống đều đặn 3 bữa chính"
        ],
        "concerns": [
            "Carbs hơi cao vào cuối tuần"
        ],
        "recommendations": [
            "💡 Giảm cơm trắng buổi tối, thay bằng rau trộn"
        ],
        "motivational_tip": "Tiếp tục phấn đấu!",
        "period": "week",
        "days_analyzed": 7,
        "generated_at": "2026-04-11T10:30:00"
    }
    ```
    """

    # Extract token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization.replace("Bearer ", "")

    try:
        service = get_nutrition_advice_service()
        result = await service.generate_full_advice(
            user_token=token,
            days=request.days,
            period=request.period,
            language=request.language
        )

        return result

    except Exception as e:
        logger.error(f"❌ Full advice error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tạo lời khuyên: {str(e)}"
        )


@router.post("/quick", response_model=QuickAdviceResponse)
async def get_quick_advice(
    request: QuickAdviceRequest,
    authorization: str = Header(..., description="Bearer JWT token")
):
    """
    **Lời khuyên NHANH cho bữa ăn tiếp theo**

    Dựa trên dữ liệu hôm nay:
    - Calories đã ăn / còn lại
    - Protein đã đạt / còn thiếu
    - Bữa ăn tiếp theo nên ăn gì

    ### Use Cases:
    1. Gợi ý bữa ăn tiếp theo khi user mở app
    2. Quick tip khi log meal
    3. Notification reminders

    ### Request:
    ```json
    {
        "target_date": "2026-04-11",
        "language": "vi"
    }
    ```

    ### Response:
    ```json
    {
        "quick_tip": "Còn 450kcal cho bữa tối - ưu tiên protein!",
        "action": "Chọn 150g cá hồi nướng + rau trộn",
        "why": "Bạn đã thiếu protein 30g, cá hồi là nguồn protein tuyệt vời",
        "date": "2026-04-11",
        "generated_at": "2026-04-11T18:00:00"
    }
    ```
    """

    # Extract token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization.replace("Bearer ", "")

    # Parse date
    target_date = None
    if request.target_date:
        try:
            target_date = date.fromisoformat(request.target_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
            )

    try:
        service = get_nutrition_advice_service()
        result = await service.generate_quick_advice(
            user_token=token,
            target_date=target_date,
            language=request.language
        )

        return result

    except Exception as e:
        logger.error(f"❌ Quick advice error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tạo lời khuyên nhanh: {str(e)}"
        )


@router.post("/progress", response_model=ProgressReportResponse)
async def get_progress_report(
    request: ProgressReportRequest,
    authorization: str = Header(..., description="Bearer JWT token")
):
    """
    **Báo cáo tiến độ (tuần/tháng)**

    Phân tích:
    - Tiến độ cân nặng so với mục tiêu
    - Điểm tổng thể (overall score)
    - Thành tựu & Cần cải thiện
    - Tips cho thời gian tới

    ### Use Cases:
    1. Hiển thị trên trang Goal/Progress
    2. Report cuối tuần/tháng
    3. Achievement badges

    ### Request:
    ```json
    {
        "period": "week",
        "language": "vi"
    }
    ```

    ### Response:
    ```json
    {
        "period": "week",
        "overall_score": 85,
        "summary": "Tuần này bạn đã đạt được nhiều tiến bộ...",
        "weight_analysis": {
            "progress": "Giảm 0.5kg trong tuần",
            "on_track": true,
            "reasoning": "Tốc độ giảm phù hợp với mục tiêu"
        },
        "nutrition_analysis": {
            "calorie_adherence": "85% ngày tuân thủ mục tiêu",
            "protein_quality": "Tốt - đạt 90% TB",
            "consistency": "Ăn đều 3 bữa chính"
        },
        "achievements": [
            "Giảm 0.5kg",
            "Tuân thủ 6/7 ngày"
        ],
        "areas_for_improvement": [
            "Cuối tuần ăn nhiều hơn mục tiêu"
        ],
        "next_week_tips": [
            "Chuẩn bị meal prep cuối tuần"
        ],
        "motivation": "Bạn đang làm rất tốt!",
        "days_analyzed": 7,
        "generated_at": "2026-04-11T10:00:00"
    }
    ```
    """

    # Extract token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization.replace("Bearer ", "")

    try:
        service = get_nutrition_advice_service()
        result = await service.generate_progress_report(
            user_token=token,
            period=request.period,
            language=request.language
        )

        return result

    except Exception as e:
        logger.error(f"❌ Progress report error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tạo báo cáo: {str(e)}"
        )


@router.get("/health")
async def advice_health_check():
    """
    Health check cho Nutrition Advice module.
    """
    try:
        service = get_nutrition_advice_service()
        return {
            "status": "healthy",
            "service": "NutritionAdviceService",
            "message": "Sẵn sàng tạo lời khuyên dinh dưỡng"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
