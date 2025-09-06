from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Prime VPN"
    APP_VERSION: str = "1.0.2"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    BASE_URL: str = "http://localhost:8000"
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Payment Integration
    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    STRIPE_MONTHLY_PRICE_ID: str = "price_monthly"
    STRIPE_YEARLY_PRICE_ID: str = "price_yearly"

    # Rate limiting and DDoS protection
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMITS: Dict[str, Dict[str, Any]] = {
        "auth_login": {"requests": 5, "window": 300, "burst": 2},
        "auth_register": {"requests": 3, "window": 3600, "burst": 1},
        "auth_refresh": {"requests": 10, "window": 300, "burst": 5},
        "password_reset": {"requests": 3, "window": 3600, "burst": 1},
        "vpn_connect": {"requests": 20, "window": 60, "burst": 5},
        "vpn_disconnect": {"requests": 30, "window": 60, "burst": 10},
        "payments": {"requests": 10, "window": 300, "burst": 3},
        "websocket": {"requests": 5, "window": 60, "burst": 2},
        "api_general": {"requests": 60, "window": 60, "burst": 20},
    }
    DDOS_PROTECTION_ENABLED: bool = True
    DDOS_THRESHOLD: int = 500
    DDOS_BAN_DURATION: int = 3600
    DDOS_WHITELIST_IPS: List[str] = ["127.0.0.1", "::1"]
    
    # Suspicious activity detection
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 50
    SUSPICIOUS_ACTIVITY_WINDOW: int = 300
    SUSPICIOUS_ACTIVITY_BAN: int = 1800
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_NAME: Optional[str] = None
    EMAIL_FROM_ADDRESS: Optional[str] = None
    EMAIL_VERIFICATION_TOKEN_EXPIRES: int = 24 * 3600
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Session
    SESSION_EXPIRES_IN: int = 30 * 24 * 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()