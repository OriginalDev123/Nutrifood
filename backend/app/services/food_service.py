"""
Food Service

Business logic for food operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from uuid import UUID

from app.models.food import Food, FoodServing
from app.schemas.food import FoodCreate


def get_foods(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    verified_only: bool = False  # Mặc định là False để hiển thị cả foods chưa verified
) -> tuple[List[Food], int]:
    """
    Get list of foods with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Number of records to return
        category: Filter by category (optional)
        verified_only: Only return verified foods (default: False)
    
    Returns:
        Tuple of (foods list, total count)
    """
    
    # Base query - chỉ lấy foods chưa bị xóa mềm
    query = db.query(Food).filter(Food.is_deleted == False)
    
    # Apply filters
    if verified_only:
        query = query.filter(Food.is_verified == True)
    
    if category:
        query = query.filter(Food.category == category)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    foods = query.order_by(Food.name_vi).offset(skip).limit(limit).all()
    
    return foods, total


def search_foods(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[Food], int]:
    """
    Search foods by name (full-text search)
    
    Args:
        db: Database session
        query: Search query
        skip: Offset
        limit: Limit
    
    Returns:
        Tuple of (foods list, total count)
    """
    
    # Simple ILIKE search - chỉ tìm foods chưa bị xóa mềm
    search_query = db.query(Food).filter(
        Food.is_deleted == False
    ).filter(
        or_(
            Food.name_vi.ilike(f'%{query}%'),
            Food.name_en.ilike(f'%{query}%')
        )
    )
    
    # Get total
    total = search_query.count()
    
    # Apply pagination with simple ordering
    foods = search_query.order_by(
        Food.name_vi
    ).offset(skip).limit(limit).all()
    
    return foods, total


def get_food_by_id(db: Session, food_id: UUID) -> Optional[Food]:
    """
    Get food by ID with servings
    
    Args:
        db: Database session
        food_id: Food UUID
    
    Returns:
        Food with servings or None
    """
    food = db.query(Food).options(
        joinedload(Food.servings)
    ).filter(Food.food_id == food_id).first()
    
    return food


def get_food_by_barcode(db: Session, barcode: str) -> Optional[Food]:
    """
    Get food by barcode
    
    Args:
        db: Database session
        barcode: Barcode string
    
    Returns:
        Food or None
    """
    food = db.query(Food).options(
        joinedload(Food.servings)
    ).filter(
        Food.barcode == barcode,
        Food.is_deleted == False
    ).first()
    
    return food


def create_food(db: Session, food_data: FoodCreate, created_by: UUID) -> Food:
    """
    Create new food (admin only)
    
    Args:
        db: Database session
        food_data: Food creation data
        created_by: User UUID who creates the food
    
    Returns:
        Created food
    """
    food = Food(
        **food_data.model_dump(),
        description=food_data.description,
        created_by=created_by,
        is_verified=False,  # Requires manual verification
        source="admin"
    )
    
    db.add(food)
    db.commit()
    db.refresh(food)
    
    return food


def get_categories(db: Session) -> List[str]:
    """
    Get all unique food categories
    
    Args:
        db: Database session
    
    Returns:
        List of category names
    """
    categories = db.query(Food.category).filter(
        Food.is_deleted == False
    ).distinct().all()
    return [cat[0] for cat in categories if cat[0]]