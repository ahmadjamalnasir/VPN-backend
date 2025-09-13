from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.schemas.subscription import *
from app.services.auth import verify_token
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

# MOBILE ENDPOINTS
@router.get("/user/plans", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's subscription history (Mobile)"""
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == current_user_id)
        .order_by(UserSubscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    return subscriptions

# ADMIN ENDPOINTS
@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_subscription_plan(
    name: str = Query(..., description="Plan name"),
    plan_type: str = Query(..., description="Plan type"),
    price: float = Query(..., description="Plan price"),
    duration_days: int = Query(..., description="Duration in days"),
    is_premium: bool = Query(False, description="Is premium plan"),
    features: str = Query(None, description="Plan features"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create new subscription plan (Admin only)"""
    # Verify admin access
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    plan = SubscriptionPlan(
        name=name,
        plan_type=plan_type,
        price=price,
        duration_days=duration_days,
        is_premium=is_premium,
        features=features
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all available subscription plans (Admin only)"""
    # Verify admin access
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price))
    plans = result.scalars().all()
    return plans

# SHARED ENDPOINTS
@router.get("/users/{user_id}", response_model=List[UserSubscriptionResponse])
async def get_user_subscription_history(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user's subscription history by user ID"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data or admin)
    requesting_user = await db.execute(select(User).where(User.id == current_user_id))
    requesting_user = requesting_user.scalar_one_or_none()
    if str(user.id) != current_user_id and not requesting_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get subscription history
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id)
        .order_by(UserSubscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    return subscriptions

@router.post("/assign", response_model=UserSubscriptionResponse)
async def assign_subscription(
    user_id: int = Query(..., description="User ID (readable integer)"),
    plan_id: int = Query(..., description="Plan ID (readable integer)"),
    auto_renew: bool = Query(True, description="Auto renew subscription"),
    payment_method: str = Query(None, description="Payment method"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Assign subscription plan to user"""
    # Find user by readable user_id
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (user can assign to themselves or admin)
    requesting_user = await db.execute(select(User).where(User.id == current_user_id))
    requesting_user = requesting_user.scalar_one_or_none()
    if str(user.id) != current_user_id and not requesting_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find plan by readable plan_id
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.plan_id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Cancel existing active subscriptions
    existing_result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id, UserSubscription.status == "active")
    )
    existing_subscriptions = existing_result.scalars().all()
    for sub in existing_subscriptions:
        sub.status = "canceled"
    
    # Create new subscription - Use plan.id (UUID) not plan_id (int)
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    subscription = UserSubscription(
        user_id=user.id,  # UUID
        plan_id=plan.id,  # UUID
        status="active",
        start_date=start_date,
        end_date=end_date,
        auto_renew=auto_renew,
        payment_method=payment_method
    )
    db.add(subscription)
    
    # Update user premium status
    user.is_premium = plan.is_premium
    
    await db.commit()
    await db.refresh(subscription)
    return subscription

@router.put("/cancel/{user_id}")
async def cancel_subscription(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Cancel user's active subscription"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data or admin)
    requesting_user = await db.execute(select(User).where(User.id == current_user_id))
    requesting_user = requesting_user.scalar_one_or_none()
    if str(user.id) != current_user_id and not requesting_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
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