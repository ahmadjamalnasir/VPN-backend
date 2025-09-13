from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.models.user_subscription import UserSubscription
from app.schemas.mobile import *
from app.services.auth import verify_token
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/profile", response_model=MobileUserProfileResponse)
async def get_mobile_profile(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile optimized for mobile"""
    result = await db.execute(
        select(User).options(selectinload(User.user_subscriptions))
        .where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get active subscription
    active_subscription = None
    for sub in user.user_subscriptions:
        if sub.status == "active" and sub.is_active:
            active_subscription = sub
            break
    
    return MobileUserProfileResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        is_premium=user.is_premium,
        subscription_status=active_subscription.status if active_subscription else "none",
        subscription_expires=active_subscription.end_date if active_subscription else None
    )

@router.get("/servers/quick", response_model=List[MobileServerResponse])
async def get_mobile_servers(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get optimized server list for mobile"""
    # Get user to check premium status
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get servers based on user subscription
    query = select(VPNServer).where(VPNServer.status == "active")
    if not user.is_premium:
        query = query.where(VPNServer.is_premium == False)
    
    query = query.order_by(VPNServer.current_load, VPNServer.ping).limit(20)
    result = await db.execute(query)
    servers = result.scalars().all()
    
    return [
        MobileServerResponse(
            id=server.id,
            name=f"{server.location.upper()} - {server.hostname}",
            location=server.location,
            ping=server.ping,
            load_percentage=int(server.current_load * 100),
            is_premium=server.is_premium,
            flag_emoji=get_flag_emoji(server.location)
        )
        for server in servers
    ]

@router.post("/connect/quick", response_model=MobileConnectResponse)
async def mobile_quick_connect(
    request: MobileConnectRequest,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Quick connect optimized for mobile"""
    # Get user
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check existing connection
    existing = await db.execute(
        select(Connection).where(
            and_(Connection.user_id == user.id, Connection.status == "connected")
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already connected")
    
    # Auto-select best server
    query = select(VPNServer).where(VPNServer.status == "active")
    if request.location:
        query = query.where(VPNServer.location == request.location)
    if not user.is_premium:
        query = query.where(VPNServer.is_premium == False)
    
    server_result = await db.execute(query.order_by(VPNServer.current_load).limit(1))
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="No servers available")
    
    # Create connection
    import secrets
    client_ip = f"10.0.{secrets.randbelow(255)}.{secrets.randbelow(254) + 1}"
    
    connection = Connection(
        user_id=user.id,
        server_id=server.id,
        client_ip=client_ip,
        client_public_key=request.device_id,  # Use device_id as key for mobile
        status="connected"
    )
    db.add(connection)
    
    # Update server load
    server.current_load = min(1.0, server.current_load + 0.1)
    
    await db.commit()
    await db.refresh(connection)
    
    return MobileConnectResponse(
        connection_id=connection.id,
        server_name=f"{server.location.upper()} - {server.hostname}",
        server_location=server.location,
        client_ip=client_ip,
        connected_at=connection.started_at,
        status="connected"
    )

@router.post("/disconnect")
async def mobile_disconnect(
    connection_id: str = Query(...),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect VPN for mobile"""
    # Find connection
    result = await db.execute(
        select(Connection).where(
            and_(
                Connection.id == connection_id,
                Connection.user_id == current_user_id,
                Connection.status == "connected"
            )
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Active connection not found")
    
    # Update connection
    ended_at = datetime.utcnow()
    duration = int((ended_at - connection.started_at).total_seconds())
    
    connection.status = "disconnected"
    connection.ended_at = ended_at
    connection.duration_seconds = duration
    
    # Update server load
    if connection.server:
        connection.server.current_load = max(0.0, connection.server.current_load - 0.1)
    
    await db.commit()
    
    return {"message": "Disconnected successfully", "duration_seconds": duration}

@router.get("/status")
async def get_connection_status(
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current connection status for mobile"""
    result = await db.execute(
        select(Connection).options(selectinload(Connection.server))
        .where(
            and_(
                Connection.user_id == current_user_id,
                Connection.status == "connected"
            )
        )
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        return {"status": "disconnected", "connection": None}
    
    duration = int((datetime.utcnow() - connection.started_at).total_seconds())
    
    return {
        "status": "connected",
        "connection": {
            "id": connection.id,
            "server_name": f"{connection.server.location.upper()} - {connection.server.hostname}",
            "server_location": connection.server.location,
            "client_ip": connection.client_ip,
            "duration_seconds": duration,
            "connected_at": connection.started_at
        }
    }

def get_flag_emoji(location: str) -> str:
    """Get flag emoji for location"""
    flags = {
        "us-east": "🇺🇸",
        "us-west": "🇺🇸", 
        "eu-west": "🇪🇺",
        "ap-south": "🇸🇬",
        "ca-central": "🇨🇦",
        "uk": "🇬🇧",
        "de": "🇩🇪",
        "fr": "🇫🇷",
        "jp": "🇯🇵"
    }
    return flags.get(location, "🌍")