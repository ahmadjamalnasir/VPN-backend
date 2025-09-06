from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.auth import get_password_hash
from uuid import UUID

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    email: str = Query(..., description="User email"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/by-id/{user_id}", response_model=UserResponse)
async def get_user_by_readable_id(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/update", response_model=UserResponse)
async def update_user(
    email: str = Query(..., description="User email"),
    request: UserUpdateRequest = None,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.name:
        user.name = request.name
    if request.phone:
        user.phone = request.phone
    if request.password:
        user.hashed_password = get_password_hash(request.password)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/status/{user_id}")
async def update_user_status(
    user_id: int,
    is_active: bool = Query(..., description="Active status"),
    is_premium: bool = Query(None, description="Premium status"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    if is_premium is not None:
        user.is_premium = is_premium
    
    await db.commit()
    return {"message": "User status updated successfully"}