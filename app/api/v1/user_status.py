from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.user_subscription import UserSubscription, SubscriptionStatus
from app.models.vpn_usage_log import VPNUsageLog
from app.schemas.subscription_new import UsageResponse, UserStatusResponse
from app.services.auth import verify_token
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter()

@router.get("/users/{user_id}/usage", response_model=UsageResponse, tags=["User Status"])
async def get_user_usage(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Show bandwidth/connection usage"""
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
    
    # Get total usage
    total_result = await db.execute(
        select(
            func.sum(VPNUsageLog.data_used_mb).label("total_data"),
            func.count(VPNUsageLog.id).label("total_connections")
        )
        .where(VPNUsageLog.user_id == user.id)
    )
    total_stats = total_result.first()
    
    # Get current month usage
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = await db.execute(
        select(
            func.sum(VPNUsageLog.data_used_mb).label("month_data"),
            func.count(VPNUsageLog.id).label("month_connections")
        )
        .where(
            and_(
                VPNUsageLog.user_id == user.id,
                VPNUsageLog.connected_at >= month_start
            )
        )
    )
    month_stats = month_result.first()
    
    return UsageResponse(
        total_data_mb=int(total_stats.total_data or 0),
        total_connections=int(total_stats.total_connections or 0),
        current_month_data_mb=int(month_stats.month_data or 0),
        current_month_connections=int(month_stats.month_connections or 0)
    )

@router.get("/users/{user_id}/status", response_model=UserStatusResponse, tags=["User Status"])
async def get_user_status(
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Active/inactive + subscription expiry (for mobile user)"""
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
    subscription_result = await db.execute(
        select(UserSubscription)
        .where(
            and_(
                UserSubscription.user_id == user.id,
                UserSubscription.status == SubscriptionStatus.active
            )
        )
        .order_by(UserSubscription.created_at.desc())
    )
    subscription = subscription_result.scalar_one_or_none()
    
    subscription_status = None
    subscription_expires = None
    days_remaining = None
    
    if subscription:
        subscription_status = subscription.status.value
        subscription_expires = subscription.end_date
        days_remaining = subscription.days_remaining
    
    return UserStatusResponse(
        user_id=user.user_id,
        is_active=user.is_active,
        is_premium=user.is_premium,
        subscription_status=subscription_status,
        subscription_expires=subscription_expires,
        days_remaining=days_remaining
    )