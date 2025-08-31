from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    plan_type: str  # monthly, yearly
    currency: str = "usd"
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, Any]] = None


class PaymentCreateResponse(BaseModel):
    checkout_url: Optional[str] = None
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None


class PaymentLogResponse(BaseModel):
    id: str
    payment_intent_id: Optional[str]
    checkout_session_id: Optional[str]
    amount: str
    currency: str
    status: str
    payment_method: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
