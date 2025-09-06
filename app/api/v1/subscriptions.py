from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionResponse, SubscriptionCreate
from uuid import UUID
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/user", response_model=SubscriptionResponse)
async def get_user_subscription(
    email: str = Query(..., description="User email to get subscription"),
    db: AsyncSession = Depends(get_db)
):
    """Get subscription by user email"""
    # First find user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get subscription
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.get("/{user_id}", response_model=SubscriptionResponse)
async def get_subscription_by_user_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get subscription by user ID"""
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    user_email: str = Query(..., description="User email for subscription"),
    plan_type: str = Query(..., description="Plan type: monthly, yearly, free"),
    db: AsyncSession = Depends(get_db)
):
    """Create subscription for user"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if subscription exists
    existing = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has a subscription")
    
    # Calculate dates
    start_date = datetime.utcnow()
    if plan_type == "monthly":
        end_date = start_date + timedelta(days=30)
    elif plan_type == "yearly":
        end_date = start_date + timedelta(days=365)
    else:  # free
        end_date = start_date + timedelta(days=365 * 10)  # Long period for free
    
    subscription = Subscription(
        user_id=user.id,
        plan_type=plan_type,
        status="active",
        start_date=start_date,
        end_date=end_date
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription

@router.put("/update", response_model=SubscriptionResponse)
async def update_subscription(
    user_email: str = Query(..., description="User email"),
    plan_type: str = Query(..., description="New plan type: monthly, yearly, free"),
    db: AsyncSession = Depends(get_db)
):
    """Update user subscription plan"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get subscription
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Update subscription
    subscription.plan_type = plan_type
    subscription.status = "active"
    
    # Update end date based on new plan
    if plan_type == "monthly":
        subscription.end_date = datetime.utcnow() + timedelta(days=30)
    elif plan_type == "yearly":
        subscription.end_date = datetime.utcnow() + timedelta(days=365)
    
    await db.commit()
    await db.refresh(subscription)
    return subscription