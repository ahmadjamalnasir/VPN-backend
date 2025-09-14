from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# Subscription Plan Schemas
class SubscriptionPlanCreate(BaseModel):
    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    price_usd: Decimal = Field(..., description="Price in USD")
    duration_days: int = Field(..., description="Duration in days")
    features: Optional[Dict[str, Any]] = Field(None, description="Plan features")

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_usd: Optional[Decimal] = None
    duration_days: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    price_usd: Decimal
    duration_days: int
    features: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User Subscription Schemas
class UserSubscriptionCreate(BaseModel):
    plan_id: UUID
    auto_renew: bool = False

class UserSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID
    start_date: datetime
    end_date: datetime
    status: str
    auto_renew: bool
    created_at: datetime
    updated_at: datetime
    plan: Optional[SubscriptionPlanResponse] = None
    
    class Config:
        from_attributes = True

# Payment Schemas
class PaymentInitiate(BaseModel):
    plan_id: UUID
    payment_method: str
    amount_usd: Decimal

class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: UUID
    amount_usd: Decimal
    payment_method: Optional[str]
    status: str
    transaction_ref: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Usage Schemas
class UsageResponse(BaseModel):
    total_data_mb: int
    total_connections: int
    current_month_data_mb: int
    current_month_connections: int

class UserStatusResponse(BaseModel):
    user_id: int
    is_active: bool
    is_premium: bool
    subscription_status: Optional[str]
    subscription_expires: Optional[datetime]
    days_remaining: Optional[int]