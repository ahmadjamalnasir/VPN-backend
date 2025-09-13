from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class SubscriptionPlanResponse(BaseModel):
    id: UUID
    plan_id: int
    name: str
    plan_type: str
    price: float
    duration_days: int
    is_premium: bool
    features: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID  # FIXED: This should be UUID to match database
    status: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    payment_method: Optional[str]
    created_at: datetime
    
    # Computed properties from model
    plan: Optional[SubscriptionPlanResponse] = None
    
    class Config:
        from_attributes = True

class AssignSubscriptionRequest(BaseModel):
    user_id: int  # Readable user ID
    plan_id: int  # Readable plan ID
    auto_renew: bool = True
    payment_method: Optional[str] = None