"""
Authentication Routes

API endpoints for user authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy.orm import joinedload, selectinload
from app.limiter import limiter

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest, UserComplete
from app.services import create_user, authenticate_user, get_user_by_id
from app.utils.security import create_access_token, create_refresh_token, decode_token, verify_token_type
from app.utils.dependencies import get_current_active_user
from app.models.user import User
from app.config import settings

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================
# REGISTRATION
# ==========================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    _ = request,
    """
    Register new user account
    
    - Creates user with hashed password
    - Creates default user profile
    - Returns user data (without password)
    
    **Note**: Use /auth/login to get authentication tokens
    """
    user = create_user(db, user_data)
    return user


# ==========================================
# LOGIN
# ==========================================

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute/ip")
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    _ = request,
    """
    Authenticate user and return JWT tokens
    
    - Validates email and password
    - Returns access token (15 min) and refresh token (7 days)
    - Updates last_login timestamp
    
    **Token Usage**:
    - Include in requests: `Authorization: Bearer {access_token}`
    - Refresh when expired: POST /auth/refresh with refresh_token
    """
    
    # Authenticate user
    user = authenticate_user(db, login_data)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.email}
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.user_id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


# ==========================================
# REFRESH TOKEN
# ==========================================

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    _ = request,
    """
    Refresh access token using refresh token
    
    - Validates refresh token
    - Issues new access token
    - Returns new token pair
    
    **Request Body**: `{"refresh_token": "your_refresh_token"}`
    """
    
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    try:
        from uuid import UUID
        user_id = UUID(user_id_str)
        user = get_user_by_id(db, user_id)
    except (ValueError, HTTPException):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Create new tokens
    new_access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.email}
    )
    
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.user_id)}
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ==========================================
# GET CURRENT USER
# ==========================================

@router.get("/me", response_model=UserComplete)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    
    - Returns user data with profile and active goal
    - Requires valid access token
    """
    
    # Eager load relationships
    from sqlalchemy.orm import joinedload
    
    user = db.query(User).options(
        joinedload(User.profile),
        selectinload(User.goals)
    ).filter(User.user_id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    active_goal = next(
        (goal for goal in user.goals if goal.is_active and not goal.is_deleted),
        None
    )
    
    # Build response
    from app.schemas.user import UserComplete, UserProfileResponse, UserGoalResponse
    
    response = UserComplete(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login=user.last_login,
        profile=UserProfileResponse(**user.profile.__dict__) if user.profile else None,
        active_goal=UserGoalResponse(**active_goal.__dict__) if active_goal else None
    )
    
    return response


# ==========================================
# LOGOUT (Optional - for token blacklist)
# ==========================================

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user
    
    **Note**: JWT tokens are stateless, so logout is client-side
    - Client should delete stored tokens
    - For enhanced security, implement token blacklist with Redis (TODO)
    """
    return {"message": "Successfully logged out"}


# ==========================================
# CHANGE PASSWORD
# ==========================================

from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user
    
    - Requires current password for verification
    - New password must be at least 6 characters
    """
    from app.utils.security import verify_password, hash_password
    
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải có ít nhất 6 ký tự"
        )
    
    # Update password
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Đổi mật khẩu thành công"}