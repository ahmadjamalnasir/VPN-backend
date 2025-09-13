from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import get_settings
from app.database import engine
from app.api.v1 import auth, users, subscriptions, vpn, admin, mobile, analytics, health, websocket
from app.middleware.ddos_protection import DDoSProtectionMiddleware, AdvancedRateLimitMiddleware
from datetime import datetime
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

async def check_database():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connected")
        return True
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

app = FastAPI(
    title="Prime VPN API",
    description="Production VPN Backend API with admin, mobile, analytics, and real-time features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting Prime VPN API server...")
    logger.info("🛡️ DDoS Protection: Enabled" if settings.DDOS_PROTECTION_ENABLED else "🛡️ DDoS Protection: Disabled")
    logger.info("⚡ Rate Limiting: Enabled" if settings.RATE_LIMIT_ENABLED else "⚡ Rate Limiting: Disabled")
    await check_database()

# Security middleware (order matters!)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# DDoS Protection Middleware
app.add_middleware(DDoSProtectionMiddleware)

# Advanced Rate Limiting Middleware
app.add_middleware(AdvancedRateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(vpn.router, prefix="/api/v1/vpn", tags=["VPN"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(mobile.router, prefix="/api/v1/mobile", tags=["Mobile"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

@app.get("/")
async def root():
    return {
        "message": "Prime VPN API",
        "version": "2.0.0",
        "security": {
            "ddos_protection": settings.DDOS_PROTECTION_ENABLED,
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "cors_enabled": True
        },
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users", 
            "subscriptions": "/api/v1/subscriptions",
            "vpn": "/api/v1/vpn",
            "admin": "/api/v1/admin",
            "mobile": "/api/v1/mobile",
            "analytics": "/api/v1/analytics",
            "health": "/health",
            "websocket": "/ws"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)