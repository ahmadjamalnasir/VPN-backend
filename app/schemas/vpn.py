from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VPNServerInfo(BaseModel):
    id: str  # UUID
    hostname: str
    ip_address: str
    location: str
    endpoint: str  # ip:port

    class Config:
        from_attributes = True


class VPNConnectionResponse(BaseModel):
    connection_id: str  # UUID
    server: VPNServerInfo
    wg_config: str
    started_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VPNConnectionSummary(BaseModel):
    connection_id: str  # UUID
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    bytes_sent: int
    bytes_received: int
    total_bytes: int

    class Config:
        from_attributes = True
