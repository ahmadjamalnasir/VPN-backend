from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ConnectionResponse(BaseModel):
    id: UUID
    user_id: UUID
    server_id: Optional[UUID]
    client_ip: str
    status: str
    bytes_sent: int
    bytes_received: int
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True