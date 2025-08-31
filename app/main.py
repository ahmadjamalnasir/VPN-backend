from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.routes import users, subscriptions, vpn, metrics
from app.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Prime VPN API",
    description="Backend API for Prime VPN service",
    version="1.0.0"
)

# Configure CORS with WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
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

@app.get("/")
async def root():
    return {"message": "Welcome to Prime VPN API"}
