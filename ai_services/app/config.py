"""
Configuration Module - NutriAI AI Service
Load và validate environment variables
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings từ environment variables
    """
    
    # === Gemini API Configuration ===
    GOOGLE_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GOOGLE_AI_API_KEY")
    )
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_VISION_MODEL: str = ""
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 2048
    
    # === Image Processing Settings ===
    MAX_IMAGE_SIZE_MB: int = 10
    TARGET_IMAGE_SIZE_PX: int = 768  # Increased from 384 for better quality food recognition
    IMAGE_QUALITY: int = 85  # Increased from 75 for better image quality
    
    # === Service Configuration ===
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    
    # === Backend API ===
    BACKEND_API_URL: str = "http://backend:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def max_image_size_bytes(self) -> int:
        """Chuyển đổi MB sang bytes"""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024
    
    @property
    def is_production(self) -> bool:
        """Check môi trường production"""
        return self.ENVIRONMENT == "production"
    
    def validate_api_key(self) -> bool:
        """
        Validate API key đã được config chưa
        
        Returns:
            True nếu API key hợp lệ
        """
        return (
            self.GOOGLE_API_KEY and
            len(self.GOOGLE_API_KEY) > 30 and
            self.GOOGLE_API_KEY.startswith("AIza")
        )


# Singleton instance - import từ module này
settings = Settings()