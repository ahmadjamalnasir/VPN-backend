from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from app.database import get_db
from app.models.user import User
from app.models.connection import Connection
from app.models.vpn_server import VPNServer
from app.schemas.analytics import *
from app.services.auth import verify_token
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

async def verify_admin_or_premium(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify user has admin or premium access"""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    if not user or (not user.is_superuser and not user.is_premium):
        raise HTTPException(status_code=403, detail="Premium or admin access required")
    return user

@router.get("/usage/personal", response_model=PersonalUsageResponse)
async def get_personal_usage(
    days: int = Query(30, ge=1, le=365),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get personal usage analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total connections
    total_connections = await db.scalar(
        select(func.count(Connection.id))
        .where(
            and_(
                Connection.user_id == current_user_id,
                Connection.created_at >= start_date
            )
        )
    )
    
    # Total data usage
    data_result = await db.execute(
        select(
            func.sum(Connection.bytes_sent + Connection.bytes_received).label("total_bytes"),
            func.sum(Connection.duration_seconds).label("total_duration")
        )
        .where(
            and_(
                Connection.user_id == current_user_id,
                Connection.status == "disconnected",
                Connection.created_at >= start_date
            )
        )
    )
    data_stats = data_result.first()
    
    total_bytes = data_stats.total_bytes or 0
    total_duration = data_stats.total_duration or 0
    
    # Daily usage breakdown
    daily_usage = await db.execute(
        text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as connections,
            SUM(bytes_sent + bytes_received) as bytes_used,
            SUM(duration_seconds) as duration
        FROM connections 
        WHERE user_id = :user_id 
        AND created_at >= :start_date
        AND status = 'disconnected'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
        """),
        {"user_id": current_user_id, "start_date": start_date}
    )
    
    daily_stats = [
        DailyUsageStats(
            date=row.date,
            connections=row.connections,
            data_mb=round((row.bytes_used or 0) / (1024 * 1024), 2),
            duration_minutes=round((row.duration or 0) / 60, 2)
        )
        for row in daily_usage.fetchall()
    ]
    
    return PersonalUsageResponse(
        period_days=days,
        total_connections=total_connections,
        total_data_gb=round(total_bytes / (1024 * 1024 * 1024), 2),
        total_duration_hours=round(total_duration / 3600, 2),
        daily_usage=daily_stats
    )

@router.get("/servers/performance", response_model=List[ServerPerformanceResponse])
async def get_server_performance(
    user: User = Depends(verify_admin_or_premium),
    db: AsyncSession = Depends(get_db)
):
    """Get server performance analytics"""
    server_stats = await db.execute(
        text("""
        SELECT 
            s.id,
            s.hostname,
            s.location,
            s.current_load,
            s.ping,
            s.is_premium,
            COUNT(c.id) as total_connections,
            AVG(c.duration_seconds) as avg_session_duration,
            SUM(c.bytes_sent + c.bytes_received) as total_data
        FROM vpn_servers s
        LEFT JOIN connections c ON s.id = c.server_id 
        WHERE s.status = 'active'
        GROUP BY s.id, s.hostname, s.location, s.current_load, s.ping, s.is_premium
        ORDER BY total_connections DESC
        """)
    )
    
    return [
        ServerPerformanceResponse(
            server_id=row.id,
            hostname=row.hostname,
            location=row.location,
            current_load=row.current_load,
            ping=row.ping,
            is_premium=row.is_premium,
            total_connections=row.total_connections or 0,
            avg_session_minutes=round((row.avg_session_duration or 0) / 60, 2),
            total_data_gb=round((row.total_data or 0) / (1024 * 1024 * 1024), 2)
        )
        for row in server_stats.fetchall()
    ]

@router.get("/system/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    user: User = Depends(verify_admin_or_premium),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide analytics overview"""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Current active connections
    active_connections = await db.scalar(
        select(func.count(Connection.id)).where(Connection.status == "connected")
    )
    
    # 24h statistics
    stats_24h = await db.execute(
        select(
            func.count(Connection.id).label("connections"),
            func.sum(Connection.bytes_sent + Connection.bytes_received).label("data_bytes")
        )
        .where(Connection.created_at >= last_24h)
    )
    stats_24h = stats_24h.first()
    
    # 7d statistics
    stats_7d = await db.execute(
        select(
            func.count(Connection.id).label("connections"),
            func.sum(Connection.bytes_sent + Connection.bytes_received).label("data_bytes")
        )
        .where(Connection.created_at >= last_7d)
    )
    stats_7d = stats_7d.first()
    
    # Server health
    server_health = await db.execute(
        select(
            func.count(VPNServer.id).label("total"),
            func.sum(func.case((VPNServer.status == "active", 1), else_=0)).label("active"),
            func.avg(VPNServer.current_load).label("avg_load")
        )
    )
    server_health = server_health.first()
    
    return SystemOverviewResponse(
        active_connections=active_connections,
        connections_24h=stats_24h.connections or 0,
        data_transfer_24h_gb=round((stats_24h.data_bytes or 0) / (1024 * 1024 * 1024), 2),
        connections_7d=stats_7d.connections or 0,
        data_transfer_7d_gb=round((stats_7d.data_bytes or 0) / (1024 * 1024 * 1024), 2),
        total_servers=server_health.total or 0,
        active_servers=server_health.active or 0,
        avg_server_load=round((server_health.avg_load or 0) * 100, 1)
    )

@router.get("/locations/usage", response_model=List[LocationUsageResponse])
async def get_location_usage(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(verify_admin_or_premium),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics by server location"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    location_stats = await db.execute(
        text("""
        SELECT 
            s.location,
            COUNT(c.id) as total_connections,
            COUNT(DISTINCT c.user_id) as unique_users,
            SUM(c.bytes_sent + c.bytes_received) as total_data,
            AVG(c.duration_seconds) as avg_duration
        FROM vpn_servers s
        LEFT JOIN connections c ON s.id = c.server_id 
        WHERE c.created_at >= :start_date OR c.created_at IS NULL
        GROUP BY s.location
        ORDER BY total_connections DESC
        """),
        {"start_date": start_date}
    )
    
    return [
        LocationUsageResponse(
            location=row.location,
            total_connections=row.total_connections or 0,
            unique_users=row.unique_users or 0,
            total_data_gb=round((row.total_data or 0) / (1024 * 1024 * 1024), 2),
            avg_session_minutes=round((row.avg_duration or 0) / 60, 2)
        )
        for row in location_stats.fetchall()
    ]