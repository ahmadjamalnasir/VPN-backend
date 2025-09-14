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

async def verify_admin_access(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify admin access"""
    try:
        admin_uuid = UUID(current_user_id)
        admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
        admin_user = admin_result.scalar_one_or_none()
        if not admin_user:
            raise HTTPException(status_code=403, detail="Admin access required")
        return admin_user
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid admin token")

# Admin Plan Management
@router.get("/plans", response_model=List[SubscriptionPlanResponse], tags=["Admin - Subscription Plans"])
async def get_all_plans(admin_user = Depends(verify_admin_access), db: AsyncSession = Depends(get_db)):
    """Get all subscription plans (Admin)"""
    result = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.created_at.desc()))
    return result.scalars().all()

@router.post("/plans", response_model=SubscriptionPlanResponse, tags=["Admin - Subscription Plans"])
async def create_plan(
    plan: SubscriptionPlanCreate,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Create new subscription plan (Admin)"""
    new_plan = SubscriptionPlan(**plan.dict())
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan

@router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse, tags=["Admin - Subscription Plans"])
async def update_plan(
    plan_id: UUID,
    plan_update: SubscriptionPlanUpdate,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Update subscription plan (Admin)"""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    for field, value in plan_update.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}", tags=["Admin - Subscription Plans"])
async def deactivate_plan(
    plan_id: UUID,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate subscription plan (Admin)"""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan.status = PlanStatus.inactive
    await db.commit()
    return {"message": "Plan deactivated successfully"}

# Admin User Subscription Management
@router.get("/users/{user_id}", response_model=UserSubscriptionResponse, tags=["Admin - User Subscriptions"])
async def get_user_subscription(
    user_id: int = Path(..., description="User ID"),
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Get user's active subscription (Admin)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@router.post("/users/{user_id}", response_model=UserSubscriptionResponse, tags=["Admin - User Subscriptions"])
async def assign_subscription(
    user_id: int,
    subscription_data: UserSubscriptionCreate,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Assign subscription to user (Admin)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@router.patch("/users/{user_id}/cancel", tags=["Admin - User Subscriptions"])
async def cancel_subscription(
    user_id: int,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Cancel user subscription (Admin)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@router.get("/users/{user_id}/history", response_model=List[UserSubscriptionResponse], tags=["Admin - User Subscriptions"])
async def get_subscription_history(
    user_id: int,
    admin_user = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Get user subscription history (Admin)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user.id)
        .order_by(UserSubscription.created_at.desc())
    )
    return result.scalars().all()