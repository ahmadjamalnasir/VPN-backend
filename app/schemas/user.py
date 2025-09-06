from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    country: Optional[str] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    user_id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    country: Optional[str]
    is_active: bool
    is_premium: bool
    is_email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True