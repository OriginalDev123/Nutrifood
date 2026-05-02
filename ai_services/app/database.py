"""
Database Connection - NutriAI AI Service
Kết nối tới Backend PostgreSQL database để fuzzy search foods
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator
import logging
import os

logger = logging.getLogger(__name__)

# === DATABASE URL ===
# Lấy từ environment variable hoặc sử dụng default
DATABASE_URL = os.getenv(
    "BACKEND_DATABASE_URL",
    "postgresql://nutriai_user:nutriai_password@postgres:5432/nutriai_db"
)

# === SQLALCHEMY ENGINE ===
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,         # Connection pool size
        max_overflow=10,     # Max connections beyond pool_size
        echo=False           # Set True to log SQL queries (debug)
    )
    
    logger.info(f"✅ Database engine created: {DATABASE_URL.split('@')[1]}")  # Log without password
    
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {str(e)}")
    raise

# === SESSION FACTORY ===
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# === BASE CLASS ===
Base = declarative_base()


# === DEPENDENCY INJECTION ===
def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI endpoints
    
    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"❌ Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# === HEALTH CHECK ===
def check_database_connection() -> bool:
    """
    Kiểm tra kết nối database có hoạt động không
    
    Returns:
        True nếu kết nối thành công, False nếu thất bại
    """
    try:
        db = SessionLocal()
        # Execute simple query
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection check failed: {str(e)}")
        return False


# === MODELS (Import từ Backend) ===
# Note: Vì AI Service và Backend cùng database,
# chúng ta cần define lại Food model ở đây (hoặc share models)

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Food(Base):
    """
    Food model - mirror từ backend/app/models/food.py
    Chỉ cần các fields cần thiết cho nutrition search
    """
    
    __tablename__ = "foods"
    
    # Primary Key
    food_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Names
    name_vi = Column(String(255), nullable=False, index=True)
    name_en = Column(String(255), nullable=True)
    
    # Category
    category = Column(String(100))
    source = Column(String(100))
    
    # Nutrition (per 100g)
    calories_per_100g = Column(Numeric(8, 2), nullable=False)
    protein_per_100g = Column(Numeric(6, 2), default=0)
    carbs_per_100g = Column(Numeric(6, 2), default=0)
    fat_per_100g = Column(Numeric(6, 2), default=0)
    fiber_per_100g = Column(Numeric(6, 2), default=0)
    sugar_per_100g = Column(Numeric(6, 2), default=0)
    sodium_per_100g = Column(Numeric(8, 2), default=0)
    
    # Metadata
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Food {self.name_vi} ({self.food_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "food_id": str(self.food_id),
            "name_vi": self.name_vi,
            "name_en": self.name_en,
            "category": self.category,
            "source": self.source,
            "nutrition": {
                "serving_size_g": 100.0,
                "calories_per_100g": float(self.calories_per_100g),
                "protein_per_100g": float(self.protein_per_100g) if self.protein_per_100g else 0.0,
                "carbs_per_100g": float(self.carbs_per_100g) if self.carbs_per_100g else 0.0,
                "fat_per_100g": float(self.fat_per_100g) if self.fat_per_100g else 0.0,
                "fiber_per_100g": float(self.fiber_per_100g) if self.fiber_per_100g else 0.0,
                "sugar_per_100g": float(self.sugar_per_100g) if self.sugar_per_100g else 0.0,
                "sodium_per_100g": float(self.sodium_per_100g) if self.sodium_per_100g else 0.0
            },
            "is_verified": self.is_verified
        }