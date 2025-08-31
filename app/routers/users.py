from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse
from app.services import auth_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(auth_service.get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    # If password is provided, update it
    if user_update.password is not None:
        current_user.hashed_password = auth_service.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    current_user.is_active = False
    db.commit()
    return {"message": "User deactivated successfully"}
