import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = True
    SECRET_KEY: str = "development-secret-key"
    
    # GitHub Configuration
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None
    
    # Mock Service Configuration
    MOCK_MODE: bool = True
    MOCK_JFROG_URL: str = "https://mock-jfrog.example.com"
    MOCK_WORKFLOW_URL: str = "https://mock-workflow.example.com"
    
    # Real Service Configuration (used when MOCK_MODE=False)
    JFROG_URL: Optional[str] = None
    JFROG_TOKEN: Optional[str] = None
    ML_PLATFORM_URL: Optional[str] = None
    ML_PLATFORM_TOKEN: Optional[str] = None
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./model_validation_bot.db"
    
    # Job Configuration
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_SECONDS: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()