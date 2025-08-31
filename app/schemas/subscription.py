from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionBase(BaseModel):
    plan_name: str
    price: int
    duration_months: int
    max_devices: int
    features: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionUpdate(BaseModel):
    plan_name: Optional[str] = None
    price: Optional[int] = None
    duration_months: Optional[int] = None
    max_devices: Optional[int] = None
    features: Optional[str] = None
    expires_at: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    user_id: int

    class Config:
        from_attributes = True
