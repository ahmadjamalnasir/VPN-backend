from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID

class SubscriptionBase(BaseModel):
    plan_type: Literal["monthly", "yearly", "free"]
    status: Literal["active", "past_due", "canceled"]

class SubscriptionCreate(SubscriptionBase):
    start_date: datetime
    end_date: datetime

class SubscriptionResponse(SubscriptionBase):
    id: UUID
    user_id: UUID
    start_date: datetime
    end_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True