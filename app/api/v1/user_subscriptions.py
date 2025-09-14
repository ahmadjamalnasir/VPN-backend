from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.subscription_plan import SubscriptionPlan, PlanStatus
from app.models.user_subscription import UserSubscription, SubscriptionStatus
from app.schemas.subscription_new import *
from app.services.auth import verify_token
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

router = APIRouter()

# Public Plans
@router.get("/plans", response_model=List[SubscriptionPlanResponse], tags=["Public - Subscription Plans"])
async def get_active_plans(db: AsyncSession = Depends(get_db)):
    """Get all active subscription plans (Public)"""
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.status == PlanStatus.active)
        .order_by(SubscriptionPlan.price_usd)
    )
    return result.scalars().all()

# User Subscription Management
@router.get("/users/{user_id}", response_model=UserSubscriptionResponse, tags=["User - Subscriptions"])
async def get_user_subscription(
    user_id: int = Path(..., description="User ID"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user's active subscription"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data or admin)
    if str(user.id) != current_user_id:
        try:
            admin_uuid = UUID(current_user_id)
            admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
            if not admin_result.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Access denied")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(
            and_(
                UserSubscription.user_id == user.id,
                UserSubscription.status == SubscriptionStatus.active
            )
        )
        .order_by(UserSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return subscription

@router.post("/users/{user_id}", response_model=UserSubscriptionResponse, tags=["User - Subscriptions"])
async def assign_subscription(
    user_id: int,
    subscription_data: UserSubscriptionCreate,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Assign subscription (user self-purchase)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data only for users, admin can assign to anyone)
    if str(user.id) != current_user_id:
        try:
            admin_uuid = UUID(current_user_id)
            admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
            if not admin_result.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Can only assign subscription to yourself")
        except ValueError:
            raise HTTPException(status_code=403, detail="Can only assign subscription to yourself")
    
    # Find plan
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == subscription_data.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Cancel existing active subscriptions
    existing_result = await db.execute(
        select(UserSubscription)
        .where(
            and_(
                UserSubscription.user_id == user.id,
                UserSubscription.status == SubscriptionStatus.active
            )
        )
    )
    for existing in existing_result.scalars().all():
        existing.status = SubscriptionStatus.canceled
    
    # Create new subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    subscription = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        auto_renew=subscription_data.auto_renew
    )
    db.add(subscription)
    
    # Update user premium status
    user.is_premium = plan.price_usd > 0
    
    await db.commit()
    await db.refresh(subscription)
    return subscription

@router.patch("/users/{user_id}/cancel", tags=["User - Subscriptions"])
async def cancel_subscription(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Cancel subscription"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data or admin)
    if str(user.id) != current_user_id:
        try:
            admin_uuid = UUID(current_user_id)
            admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
            if not admin_result.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Access denied")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Find active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(
            and_(
                UserSubscription.user_id == user.id,
                UserSubscription.status == SubscriptionStatus.active
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    subscription.auto_renew = False
    await db.commit()
    return {"message": "Subscription auto-renew disabled"}

@router.get("/users/{user_id}/history", response_model=List[UserSubscriptionResponse], tags=["User - Subscriptions"])
async def get_subscription_history(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get subscription history"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access (own data or admin)
    if str(user.id) != current_user_id:
        try:
            admin_uuid = UUID(current_user_id)
            admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
            if not admin_result.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Access denied")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id)
        .order_by(UserSubscription.created_at.desc())
    )
    return result.scalars().all()