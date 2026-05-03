"""
Health Profile Routes
Endpoints for managing user health profile (dietary preferences, allergies, health conditions)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.user_health_profile import UserHealthProfile
from app.schemas.health_profile import HealthProfileInput, HealthProfileResponse
from app.utils.dependencies import get_current_active_user


router = APIRouter(prefix="/users/me/health-profile", tags=["Health Profile"])


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _get_or_create_health_profile(db: Session, user_id) -> dict:
    """
    Get user's health profile or return empty profile.
    """
    profile = db.query(UserHealthProfile).filter(
        UserHealthProfile.user_id == user_id
    ).first()
    
    if not profile:
        return {
            "health_conditions": [],
            "food_allergies": [],
            "dietary_preferences": [],
            "updated_at": None,
        }
    
    return {
        "health_conditions": profile.health_conditions or [],
        "food_allergies": profile.food_allergies or [],
        "dietary_preferences": profile.dietary_preferences or [],
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _create_or_update_health_profile(db: Session, user_id, health_data: dict) -> dict:
    """
    Create or update user's health profile.
    """
    profile = db.query(UserHealthProfile).filter(
        UserHealthProfile.user_id == user_id
    ).first()
    
    if not profile:
        # Create new profile
        profile = UserHealthProfile(
            user_id=user_id,
            health_conditions=health_data.get("health_conditions", []),
            food_allergies=health_data.get("food_allergies", []),
            dietary_preferences=health_data.get("dietary_preferences", []),
        )
        db.add(profile)
    else:
        # Update existing profile
        profile.health_conditions = health_data.get("health_conditions", [])
        profile.food_allergies = health_data.get("food_allergies", [])
        profile.dietary_preferences = health_data.get("dietary_preferences", [])
    
    db.commit()
    db.refresh(profile)
    
    return {
        "health_conditions": profile.health_conditions or [],
        "food_allergies": profile.food_allergies or [],
        "dietary_preferences": profile.dietary_preferences or [],
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


# ==========================================
# ROUTES
# ==========================================

@router.get("", response_model=HealthProfileResponse)
def get_my_health_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's health profile
    
    Returns the user's health conditions, food allergies, and dietary preferences.
    If no health profile exists, returns empty lists.
    
    **Returns:**
    - health_conditions: List of health conditions
    - food_allergies: List of food allergies
    - dietary_preferences: List of dietary preferences
    """
    return _get_or_create_health_profile(db, current_user.user_id)


@router.put("", response_model=HealthProfileResponse)
def update_my_health_profile(
    health_profile: HealthProfileInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's health profile
    
    Replaces the entire health profile with the provided data.
    
    **Body:**
    - health_conditions: List of health conditions (e.g., ["Tiểu đường", "Huyết áp cao"])
    - food_allergies: List of food allergies (e.g., ["Hải sản", "Đậu phộng"])
    - dietary_preferences: List of dietary preferences (e.g., ["Low Carb", "Keto", "Eat Clean"])
    
    **Returns:**
    - Updated health profile
    """
    health_data = {
        "health_conditions": health_profile.health_conditions or [],
        "food_allergies": health_profile.food_allergies or [],
        "dietary_preferences": health_profile.dietary_preferences or [],
    }
    
    return _create_or_update_health_profile(db, current_user.user_id, health_data)


@router.patch("", response_model=HealthProfileResponse)
def patch_my_health_profile(
    health_profile: HealthProfileInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Partially update current user's health profile
    
    Only updates fields that are provided (non-empty lists).
    Empty lists will be preserved, not cleared.
    
    **Body:**
    - health_conditions: List of health conditions
    - food_allergies: List of food allergies
    - dietary_preferences: List of dietary preferences
    
    **Returns:**
    - Updated health profile
    """
    existing = _get_or_create_health_profile(db, current_user.user_id)
    
    health_data = {
        "health_conditions": health_profile.health_conditions if health_profile.health_conditions else existing["health_conditions"],
        "food_allergies": health_profile.food_allergies if health_profile.food_allergies else existing["food_allergies"],
        "dietary_preferences": health_profile.dietary_preferences if health_profile.dietary_preferences else existing["dietary_preferences"],
    }
    
    return _create_or_update_health_profile(db, current_user.user_id, health_data)
