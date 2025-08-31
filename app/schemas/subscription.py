from pydantic import BaseModel
from typing import Literal
from datetime import datetime


PlanType = Literal["monthly", "yearly", "free"]
SubscriptionStatus = Literal["active", "past_due", "canceled"]


class SubscriptionBase(BaseModel):
    plan_type: PlanType
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime


class SubscriptionCreate(SubscriptionBase):
    user_id: str  # UUID


class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus
    end_date: datetime


class SubscriptionResponse(SubscriptionBase):
    id: str  # UUID

    class Config:
        from_attributes = True
