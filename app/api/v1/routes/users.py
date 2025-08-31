from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.schemas.user import UserResponse
from app.schemas.subscription import SubscriptionResponse
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.database import get_db
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy.orm import joinedload

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch user with subscription
    user = db.query(User).options(
        joinedload(User.subscription)
    ).filter(User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
