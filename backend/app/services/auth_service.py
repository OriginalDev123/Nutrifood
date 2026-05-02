"""
Authentication Service

Business logic for user authentication
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime, timezone
from uuid import UUID

from app.models.user import User, UserProfile
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import verify_password, get_password_hash


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create new user account
    
    Args:
        db: Database session
        user_data: User registration data
    
    Returns:
        User: Created user object
    
    Raises:
        HTTPException: 400 if email already exists
    """
    
    # 1. Kiểm tra email tồn tại (Nên dùng lowercase để đồng nhất)
    email_lower = user_data.email.lower()
    existing_user = db.query(User).filter(User.email == email_lower).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký"
        )
    
    # 2. Hash mật khẩu (Issue #10: Đảm bảo chỉ hash 1 lần duy nhất tại đây)
    hashed_password = get_password_hash(user_data.password)
    
    try:
        # 3. Khởi tạo đối tượng User
        user = User(
            email=email_lower,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_admin=False,
            email_verified=False
        )
        db.add(user)
        db.flush()  # Đẩy lên DB để lấy user_id nhưng chưa chốt (commit)
        
        # 4. Tạo Profile mặc định
        profile = UserProfile(
            user_id=user.user_id,
            timezone="Asia/Ho_Chi_Minh",
            language="vi"
        )
        db.add(profile)
        
        # 5. Commit toàn bộ hoặc không gì cả
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        db.rollback() # Rollback nếu bất kỳ bước nào ở trên thất bại
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi tạo tài khoản: {str(e)}"
        )


def authenticate_user(db: Session, login_data: UserLogin) -> User:
    """
    Authenticate user with email and password
    
    Args:
        db: Database session
        login_data: Login credentials
    
    Returns:
        User: Authenticated user object
    
    Raises:
        HTTPException: 401 if credentials invalid
    """
    
    # 1. Tìm user (Dùng lowercase email)
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    # 2. Verify mật khẩu
    # Lưu ý: verify_password nhận (plain_password, hashed_password)
    if not user or not verify_password(login_data.password, user.password_hash):
        # Trả về cùng một lỗi để tránh tiết lộ email có tồn tại hay không (Security Best Practice)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    try:
        user.last_login = datetime.now(timezone.utc)
        db.commit() # Lưu timestamp đăng nhập
    except:
        db.rollback() # Không để lỗi update timestamp làm gián đoạn đăng nhập
        
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User UUID
    
    Returns:
        User: User object
    
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user