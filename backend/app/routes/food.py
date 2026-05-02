"""
Food Routes

API endpoints for food database
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.schemas.food import (
    FoodResponse, FoodWithServings, FoodSearchResponse, FoodCreate
)
from app.services.food_service import (
    get_foods, search_foods, get_food_by_id, get_food_by_barcode,
    create_food, get_categories
)
from app.utils.dependencies import get_current_active_user, require_admin
from app.models.user import User
from app.models.food import PortionPreset

# Create router
router = APIRouter(
    prefix="/foods",
    tags=["Foods"]
)


# ==========================================
# PUBLIC ENDPOINTS
# ==========================================

@router.get("", response_model=FoodSearchResponse)
async def list_foods(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    verified_only: bool = Query(False, description="Only show verified foods"),
    db: Session = Depends(get_db)
):
    """
    Get list of foods with pagination
    
    - Default: Returns all (verified and unverified) foods
    - Can filter by category
    - Supports pagination
    """
    foods, total = get_foods(db, skip, limit, category, verified_only)
    
    return FoodSearchResponse(
        total=total,
        foods=[FoodResponse.model_validate(food) for food in foods],
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/search", response_model=FoodSearchResponse)
async def search_foods_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search foods by name (Vietnamese or English)
    
    - Uses full-text search with PostgreSQL GIN index
    - Searches both name_vi and name_en
    - Returns verified foods only
    
    **Example**: `?q=cơm` or `?q=rice`
    """
    foods, total = search_foods(db, q, skip, limit)
    
    return FoodSearchResponse(
        total=total,
        foods=[FoodResponse.model_validate(food) for food in foods],
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/categories", response_model=List[str])
async def list_categories(db: Session = Depends(get_db)):
    """
    Get all food categories
    
    Returns list of unique categories in the database
    """
    return get_categories(db)


@router.get("/barcode/{barcode}", response_model=FoodWithServings)
async def lookup_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):
    """
    Lookup food by barcode
    
    - Used for barcode scanner feature
    - Returns food with all servings
    """
    food = get_food_by_barcode(db, barcode)
    
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found for this barcode"
        )
    
    return food


@router.get("/{food_id}", response_model=FoodWithServings)
async def get_food_detail(
    food_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get food details with servings
    
    - Returns complete food information
    - Includes all serving options
    """
    food = get_food_by_id(db, food_id)
    
    if not food or food.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Món ăn không tồn tại hoặc đã bị gỡ bỏ"
        )
    
    return food


@router.get("/{food_id}/portions")
async def get_food_portion_presets(
    food_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get portion presets for a food
    
    Returns list of available portion sizes (small/medium/large)
    for Vision AI integration.
    
    **Example response:**
    ```json
    [
        {
            "preset_id": "uuid",
            "size_label": "single",
            "display_name_vi": "1 quả",
            "display_name_en": "1 piece",
            "unit_type": "piece",
            "unit_display_vi": "quả",
            "grams": 50,
            "is_default": true,
            "sort_order": 1
        }
    ]
    ```
    """
    # Check if food exists
    food = get_food_by_id(db, food_id)
    if not food or food.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    # Get portion presets
    presets = db.query(PortionPreset).filter(
        PortionPreset.food_id == food_id
    ).order_by(PortionPreset.sort_order).all()
    
    # Convert to dict
    return [preset.to_dict() for preset in presets]


# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@router.post("", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def create_food_endpoint(
    food_data: FoodCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create new food (Admin only)
    
    - Requires admin authentication
    - Creates unverified food (requires manual verification)
    """
    food = create_food(db, food_data, current_user.user_id)
    return food