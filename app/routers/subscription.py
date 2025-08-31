from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import SubscriptionStatusResponse, UserResponse
from app.services.subscription_service import subscription_service
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1", tags=["Subscriptions"])

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user info with subscription details"""
    user = await subscription_service.get_user_with_subscription(db, str(current_user.id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/subscriptions/status/{user_id}", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subscription status for a user"""
    # Only allow users to view their own subscription or superusers to view any subscription
    if str(current_user.id) != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this subscription"
        )

    subscription = await subscription_service.get_user_subscription_status(db, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for this user"
        )

    return {
        "user_id": user_id,
        "subscription": subscription
    }
