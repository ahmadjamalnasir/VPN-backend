from fastapi import APIRouter, Depends
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/status")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db)
):
    """Get subscription status (placeholder)"""
    return {
        "plan_type": "free",
        "status": "active",
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-12-31T23:59:59Z"
    }

@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free Plan",
                "price": 0,
                "features": ["Basic VPN access", "1 device"]
            },
            {
                "id": "premium",
                "name": "Premium Plan",
                "price": 9.99,
                "features": ["Unlimited VPN access", "5 devices", "Premium servers"]
            }
        ]
    }
