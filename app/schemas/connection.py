from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ConnectionSessionResponse(BaseModel):
    id: UUID
    server_hostname: Optional[str]
    server_location: Optional[str]
    client_ip: str
    status: str
    bytes_sent: int
    bytes_received: int
    total_bytes: int
    duration_seconds: int
    duration_formatted: str
    avg_speed_mbps: float
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ConnectionResponse(BaseModel):
    id: UUID
    user_id: UUID
    server_id: Optional[UUID]
    client_ip: str
    status: str
    bytes_sent: int
    bytes_received: int
    duration_seconds: int
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True