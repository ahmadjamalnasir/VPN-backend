from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    premium_users: int
    total_servers: int
    active_servers: int
    active_connections: int
    daily_connections: int

class AdminUserResponse(BaseModel):
    id: UUID
    user_id: int
    name: str
    email: str
    phone: Optional[str]
    country: Optional[str]
    is_active: bool
    is_premium: bool
    is_superuser: bool
    is_email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminUserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    is_superuser: Optional[bool] = None

class CreateVPNServerRequest(BaseModel):
    hostname: str
    location: str
    ip_address: str
    endpoint: str
    public_key: str
    available_ips: str
    is_premium: bool = False

class UpdateVPNServerRequest(BaseModel):
    status: Optional[str] = None
    is_premium: Optional[bool] = None
    current_load: Optional[float] = None

class VPNServerResponse(BaseModel):
    id: UUID
    hostname: str
    location: str
    ip_address: str
    endpoint: str
    status: str
    current_load: float
    ping: int
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True