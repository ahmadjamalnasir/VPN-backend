from pydantic import BaseModel
from typing import List
from datetime import datetime

class DatabaseHealth(BaseModel):
    status: str
    response_time_ms: float

class RedisHealth(BaseModel):
    status: str
    response_time_ms: float

class ServerHealth(BaseModel):
    active_count: int
    total_connections: int

class SystemHealth(BaseModel):
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float

class HealthStatusResponse(BaseModel):
    status: str
    timestamp: datetime
    database: DatabaseHealth
    redis: RedisHealth
    servers: ServerHealth
    system: SystemHealth

class LocationLoad(BaseModel):
    location: str
    avg_load_percent: float
    server_count: int

class SystemMetricsResponse(BaseModel):
    connections_24h: int
    active_connections: int
    avg_session_duration_minutes: float
    data_transfer_24h_gb: float
    server_load_distribution: List[LocationLoad]