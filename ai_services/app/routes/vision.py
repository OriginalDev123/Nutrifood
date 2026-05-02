"""
Vision API Routes - NutriAI Food Recognition
Endpoint: POST /vision/analyze
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
from pathlib import Path
import tempfile
import logging
import os

from app.services.vision_service import vision_service
from app.utils.image_processing import image_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision Analysis"])


@router.post("/analyze")
async def analyze_food_image(
    image: UploadFile = File(..., description="Ảnh món ăn (JPG/PNG/WEBP, max 10MB)"),
    user_hint: Optional[str] = Form(None, description="Gợi ý tên món (optional)")
):
    """
    **Phân tích ảnh món ăn bằng Gemini Vision AI + Backend Integration**
    
    ### Workflow (Updated with Portion Presets):
    1. User upload ảnh món ăn
    2. Backend validate & compress ảnh
    3. Gọi Gemini Vision API để nhận diện món ăn
    4. Tìm món ăn trong backend database (recipes/foods)
    5. Lấy portion presets từ database
    6. Trả về kết quả + danh sách portion sizes để user chọn
    
    ### Request:
    - **image**: File ảnh (multipart/form-data)
    - **user_hint**: (Optional) Gợi ý tên món để tăng độ chính xác
    
    ### Response:
    ```json
    {
      "is_food": true,
      "food_name": "Ức gà nướng hương thảo",
      "food_type": "recipe",
      "components": ["ức gà", "hương thảo", "tỏi", "dầu ô liu"],
      "description": "Món gà nướng với hương thảo thơm",
      "confidence": 0.85,
      "processing_time_ms": 1234,
      "database_match": {
        "item_type": "recipe",
        "item_id": "uuid",
        "name_vi": "Ức gà nướng hương thảo",
        "calories_per_serving": 280
      },
      "alternatives": [
        {
          "item_type": "recipe",
          "item_id": "uuid-2",
          "name_vi": "Ức gà nướng tiêu",
          "calories_per_serving": 260,
          "match_score": 0.78
        },
        {
          "item_type": "recipe",
          "item_id": "uuid-3",
          "name_vi": "Gà nướng mật ong",
          "calories_per_serving": 320,
          "match_score": 0.65
        }
      ],
      "portion_presets": [
        {
          "preset_id": "uuid",
          "size_label": "small",
          "display_name_vi": "Phần nhỏ",
          "grams": 250,
          "is_default": false
        },
        {
          "preset_id": "uuid",
          "size_label": "medium",
          "display_name_vi": "Phần vừa",
          "grams": 350,
          "is_default": true
        },
        {
          "preset_id": "uuid",
          "size_label": "large",
          "display_name_vi": "Phần lớn",
          "grams": 500,
          "is_default": false
        }
      ]
    }
    ```
    
    ### Error Codes:
    - **400**: Invalid image format hoặc file quá lớn
    - **422**: Không thể xử lý ảnh
    - **429**: Rate limit (quá nhiều requests)
    - **503**: Gemini API không khả dụng
    """
    
    temp_original_path = None
    temp_compressed_path = None
    
    try:
        # === BƯỚC 1: Validate content type ===
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File không phải ảnh hợp lệ"
            )
        
        logger.info(
            f"📤 Nhận request: filename={image.filename}, "
            f"content_type={image.content_type}, hint={user_hint}"
        )
        
        # === BƯỚC 2: Lưu file tạm (original) ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_original_path = Path(temp_file.name)
            content = await image.read()
            temp_file.write(content)
        
        logger.info(f"💾 Saved temp file: {temp_original_path}")
        
        # === BƯỚC 3: Validate ảnh ===
        is_valid, error_message = image_processor.validate_image(temp_original_path)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # === BƯỚC 4: Compress ảnh ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_compressed_path = Path(temp_file.name)
        
        compression_metadata = image_processor.compress_image(
            input_path=temp_original_path,
            output_path=temp_compressed_path
        )
        
        logger.info(
            f"🗜️  Compressed: {compression_metadata['original_size_kb']}KB → "
            f"{compression_metadata['compressed_size_kb']}KB"
        )
        
        # === BƯỚC 5: Gọi Gemini Vision Service ===
        result = await vision_service.analyze_food_image(
            image_path=temp_compressed_path,
            user_hint=user_hint
        )
        
        # === BƯỚC 6: Trả kết quả ===
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (đã có status code & message)
        raise
        
    except ValueError as e:
        # Lỗi từ vision_service hoặc image_processor
        logger.error(f"❌ ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
        
    finally:
        # === CLEANUP: Xóa temp files ===
        if temp_original_path and temp_original_path.exists():
            try:
                os.unlink(temp_original_path)
                logger.debug(f"🗑️  Cleaned up: {temp_original_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete temp file: {e}")
        
        if temp_compressed_path and temp_compressed_path.exists():
            try:
                os.unlink(temp_compressed_path)
                logger.debug(f"🗑️  Cleaned up: {temp_compressed_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete temp file: {e}")


@router.get("/health")
async def vision_health_check():
    """
    Health check cho Vision module
    
    Kiểm tra:
    - Gemini API key configured
    - Service sẵn sàng
    """
    from app.config import settings
    
    if not settings.validate_api_key():
        return {
            "status": "unhealthy",
            "message": "GOOGLE_API_KEY not configured",
            "vision_enabled": False
        }
    
    return {
        "status": "healthy",
        "message": "Vision service ready",
        "vision_enabled": True,
        "model": settings.GEMINI_VISION_MODEL or settings.GEMINI_MODEL
    }