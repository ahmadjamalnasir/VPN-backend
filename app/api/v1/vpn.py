from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.user import User
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.schemas.vpn import VPNServerResponse, VPNConnectRequest, VPNConnectionResponse, VPNDisconnectResponse
from app.services.auth import verify_token
from uuid import UUID
from datetime import datetime
from typing import List, Optional
import secrets

router = APIRouter()

@router.get("/servers", response_model=List[VPNServerResponse])
async def get_vpn_servers(
    location: Optional[str] = Query(None, description="Filter by location"),
    is_premium: Optional[bool] = Query(None, description="Filter premium servers"),
    db: AsyncSession = Depends(get_db)
):
    """Get available VPN servers"""
    query = select(VPNServer).where(VPNServer.status == "active")
    if location:
        query = query.where(VPNServer.location == location)
    if is_premium is not None:
        query = query.where(VPNServer.is_premium == is_premium)
    
    result = await db.execute(query.order_by(VPNServer.current_load, VPNServer.ping))
    servers = result.scalars().all()
    return servers

@router.post("/connect", response_model=VPNConnectionResponse)
async def connect_vpn(
    request: VPNConnectRequest,
    user_id: int,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Connect user to VPN server"""
    # Find user by readable ID
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate user profile
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    if not user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email verification required")
    
    # Check for existing active connection
    existing = await db.execute(
        select(Connection).where(
            and_(Connection.user_id == user.id, Connection.status == "connected")
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has an active connection")
    
    # Find server
    if request.server_id:
        server_result = await db.execute(select(VPNServer).where(VPNServer.id == request.server_id))
        server = server_result.scalar_one_or_none()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
    else:
        # Auto-select server based on user premium status
        query = select(VPNServer).where(VPNServer.status == "active")
        if request.location:
            query = query.where(VPNServer.location == request.location)
        
        # Premium users can access premium servers, free users only free servers
        if not user.is_premium:
            query = query.where(VPNServer.is_premium == False)
        
        server_result = await db.execute(query.order_by(VPNServer.current_load).limit(1))
        server = server_result.scalar_one_or_none()
        if not server:
            raise HTTPException(status_code=404, detail="No available servers for your subscription")
    
    # Validate premium server access
    if server.is_premium and not user.is_premium:
        raise HTTPException(status_code=403, detail="Premium subscription required for this server")
    
    # Generate client IP
    client_ip = f"10.0.{secrets.randbelow(255)}.{secrets.randbelow(254) + 1}"
    
    # Create connection
    connection = Connection(
        user_id=user.id,
        server_id=server.id,
        client_ip=client_ip,
        client_public_key=request.client_public_key,
        status="connected"
    )
    db.add(connection)
    
    # Update server load
    server.current_load = min(1.0, server.current_load + 0.1)
    
    await db.commit()
    await db.refresh(connection)
    
    # Generate WireGuard config
    wg_config = f"""[Interface]
PrivateKey = <client_private_key>
Address = {client_ip}/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server.public_key}
Endpoint = {server.endpoint}
AllowedIPs = 0.0.0.0/0"""
    
    return VPNConnectionResponse(
        connection_id=connection.id,
        server=server,
        client_ip=client_ip,
        wg_config=wg_config,
        started_at=connection.started_at,
        status=connection.status
    )

@router.post("/disconnect", response_model=VPNDisconnectResponse)
async def disconnect_vpn(
    connection_id: UUID = Query(..., description="Connection ID"),
    user_id: int = Query(..., description="User ID"),
    bytes_sent: int = Query(0, description="Bytes sent"),
    bytes_received: int = Query(0, description="Bytes received"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect VPN connection"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify access
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find connection
    result = await db.execute(
        select(Connection).where(
            and_(
                Connection.id == connection_id,
                Connection.user_id == user.id,
                Connection.status == "connected"
            )
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Active connection not found")
    
    # Calculate duration and stats
    ended_at = datetime.utcnow()
    duration = int((ended_at - connection.started_at).total_seconds())
    total_bytes = bytes_sent + bytes_received
    
    # Calculate speeds
    avg_speed_mbps = 0.0
    if duration > 0:
        avg_speed_mbps = round((total_bytes / (1024 * 1024)) / duration, 2)
    
    # Format duration
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Update connection
    connection.status = "disconnected"
    connection.ended_at = ended_at
    connection.bytes_sent = bytes_sent
    connection.bytes_received = bytes_received
    connection.duration_seconds = duration
    
    # Update server load
    if connection.server:
        connection.server.current_load = max(0.0, connection.server.current_load - 0.1)
    
    await db.commit()
    
    # Prepare session stats
    session_stats = {
        "duration_seconds": duration,
        "duration_formatted": duration_formatted,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "total_bytes": total_bytes,
        "total_data_mb": round(total_bytes / (1024 * 1024), 2),
        "avg_speed_mbps": avg_speed_mbps,
        "server_location": connection.server.location if connection.server else "Unknown",
        "client_ip": connection.client_ip
    }
    
    return VPNDisconnectResponse(
        connection_id=connection.id,
        session_stats=session_stats,
        message="VPN disconnected successfully. Session stats recorded."
    )