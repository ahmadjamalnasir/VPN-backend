from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import users, subscriptions, vpn, metrics, admin
from app.database import Base, engine
from app.middleware.ddos_protection import DDoSProtectionMiddleware, AdvancedRateLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from datetime import datetime
import asyncio
from fastapi import HTTPException
from sqlalchemy import text
import redis.asyncio as redis
import logging
import sys

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def check_database_connection():
    """Check if database is accessible"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False

# Initialize FastAPI app with debug mode for development
app = FastAPI(
    title="Prime VPN API",
    description="Backend API for Prime VPN service with advanced DDoS protection",
    version="1.0.2",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    debug=True  # Enable debug mode for better error messages
)

@app.on_event("startup")
async def startup_event():
    """
    Verify all required services are available on startup
    """
    logger.info("Starting up Prime VPN API server...")
    
    # Check database
    if not await check_database_connection():
        logger.error("Database connection failed - shutting down")
        sys.exit(1)
        
    # Check Redis only if rate limiting is enabled
    if settings.RATE_LIMITING_ENABLED:
        if not await check_redis_connection():
            logger.warning("Redis connection failed - rate limiting will be disabled")
            app.state.rate_limiting_enabled = False
        else:
            app.state.rate_limiting_enabled = True
            logger.info("Rate limiting enabled")
    
    logger.info("All startup checks completed successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up connections on shutdown
    """
    logger.info("Shutting down Prime VPN API server...")
    # Close any remaining connections
    await engine.dispose()
    logger.info("All connections closed")

# Add rate limiting middleware (with lazy Redis connection)
app.add_middleware(
    RateLimitMiddleware,
    redis_url=settings.REDIS_URL,
    auto_connect=False  # Don't connect to Redis until first request
)

@app.on_event("startup")
async def startup_event():
    """
    Perform startup checks without blocking server startup.
    Services will be checked in background.
    """
    logger.info("Starting API server...")
    asyncio.create_task(check_database_connection())
    asyncio.create_task(check_redis_connection())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = await check_database_connection()
    redis_ok = await check_redis_connection()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

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
