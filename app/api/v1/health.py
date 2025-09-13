from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.database import get_db, engine
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.schemas.health import *
from datetime import datetime
import redis.asyncio as redis
from app.core.config import get_settings
import psutil
import asyncio

router = APIRouter()
settings = get_settings()

@router.get("/status", response_model=HealthStatusResponse)
async def get_health_status(db: AsyncSession = Depends(get_db)):
    """Get comprehensive system health status"""
    
    # Database health
    db_healthy = True
    db_response_time = 0
    try:
        start_time = datetime.now()
        await db.execute(text("SELECT 1"))
        db_response_time = (datetime.now() - start_time).total_seconds() * 1000
    except Exception:
        db_healthy = False
    
    # Redis health
    redis_healthy = True
    redis_response_time = 0
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        start_time = datetime.now()
        await redis_client.ping()
        redis_response_time = (datetime.now() - start_time).total_seconds() * 1000
        await redis_client.close()
    except Exception:
        redis_healthy = False
    
    # Server statistics
    active_servers = await db.scalar(
        select(func.count(VPNServer.id)).where(VPNServer.status == "active")
    )
    
    active_connections = await db.scalar(
        select(func.count(Connection.id)).where(Connection.status == "connected")
    )
    
    # System resources
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Overall health
    overall_healthy = db_healthy and redis_healthy and cpu_usage < 90 and memory.percent < 90
    
    return HealthStatusResponse(
        status="healthy" if overall_healthy else "degraded",
        timestamp=datetime.utcnow(),
        database=DatabaseHealth(
            status="healthy" if db_healthy else "unhealthy",
            response_time_ms=round(db_response_time, 2)
        ),
        redis=RedisHealth(
            status="healthy" if redis_healthy else "unhealthy",
            response_time_ms=round(redis_response_time, 2)
        ),
        servers=ServerHealth(
            active_count=active_servers or 0,
            total_connections=active_connections or 0
        ),
        system=SystemHealth(
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent
        )
    )

@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    """Get detailed system metrics"""
    
    # Connection metrics
    connection_metrics = await db.execute(
        text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'connected' THEN 1 END) as active,
            AVG(duration_seconds) as avg_duration,
            SUM(bytes_sent + bytes_received) as total_bytes
        FROM connections 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
    )
    conn_stats = connection_metrics.first()
    
    # Server load distribution
    server_loads = await db.execute(
        select(
            VPNServer.location,
            func.avg(VPNServer.current_load).label("avg_load"),
            func.count(VPNServer.id).label("server_count")
        )
        .where(VPNServer.status == "active")
        .group_by(VPNServer.location)
    )
    
    load_distribution = [
        LocationLoad(
            location=row.location,
            avg_load_percent=round(row.avg_load * 100, 1),
            server_count=row.server_count
        )
        for row in server_loads.fetchall()
    ]
    
    return SystemMetricsResponse(
        connections_24h=conn_stats.total or 0,
        active_connections=conn_stats.active or 0,
        avg_session_duration_minutes=round((conn_stats.avg_duration or 0) / 60, 2),
        data_transfer_24h_gb=round((conn_stats.total_bytes or 0) / (1024**3), 2),
        server_load_distribution=load_distribution
    )

@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancer health checks"""
    return {"status": "ok", "timestamp": datetime.utcnow()}

@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe - checks if service can handle requests"""
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        
        # Check if we have active servers
        server_count = await db.scalar(
            select(func.count(VPNServer.id)).where(VPNServer.status == "active")
        )
        
        if server_count == 0:
            return {"status": "not_ready", "reason": "no_active_servers"}
        
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}

@router.get("/live")
async def liveness():
    """Liveness probe - checks if service is alive"""
    return {"status": "alive", "timestamp": datetime.utcnow()}