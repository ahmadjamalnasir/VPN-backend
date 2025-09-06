from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from uuid import UUID
from typing import Optional

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    email: str = Query(..., description="User email to get profile"),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile by email"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    is_active: bool = Query(..., description="Set user active status"),
    db: AsyncSession = Depends(get_db)
):
    """Update user active status"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    await db.commit()
    return {"message": f"User status updated to {'active' if is_active else 'inactive'}"}