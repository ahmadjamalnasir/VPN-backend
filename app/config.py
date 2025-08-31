from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # JWT settings
    JWT_SECRET: str
    
    # Redis settings
    REDIS_URL: str
    
    # Stripe settings
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # PayPal settings
    PAYPAL_CLIENT_ID: str
    PAYPAL_SECRET: str
    
    # Base URL
    BASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
