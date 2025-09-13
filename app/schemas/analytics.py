from pydantic import BaseModel
from typing import List
from datetime import date
from uuid import UUID

class DailyUsageStats(BaseModel):
    date: date
    connections: int
    data_mb: float
    duration_minutes: float

class PersonalUsageResponse(BaseModel):
    period_days: int
    total_connections: int
    total_data_gb: float
    total_duration_hours: float
    daily_usage: List[DailyUsageStats]

class ServerPerformanceResponse(BaseModel):
    server_id: UUID
    hostname: str
    location: str
    current_load: float
    ping: int
    is_premium: bool
    total_connections: int
    avg_session_minutes: float
    total_data_gb: float

class SystemOverviewResponse(BaseModel):
    active_connections: int
    connections_24h: int
    data_transfer_24h_gb: float
    connections_7d: int
    data_transfer_7d_gb: float
    total_servers: int
    active_servers: int
    avg_server_load: float

class LocationUsageResponse(BaseModel):
    location: str
    total_connections: int
    unique_users: int
    total_data_gb: float
    avg_session_minutes: float