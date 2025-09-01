from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import users, subscriptions, vpn, metrics, admin
from app.database import Base, engine
from app.middleware.ddos_protection import DDoSProtectionMiddleware, AdvancedRateLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from datetime import datetime

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Prime VPN API",
    description="Backend API for Prime VPN service with advanced DDoS protection",
    version="1.0.2",
    docs_url="/api/docs",  # Move Swagger UI to /api/docs for security
    redoc_url="/api/redoc"  # Move ReDoc to /api/redoc
)

# Add DDoS protection middleware (first layer)
app.add_middleware(DDoSProtectionMiddleware)

# Add advanced rate limiting middleware (second layer)
app.add_middleware(AdvancedRateLimitMiddleware)

# Configure CORS with WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Use configured origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_websockets=True,
)

# Include routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(vpn.router, prefix="/vpn", tags=["vpn"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Welcome to Prime VPN API"}

@app.get("/health")
async def health_check():
    """Health check endpoint with rate limiting status"""
    return {
        "status": "healthy",
        "version": "1.0.2",
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "ddos_protection": settings.DDOS_PROTECTION_ENABLED
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    from app.services.rate_limit_service import rate_limit_service
    try:
        stats = await rate_limit_service.get_rate_limit_stats()
        return {
            "rate_limiting": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception:
        return {"error": "Unable to fetch metrics"}
