from pydantic_settings import BaseSettings
from typing import List, Dict, Any

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Prime VPN"
    DEBUG: bool = True
    
    # JWT Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ahmad.nasir@localhost:5432/primevpn"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "https://yourdomain.com"]
    
    # Security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "yourdomain.com"]
    TRUSTED_PROXIES: List[str] = ["127.0.0.1"]
    
    # DDoS Protection
    DDOS_PROTECTION_ENABLED: bool = True
    DDOS_THRESHOLD: int = 100  # requests per minute
    DDOS_BAN_DURATION: int = 300  # seconds
    DDOS_WHITELIST_IPS: List[str] = ["127.0.0.1", "::1"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMITS: Dict[str, Dict[str, Any]] = {
        "auth_login": {"requests": 5, "window": 60, "burst": 2},
        "auth_register": {"requests": 3, "window": 60, "burst": 1},
        "auth_refresh": {"requests": 10, "window": 60, "burst": 5},
        "password_reset": {"requests": 3, "window": 300, "burst": 0},
        "vpn_connect": {"requests": 10, "window": 60, "burst": 3},
        "vpn_disconnect": {"requests": 20, "window": 60, "burst": 5},
        "payments": {"requests": 5, "window": 60, "burst": 1},
        "websocket": {"requests": 2, "window": 60, "burst": 0},
        "api_general": {"requests": 30, "window": 60, "burst": 10}
    }
    
    # Suspicious Activity Detection
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 20
    SUSPICIOUS_ACTIVITY_WINDOW: int = 300  # 5 minutes
    SUSPICIOUS_ACTIVITY_BAN: int = 1800  # 30 minutes
    
    # Stripe Payment
    STRIPE_SECRET_KEY: str = "sk_test_your_stripe_secret_key"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_your_stripe_publishable_key"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_webhook_secret"
    
    # Connection Limits
    MAX_CONNECTIONS_PER_IP: int = 10
    CONNECTION_TIMEOUT: int = 30

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()