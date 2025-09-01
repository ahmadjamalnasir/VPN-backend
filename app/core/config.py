from pydantic_settings import BaseSettings
from typing import List, Dict, Any

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
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting & DDoS Protection
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE: str = "redis"  # redis or memory
    
    # Global rate limits (requests per minute)
    GLOBAL_RATE_LIMIT: int = 1000
    IP_RATE_LIMIT: int = 100
    
    # Endpoint-specific rate limits
    RATE_LIMITS: Dict[str, Dict[str, Any]] = {
        "auth_login": {"requests": 5, "window": 300, "burst": 2},  # 5 req/5min, burst 2
        "auth_register": {"requests": 3, "window": 3600, "burst": 1},  # 3 req/hour
        "auth_refresh": {"requests": 10, "window": 300, "burst": 5},  # 10 req/5min
        "password_reset": {"requests": 3, "window": 3600, "burst": 1},  # 3 req/hour
        "vpn_connect": {"requests": 20, "window": 60, "burst": 5},  # 20 req/min
        "vpn_disconnect": {"requests": 30, "window": 60, "burst": 10},  # 30 req/min
        "payments": {"requests": 10, "window": 300, "burst": 3},  # 10 req/5min
        "websocket": {"requests": 5, "window": 60, "burst": 2},  # 5 connections/min
        "api_general": {"requests": 60, "window": 60, "burst": 20},  # 60 req/min
    }
    
    # DDoS Protection
    DDOS_PROTECTION_ENABLED: bool = True
    DDOS_THRESHOLD: int = 500  # requests per minute to trigger protection
    DDOS_BAN_DURATION: int = 3600  # 1 hour ban
    DDOS_WHITELIST_IPS: List[str] = ["127.0.0.1", "::1"]
    
    # Suspicious activity detection
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 50  # failed attempts
    SUSPICIOUS_ACTIVITY_WINDOW: int = 300  # 5 minutes
    SUSPICIOUS_ACTIVITY_BAN: int = 1800  # 30 minutes
    
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
