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
    
    class Config:
        from_attributes = True

class UserSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan: SubscriptionPlanResponse
    status: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    payment_method: Optional[str]
    is_active: bool
    days_remaining: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignSubscriptionRequest(BaseModel):
    user_email: str
    plan_id: int
    auto_renew: bool = True
    payment_method: Optional[str] = None