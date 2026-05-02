"""
User Goals Routes
Endpoints for managing user goals and nutrition targets
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserGoalCreate, UserGoalResponse, UserGoalUpdate
from app.services import goal_service
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/users/me/goals", tags=["User Goals"])


@router.post("", response_model=UserGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: UserGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new goal for current user
    
    - Automatically deactivates any existing active goals
    - Calculates calorie targets if not provided (using BMR/TDEE)
    - Calculates macro targets (protein, carbs, fat) based on goal type
    - Only one active goal allowed per user
    
    **Goal Types:**
    - `weight_loss`: Calorie deficit (-500 cal/day, ~0.5kg/week)
    - `weight_gain`: Calorie surplus (+500 cal/day, ~0.5kg/week)
    - `maintain`: Maintenance calories (TDEE)
    - `healthy_lifestyle`: Balanced nutrition (TDEE)
    
    **Activity Levels:**
    - `sedentary`: Little/no exercise
    - `lightly_active`: Exercise 1-3 days/week
    - `moderately_active`: Exercise 3-5 days/week
    - `very_active`: Exercise 6-7 days/week
    - `extra_active`: Physical job or 2x/day training
    """
    try:
        new_goal = goal_service.create_user_goal(db, current_user.user_id, goal_data)
        return new_goal
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[UserGoalResponse])
def get_my_goals(
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all goals for current user
    
    - Returns goals sorted by created_at (newest first)
    - Use `active_only=true` to get only active goal
    """
    goals = goal_service.get_user_goals(db, current_user.user_id, active_only)
    return goals


@router.get("/active", response_model=UserGoalResponse)
def get_active_goal(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's active goal
    
    Returns 404 if no active goal found
    """
    active_goal = goal_service.get_active_goal(db, current_user.user_id)
    
    if not active_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal found. Please create a goal first."
        )
    
    return active_goal


@router.patch("/{goal_id}", response_model=UserGoalResponse)
def update_goal(
    goal_id: UUID = Path(..., description="Mã định danh mục tiêu (UUID)"),
    goal_update: UserGoalUpdate = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific goal
    
    - Can update any field (partial update)
    - Goal must belong to current user
    """
    
    try:
        updated_goal = goal_service.update_goal(
        db, 
        current_user.user_id, 
        goal_id,
        goal_update
        )
        return updated_goal
    except ValueError as e:
        msg = str(e)
        if msg == "Goal not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )


@router.put("/{goal_id}", response_model=UserGoalResponse)
def replace_goal(
    goal_id: UUID,
    goal_data: UserGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Full update/replace a goal
    
    - Replaces all goal fields with new values
    - Goal must belong to current user
    - If goal was active, remains active
    """
    from app.models.user import UserGoal
    
    # Find existing goal
    goal = db.query(UserGoal).filter(
        UserGoal.goal_id == goal_id,
        UserGoal.user_id == current_user.user_id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    try:
        goal_service.validate_goal_create_payload(goal_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Update all fields
    goal.goal_type = goal_data.goal_type
    goal.target_weight_kg = goal_data.target_weight_kg
    goal.target_date = goal_data.target_date
    goal.daily_calorie_target = goal_data.daily_calorie_target
    goal.protein_target_g = goal_data.protein_target_g
    goal.carbs_target_g = goal_data.carbs_target_g
    goal.fat_target_g = goal_data.fat_target_g
    
    db.commit()
    db.refresh(goal)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_goal(
    goal_id: UUID = Path(..., description="Mã định danh mục tiêu (UUID)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a goal (soft delete)
    
    - Sets is_active = False instead of deleting
    - Goal must belong to current user
    """
    
    try:
        # Service sẽ xử lý logic soft_delete()
        goal_service.deactivate_goal(db, current_user.user_id, goal_id)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )