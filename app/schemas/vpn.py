from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

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
    
    class Config:
        from_attributes = True

class VPNConnectRequest(BaseModel):
    server_id: Optional[UUID] = None
    location: Optional[str] = None
    client_public_key: str

class VPNConnectionResponse(BaseModel):
    connection_id: UUID
    server: VPNServerResponse
    client_ip: str
    wg_config: str
    started_at: datetime
    status: str

class VPNDisconnectRequest(BaseModel):
    bytes_sent: int = 0
    bytes_received: int = 0

class VPNDisconnectResponse(BaseModel):
    message: str
    duration_seconds: int
    bytes_sent: int
    bytes_received: int
    total_bytes: int

class VPNStatusResponse(BaseModel):
    connection_id: UUID
    status: str  # connected, disconnected, connecting
    server: dict
    client_ip: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int
    bytes_sent: int
    bytes_received: int
    total_bytes: int
    connection_speed_mbps: float
    server_load: float
    ping_ms: int
    is_active: bool