from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VPNServerBase(BaseModel):
    name: str
    location: str
    ip_address: str
    public_key: str
    port: int


class VPNServerCreate(VPNServerBase):
    pass


class VPNServerUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    public_key: Optional[str] = None
    port: Optional[int] = None
    is_active: Optional[bool] = None
    load: Optional[int] = None


class VPNServerResponse(VPNServerBase):
    id: int
    is_active: bool
    load: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VPNConnectionConfig(BaseModel):
    server_ip: str
    server_port: int
    server_public_key: str
    client_private_key: str
    client_ip: str
    dns: list[str]
