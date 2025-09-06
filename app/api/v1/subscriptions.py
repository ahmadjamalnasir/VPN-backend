from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.schemas.subscription import *
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan))
    plans = result.scalars().all()
    return plans

@router.get("/user", response_model=UserSubscriptionResponse)
async def get_user_subscription(
    email: str = Query(..., description="User email"),
    db: AsyncSession = Depends(get_db)
):
    # Find user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id, UserSubscription.status == "active")
        .order_by(UserSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return subscription

@router.post("/assign", response_model=UserSubscriptionResponse)
async def assign_subscription(
    request: AssignSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    # Find user
    user_result = await db.execute(select(User).where(User.email == request.user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find plan
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.plan_id == request.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Cancel existing active subscriptions
    existing_result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id, UserSubscription.status == "active")
    )
    existing_subscriptions = existing_result.scalars().all()
    for sub in existing_subscriptions:
        sub.status = "canceled"
    
    # Create new subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    subscription = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        start_date=start_date,
        end_date=end_date
    )
    db.add(subscription)
    
    # Update user premium status
    user.is_premium = plan.is_premium
    
    await db.commit()
    await db.refresh(subscription)
    return subscription

@router.put("/cancel")
async def cancel_subscription(
    email: str = Query(..., description="User email"),
    db: AsyncSession = Depends(get_db)
):
    # Find user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cancel active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id, UserSubscription.status == "active")
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    subscription.status = "canceled"
    user.is_premium = False
    
    await db.commit()
    return {"message": "Subscription canceled successfully"}