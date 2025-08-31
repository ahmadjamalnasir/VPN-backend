from fastapi import APIRouter, Depends, HTTPException
from app.schemas.subscription import SubscriptionResponse
from app.models.subscription import Subscription
from app.services.auth_service import get_current_user
from app.models.user import User
from app.database import get_db
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter()


@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch subscription for user
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription
