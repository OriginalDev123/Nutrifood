"""
FastAPI Dependencies

Dependency injection for authentication and authorization
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token, verify_token_type

# ==========================================
# OAuth2 SCHEME
# ==========================================

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",  # Token endpoint URL
    scheme_name="JWT"
)


# ==========================================
# AUTHENTICATION DEPENDENCIES
# ==========================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Dependency injection:
    - Extracts token from Authorization header
    - Decodes and validates token
    - Fetches user from database
    - Raises 401 if invalid
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        User: Authenticated user object
    
    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    
    # Define exception for reuse
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.user_id == user_id, User.is_deleted == False).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (not disabled)
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        User: Active user object
    
    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin privileges
    
    Args:
        current_user: Active user from get_current_active_user
    
    Returns:
        User: Admin user object
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required"
        )
    return current_user


# ==========================================
# OPTIONAL USER DEPENDENCY
# ==========================================

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, otherwise None
    
    Useful for endpoints that work both authenticated and anonymous
    
    Args:
        token: Optional JWT token
        db: Database session
    
    Returns:
        User or None
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None