from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class MobileUserProfileResponse(BaseModel):
    user_id: int
    name: str
    email: str
    is_premium: bool
    subscription_status: str
    subscription_expires: Optional[datetime]

class MobileServerResponse(BaseModel):
    id: UUID
    name: str
    location: str
    ping: int
    load_percentage: int
    is_premium: bool
    flag_emoji: str

class MobileConnectRequest(BaseModel):
    device_id: str
    location: Optional[str] = None

class MobileConnectResponse(BaseModel):
    connection_id: UUID
    server_name: str
    server_location: str
    client_ip: str
    connected_at: datetime
    status: str