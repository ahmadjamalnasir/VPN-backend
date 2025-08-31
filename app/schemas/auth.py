from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=64)  # type: ignore

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str
    jti: str

class RefreshToken(BaseModel):
    refresh_token: str

class UserResponse(UserBase):
    id: str
    is_verified: bool
    created_at: datetime
    subscription_status: Optional[str] = None
    subscription_expiry: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(Token):
    user: UserResponse
