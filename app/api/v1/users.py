from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.connection import Connection
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.connection import ConnectionSessionResponse
from app.services.auth import get_password_hash, verify_token
from uuid import UUID
from typing import List

router = APIRouter()

@router.get("/connections", response_model=List[ConnectionSessionResponse])
async def get_user_connections(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(50, description="Number of sessions to return"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user's past VPN connection history (Premium users only)"""
    # Find user by readable ID
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user can access this data (own data or admin)
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Premium validation
    if not user.is_premium:
        raise HTTPException(status_code=403, detail="Premium subscription required")
    
    # Get past connections
    query = select(Connection).options(selectinload(Connection.server)).where(
        Connection.user_id == user.id,
        Connection.status == "disconnected"
    ).order_by(Connection.ended_at.desc()).limit(limit)
    
    result = await db.execute(query)
    connections = result.scalars().all()
    
    # Format sessions
    sessions = []
    for conn in connections:
        total_bytes = conn.bytes_sent + conn.bytes_received
        avg_speed_mbps = 0.0
        if conn.duration_seconds > 0:
            avg_speed_mbps = round((total_bytes / (1024 * 1024)) / conn.duration_seconds, 2)
        
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
    user_id: int = Query(..., description="User ID"),
    request: UserUpdateRequest = ...,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile by user ID"""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user can update this profile
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if request.name:
        user.name = request.name
    if request.phone:
        user.phone = request.phone
    if hasattr(request, 'country') and request.country:
        user.country = request.country
    if request.password:
        user.hashed_password = get_password_hash(request.password)
    
    await db.commit()
    await db.refresh(user)
    return user