from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.connection import Connection
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.connection import ConnectionSessionResponse
from app.services.auth import get_password_hash
from uuid import UUID
from typing import List, Optional

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    email: str = Query(..., description="User email"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/by-id/{user_id}", response_model=UserResponse)
async def get_user_by_readable_id(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/connections", response_model=List[ConnectionSessionResponse])
async def get_user_connections(
    email: str = Query(..., description="User email"),
    limit: int = Query(50, description="Number of sessions to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get user's past VPN connection history (Premium users only)"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Premium validation
    if not user.is_premium:
        raise HTTPException(status_code=403, detail="Premium subscription required to view connection history")
    
    # Get only disconnected (past) connections
    query = select(Connection).options(selectinload(Connection.server)).where(
        Connection.user_id == user.id,
        Connection.status == "disconnected"
    ).order_by(Connection.ended_at.desc()).limit(limit)
    
    result = await db.execute(query)
    connections = result.scalars().all()
    
    # Format sessions with stats
    sessions = []
    for conn in connections:
        total_bytes = conn.bytes_sent + conn.bytes_received
        
        # Calculate average speed (MB/s)
        avg_speed_mbps = 0.0
        if conn.duration_seconds > 0:
            avg_speed_mbps = round((total_bytes / (1024 * 1024)) / conn.duration_seconds, 2)
        
        # Format duration
        hours = conn.duration_seconds // 3600
        minutes = (conn.duration_seconds % 3600) // 60
        seconds = conn.duration_seconds % 60
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        session = ConnectionSessionResponse(
            id=conn.id,
            server_hostname=conn.server.hostname if conn.server else "Unknown",
            server_location=conn.server.location if conn.server else "Unknown",
            client_ip=conn.client_ip,
            status=conn.status,
            bytes_sent=conn.bytes_sent,
            bytes_received=conn.bytes_received,
            total_bytes=total_bytes,
            duration_seconds=conn.duration_seconds,
            duration_formatted=duration_formatted,
            avg_speed_mbps=avg_speed_mbps,
            started_at=conn.started_at,
            ended_at=conn.ended_at
        )
        sessions.append(session)
    
    return sessions

@router.put("/update", response_model=UserResponse)
async def update_user(
    email: str = Query(..., description="User email"),
    request: UserUpdateRequest = None,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.name:
        user.name = request.name
    if request.phone:
        user.phone = request.phone
    if request.password:
        user.hashed_password = get_password_hash(request.password)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/status/{user_id}")
async def update_user_status(
    user_id: int,
    is_active: bool = Query(..., description="Active status"),
    is_premium: bool = Query(None, description="Premium status"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    if is_premium is not None:
        user.is_premium = is_premium
    
    await db.commit()
    return {"message": "User status updated successfully"}