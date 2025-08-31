from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .subscription import SubscriptionResponse


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    password: Optional[str] = None


class UserResponse(UserBase):
    id: str  # UUID
    email: str
    is_active: bool
    is_superuser: bool
    subscription: Optional[SubscriptionResponse] = None

    class Config:
        from_attributes = True
