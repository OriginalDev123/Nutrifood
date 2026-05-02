"""
Nutrition API Routes - Fuzzy Search cho Vietnamese Food
Endpoint: POST /nutrition/search
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, model_validator
from typing import Optional
import logging

from app.database import get_db
from app.services.nutrition_service import nutrition_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition", tags=["Nutrition Search"])


# === REQUEST/RESPONSE SCHEMAS ===

class NutritionSearchRequest(BaseModel):
    """Request schema cho nutrition search"""
    
    food_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Tên món ăn cần tìm (VD: 'pho bo', 'Phở bò', 'beef pho')"
    )
    return_top_k: bool = Field(
        False,
        description="False = best match, True = top 3 candidates"
    )
    limit: Optional[int] = Field(
        3,
        ge=1,
        le=10,
        description="Số lượng kết quả trả về (alias cho top_k, mặc định 3)"
    )
    threshold: Optional[int] = Field(
        None,  # None = use dynamic threshold based on query length
        ge=0,
        le=100,
        description="Minimum similarity score (0-100). If not provided, uses dynamic threshold based on query length"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "food_name": "pho bo",
                "return_top_k": False,
                "threshold": 80
            }
        }


class CalculateNutritionRequest(BaseModel):
    """Request schema cho calculate nutrition (flexible - accepts food_id OR food_name)"""
    
    food_id: Optional[str] = Field(None, description="UUID của món ăn")
    food_name: Optional[str] = Field(None, description="Tên món ăn (alternative to food_id)")
    portion_grams: float = Field(..., gt=0, description="Khối lượng (grams)")
    
    @model_validator(mode='after')
    def check_food_identifier(self) -> 'CalculateNutritionRequest':
        if not self.food_id and not self.food_name:
            raise ValueError("Must provide either 'food_id' or 'food_name'")
        return self
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "food_id": "123e4567-e89b-12d3-a456-426614174000",
                    "portion_grams": 500
                },
                {
                    "food_name": "Cơm trắng",
                    "portion_grams": 200
                }
            ]
        }


# === ENDPOINTS ===

@router.post("/search")
async def search_food(
    request: NutritionSearchRequest,
    db: Session = Depends(get_db)
):
    """
    **Tìm món ăn trong database bằng fuzzy matching**
    
    ### Use Cases:
    1. **Best Match Mode** (`return_top_k=false`):
       - User upload ảnh → AI Vision nhận diện → "Phở bò"
       - Backend search database với fuzzy matching
       - Return món ăn khớp nhất (nếu similarity ≥ threshold)
    
    2. **Top K Mode** (`return_top_k=true`):
       - User nhập tên món không chắc chắn
       - Return top 3 kết quả gần nhất
       - User chọn đúng món
    
    ### Fuzzy Matching Features:
    - Xử lý Vietnamese diacritics ("pho" matches "Phở")
    - Word order independence ("Phở bò tái" matches "Bò tái phở")
    - Synonym expansion ("cha gio" matches "nem rán")
    - Partial matching ("Cơm tấm" matches "Cơm tấm sườn")
    
    ### Request:
    ```json
    {
      "food_name": "pho bo",
      "return_top_k": false,
      "threshold": 80
    }
    ```
    
    ### Response (Best Match):
    ```json
    {
      "matched": true,
      "food": {
        "food_id": "uuid",
        "name_vi": "Phở bò",
        "name_en": "Beef Pho",
        "nutrition": {...}
      },
      "similarity_score": 95.2,
      "matched_name": "Phở bò / Beef Pho",
      "search_time_ms": 45
    }
    ```
    
    ### Response (Top K):
    ```json
    {
      "matched": true,
      "candidates": [
        {
          "food": {...},
          "similarity_score": 95.2,
          "matched_name": "Phở bò"
        },
        {
          "food": {...},
          "similarity_score": 87.5,
          "matched_name": "Phở gà"
        }
      ],
      "search_time_ms": 52
    }
    ```
    
    ### Error Codes:
    - **400**: Invalid request (empty food_name)
    - **503**: Database connection error
    """
    
    try:
        logger.info(
            f"➡️  Search request: '{request.food_name}' "
            f"(top_k={request.return_top_k}, threshold={request.threshold})"
        )
        
        # Call service (use limit if provided, otherwise default to 3)
        result = nutrition_service.search_food(
            db=db,
            food_name=request.food_name,
            return_top_k=request.return_top_k,
            threshold=request.threshold,
            top_k=request.limit if request.limit else 3
        )
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/calculate-nutrition")
async def calculate_nutrition(
    request: CalculateNutritionRequest,
    db: Session = Depends(get_db)
):
    """
    **Tính nutrition cho portion cụ thể**
    
    ### Use Case:
    User đã chọn món ăn, giờ cần tính nutrition cho khẩu phần thực tế
    
    ### Request:
    ```json
    {
      "food_id": "123e4567-e89b-12d3-a456-426614174000",
      "portion_grams": 500
    }
    ```
    
    ### Response:
    ```json
    {
      "food_id": "uuid",
      "food_name": "Phở bò",
      "portion_grams": 500,
      "nutrition": {
        "calories": 600,
        "protein_g": 42.5,
        "carbs_g": 75,
        "fat_g": 15,
        ...
      }
    }
    ```
    """
    
    try:
        # Get food by ID or name
        if request.food_id:
            food = nutrition_service.get_food_by_id(db, request.food_id)
            
            if not food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food not found: {request.food_id}"
                )
        else:
            # Search by name using fuzzy matching
            search_result = nutrition_service.search_food(
                db=db,
                food_name=request.food_name,
                return_top_k=False,
                threshold=70
            )
            
            if not search_result.get('matched'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food not found: {request.food_name}"
                )
            
            food = search_result['food']
        
        # Calculate nutrition for portion
        nutrition = nutrition_service.calculate_nutrition_for_portion(
            food_dict=food,
            portion_grams=request.portion_grams
        )
        
        return {
            "food_id": food["food_id"],
            "food_name": food["name_vi"],
            "portion_grams": request.portion_grams,
            "nutrition": nutrition
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Calculate nutrition error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def nutrition_health_check(db: Session = Depends(get_db)):
    """
    Health check cho Nutrition module
    
    Kiểm tra:
    - Database connection
    - Number of foods in database
    """
    try:
        from app.database import Food
        
        # Count foods
        food_count = db.query(Food).filter(
            Food.is_deleted == False
        ).count()
        
        return {
            "status": "healthy",
            "message": "Nutrition search ready",
            "database_connected": True,
            "foods_count": food_count
        }
    
    except Exception as e:
        logger.error(f"❌ Nutrition health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "database_connected": False
        }


@router.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Thống kê database
    
    Returns:
    - Số lượng foods theo category
    - Verified vs unverified
    """
    try:
        from app.database import Food
        from sqlalchemy import func
        
        # Total foods
        total = db.query(Food).filter(Food.is_deleted == False).count()
        
        # By category
        by_category = db.query(
            Food.category,
            func.count(Food.food_id).label('count')
        ).filter(
            Food.is_deleted == False
        ).group_by(Food.category).all()
        
        # Verified
        verified = db.query(Food).filter(
            Food.is_deleted == False,
            Food.is_verified == True
        ).count()
        
        return {
            "total_foods": total,
            "verified_foods": verified,
            "unverified_foods": total - verified,
            "by_category": [
                {"category": cat, "count": count}
                for cat, count in by_category
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )