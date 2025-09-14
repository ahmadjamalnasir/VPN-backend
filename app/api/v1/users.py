from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserProfileResponse
from app.services.auth import verify_token

router = APIRouter()

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile for mobile app"""
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        country=user.country,
        is_premium=user.is_premium,
        is_email_verified=user.is_email_verified,
        subscription_status="none",
        subscription_expires=None,
        created_at=user.created_at
    )