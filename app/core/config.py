"""
Core configuration settings for the Image-to-Song backend application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Image-to-Song API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # AI Model Configuration
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "./models")
    BLIP2_MODEL_NAME: str = "Salesforce/blip2-flan-t5-xl"
    USE_GPU: bool = os.getenv("USE_GPU", "True").lower() == "true"
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "4"))
    
    # Image Processing
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    TARGET_IMAGE_SIZE: tuple = (384, 384)  # Optimal for BLIP-2
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Caching Settings
    CAPTION_CACHE_TTL: int = int(os.getenv("CAPTION_CACHE_TTL", "86400"))  # 24 hours
    
    # Performance Settings
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "2"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Spotify API Configuration
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8001/api/v1/spotify/callback")
    
    class Config:
        case_sensitive = True

# Global settings instance
settings = Settings()
