#!/usr/bin/env python3
"""
Insert default subscription plans
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.subscription_plan import SubscriptionPlan

async def insert_default_plans():
    print("📋 Inserting default subscription plans...")
    
    async with AsyncSessionLocal() as db:
        plans = [
            SubscriptionPlan(
                name="Free Plan",
                plan_type="free",
                price=0.0,
                duration_days=365,
                is_premium=False,
                features='{"servers": "basic", "locations": "limited", "bandwidth": "1GB/month"}'
            ),
            SubscriptionPlan(
                name="Monthly Premium",
                plan_type="monthly",
                price=9.99,
                duration_days=30,
                is_premium=True,
                features='{"servers": "premium", "locations": "all", "bandwidth": "unlimited"}'
            ),
            SubscriptionPlan(
                name="Yearly Premium",
                plan_type="yearly",
                price=99.99,
                duration_days=365,
                is_premium=True,
                features='{"servers": "premium", "locations": "all", "bandwidth": "unlimited", "discount": "2 months free"}'
            )
        ]
        
        for plan in plans:
            db.add(plan)
        
        await db.commit()
        print(f"✅ Inserted {len(plans)} subscription plans")
        
        for plan in plans:
            print(f"   Plan {plan.plan_id}: {plan.name} - ${plan.price}")

if __name__ == "__main__":
    asyncio.run(insert_default_plans())