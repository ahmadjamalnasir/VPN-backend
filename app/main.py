from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import get_settings
from app.database import engine
from app.api.v1 import auth, admin_auth, users, subscriptions, vpn, admin, mobile, analytics, health, websocket, user_management
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

# ADMIN AUTHENTICATION (No Rate Limiting)
app.include_router(admin_auth.router, prefix="/api/v1/admin-auth", tags=["Admin - Authentication"])

# ADMIN BACKOFFICE ENDPOINTS
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(user_management.router, prefix="/api/v1/admin")
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Admin - Analytics"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Admin - Health"])

# MOBILE APP ENDPOINTS
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Mobile - Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Mobile - Users"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Mobile - Subscriptions"])
app.include_router(vpn.router, prefix="/api/v1/vpn", tags=["Mobile - VPN"])
app.include_router(websocket.router, prefix="/api/v1/websocket", tags=["Mobile - WebSocket"])


# LEGACY MOBILE ENDPOINTS (for compatibility)
app.include_router(mobile.router, prefix="/api/v1/mobile", tags=["Legacy Mobile"])

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
        "admin_authentication": {
            "login": "/api/v1/admin-auth/login (No rate limiting)"
        },
        
        "admin_endpoints": {
            "admin_users": "/api/v1/admin/admin-users (list)",

            "vpn_users": "/api/v1/admin/vpn-users (list), /api/v1/admin/vpn-user/{id}/status",
            "create_admin_user": "/api/v1/admin/create-admin-user",
            "subscriptions": "/api/v1/subscriptions/plans",
            "analytics": "/api/v1/analytics",
            "list_servers": "/api/v1/admin/servers",
            "add_server": "/api/v1/admin/add_server",
            "health": "/api/v1/health",
            "websocket": "/api/v1/websocket/admin-dashboard",
            "rate_limits": "/api/v1/admin/rate-limits/config"
        },
        "mobile_endpoints": {
            "auth": "/api/v1/auth",
            "profile": "/api/v1/users/profile",
            "vpn": "/api/v1/vpn",
            "subscriptions": "/api/v1/subscriptions/user/plans",
            "websocket": "/api/v1/websocket/connection"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)