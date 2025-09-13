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
    description="Production VPN Backend API with mobile and admin endpoints",
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

# MOBILE APP ENDPOINTS
app.include_router(auth.router, prefix="/auth", tags=["Mobile - Authentication"])
app.include_router(users.router, prefix="/users", tags=["Mobile - Users"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Mobile - Subscriptions"])
app.include_router(vpn.router, prefix="/vpn", tags=["Mobile - VPN"])
app.include_router(websocket.router, prefix="/websocket", tags=["Mobile - WebSocket"])

# ADMIN BACKOFFICE ENDPOINTS
app.include_router(admin.router, prefix="/admin", tags=["Admin - Management"])
app.include_router(analytics.router, prefix="/analytics", tags=["Admin - Analytics"])
app.include_router(health.router, prefix="/health", tags=["Admin - Health"])

# LEGACY MOBILE ENDPOINTS (for compatibility)
app.include_router(mobile.router, prefix="/mobile", tags=["Legacy Mobile"])

@app.get("/")
async def root():
    return {
        "message": "Prime VPN API v2.0.0",
        "version": "2.0.0",
        "security": {
            "ddos_protection": settings.DDOS_PROTECTION_ENABLED,
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "cors_enabled": True
        },
        "docs": "/docs",
        "mobile_endpoints": {
            "auth": "/auth",
            "profile": "/users/profile",
            "vpn": "/vpn",
            "subscriptions": "/subscriptions/user/plans",
            "websocket": "/websocket/connection"
        },
        "admin_endpoints": {
            "users": "/users (list), /users/by-id/{id}, /users/status/{id}",
            "subscriptions": "/subscriptions/plans",
            "analytics": "/analytics",
            "vpn_servers": "/vpn/servers",
            "health": "/health",
            "websocket": "/websocket/admin-dashboard"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)