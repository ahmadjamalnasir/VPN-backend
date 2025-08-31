from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from app.database import async_session
from app.crud.subscription_plan import subscription_plan_crud

async def init_subscription_plans():
    async with async_session() as db:
        # Create Free Plan
        free_plan = {
            "name": "Free",
            "description": "Basic VPN access with limited features",
            "price": "0",
            "duration_days": 30,
            "is_free": True,
            "features": {
                "servers": ["US", "UK"],
                "devices": 1,
                "bandwidth": "10GB",
                "speed": "Medium",
                "support": "Email"
            }
        }

        # Create Basic Plan
        basic_plan = {
            "name": "Basic",
            "description": "Enhanced VPN access with more features",
            "price": "9.99",
            "duration_days": 30,
            "is_free": False,
            "features": {
                "servers": ["US", "UK", "EU", "Asia"],
                "devices": 3,
                "bandwidth": "Unlimited",
                "speed": "High",
                "support": "24/7 Email"
            }
        }

        # Create Premium Plan
        premium_plan = {
            "name": "Premium",
            "description": "Ultimate VPN access with all features",
            "price": "19.99",
            "duration_days": 30,
            "is_free": False,
            "features": {
                "servers": ["All Locations"],
                "devices": 5,
                "bandwidth": "Unlimited",
                "speed": "Maximum",
                "support": "24/7 Priority Support",
                "streaming": True,
                "dedicated_ip": True
            }
        }

        # Check if free plan exists
        if not await subscription_plan_crud.get_free_plan(db):
            await subscription_plan_crud.create(db, free_plan)
            await subscription_plan_crud.create(db, basic_plan)
            await subscription_plan_crud.create(db, premium_plan)
            print("Subscription plans initialized successfully")
        else:
            print("Subscription plans already exist")

if __name__ == "__main__":
    asyncio.run(init_subscription_plans())
