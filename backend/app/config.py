"""
Configuration Management using Pydantic Settings

Pydantic Settings tự động:
1. Đọc file .env
2. Validate types (str, int, bool, etc.)
3. Provide default values
4. Raise errors nếu thiếu required fields
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, validator
from typing import List
import secrets


class Settings(BaseSettings):
    """
    Application Settings
    
    Pydantic sẽ tự động map:
    - APP_NAME trong .env → self.APP_NAME
    - Case-insensitive: app_name = APP_NAME = App_Name
    """
    
    # ==========================================
    # Application
    # ==========================================
    APP_NAME: str = "NutriAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ==========================================
    # Server
    # ==========================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ==========================================
    # Database
    # ==========================================
    DATABASE_URL: str = Field(
        ...,  # ... means REQUIRED (phải có trong .env)
        description="PostgreSQL connection string"
    )
    DB_ECHO: bool = False  # Log SQL queries
    
    # ==========================================
    # Redis
    # ==========================================
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ==========================================
    # JWT Authentication
    # ==========================================
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    
    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "your-super-secret-jwt-key-change-this-in-production":
            raise ValueError("❌ JWT_SECRET_KEY must be changed in production!")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ==========================================
    # Password Hashing
    # ==========================================
    BCRYPT_ROUNDS: int = 12
    
    # ==========================================
    # CORS (Cross-Origin Resource Sharing)
    # ==========================================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """
        Convert comma-separated string to list
        "http://localhost:3000,http://localhost:5173" 
        → ["http://localhost:3000", "http://localhost:5173"]
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ==========================================
    # File Upload
    # ==========================================
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Convert MB to Bytes for validation"""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # ==========================================
    # AI Services (Microservices URLs)
    # ==========================================
    AI_SERVICE_URL: str = "http://localhost:8001"  # Main AI Service (Vision + Advice + Chat)
    AI_VISION_SERVICE_URL: str = "http://localhost:8001"
    AI_CHATBOT_SERVICE_URL: str = "http://localhost:8002"
    AI_MEAL_PLANNER_SERVICE_URL: str = "http://localhost:8003"
    
    # ==========================================
    # Celery (Async Tasks)
    # ==========================================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # ==========================================
    # External APIs
    # ==========================================
    OPENAI_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # ==========================================
    # MongoDB (Optional - AI Logs)
    # ==========================================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "nutriai_logs"
    
    # ==========================================
    # Qdrant (Vector DB)
    # ==========================================
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_LEVEL: str = "INFO"
    
    # ==========================================
    # Pydantic Settings Configuration
    # ==========================================
    model_config = SettingsConfigDict(
        env_file=".env",           # Đọc từ file .env
        env_file_encoding="utf-8", # Encoding
        case_sensitive=False,       # APP_NAME = app_name
        extra="ignore"              # Ignore unknown env vars
    )
    
    # ==========================================
    # Validators (Optional - Advanced)
    # ==========================================
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Đảm bảo ENVIRONMENT chỉ có 3 giá trị hợp lệ"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Đảm bảo DATABASE_URL đúng format"""
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://'")
        return v
    
    # ==========================================
    # Helper Properties
    # ==========================================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"


# ==========================================
# Singleton Instance
# ==========================================
# Tạo 1 instance duy nhất (singleton pattern)
# Import từ file khác: from app.config import settings
settings = Settings()


# ==========================================
# Print config on startup (for debugging)
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 NutriAI Configuration Loaded")
    print("=" * 50)
    print(f"App Name: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1]}")  # Hide password
    print(f"Redis: {settings.REDIS_URL}")
    print(f"CORS Origins: {settings.CORS_ORIGINS_LIST}")
    print("=" * 50)