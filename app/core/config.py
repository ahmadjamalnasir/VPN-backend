from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Prime VPN"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    
    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = None
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM_NAME: str
    EMAIL_FROM_ADDRESS: str
    EMAIL_VERIFICATION_TOKEN_EXPIRES: int = 24 * 3600  # 24 hours
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Session
    SESSION_EXPIRES_IN: int = 30 * 24 * 3600  # 30 days
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
