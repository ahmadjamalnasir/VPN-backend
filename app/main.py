from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.database import engine
from app.api.v1 import auth, users, subscriptions, vpn
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
    description="Professional VPN Backend API with logical request/response patterns",
    version="1.0.2",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting Prime VPN API server...")
    await check_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API routers with proper structure
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(vpn.router, prefix="/api/v1/vpn", tags=["VPN"])

@app.get("/")
async def root():
    return {
        "message": "Prime VPN API",
        "version": "1.0.2",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users", 
            "subscriptions": "/api/v1/subscriptions",
            "vpn": "/api/v1/vpn"
        }
    }

@app.get("/health")
async def health():
    db_ok = await check_database()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.2"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)