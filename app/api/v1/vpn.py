from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.schemas.vpn import VPNServerResponse, VPNConnectRequest, VPNConnectionResponse, VPNDisconnectResponse
from app.services.auth import verify_token
from app.services.vpn_service import generate_wireguard_keys
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import secrets

router = APIRouter()

# MOBILE ENDPOINTS

@router.post("/connect", response_model=VPNConnectionResponse)
async def connect_vpn(
    user_id: int = Query(..., description="User ID"),
    request: VPNConnectRequest = ...,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Connect to VPN server (Mobile)"""
    # Find user by readable ID
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user can connect (own connection only)
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check for existing connection
    existing = await db.execute(
        select(Connection).where(
            and_(Connection.user_id == user.id, Connection.status == "connected")
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already connected to a server")
    
    # Find server
    server = None
    if request.server_id:
        server_result = await db.execute(select(VPNServer).where(VPNServer.id == request.server_id))
        server = server_result.scalar_one_or_none()
        if not server or server.status != "active":
            raise HTTPException(status_code=404, detail="Server not available")
    else:
        # Auto-select best server
        query = select(VPNServer).where(VPNServer.status == "active")
        if request.location:
            query = query.where(VPNServer.location == request.location)
        # Allow auto-selection from all servers (premium check happens below)
        
        server_result = await db.execute(query.order_by(VPNServer.current_load).limit(1))
        server = server_result.scalar_one_or_none()
        if not server:
            raise HTTPException(status_code=404, detail="No servers available")
    
    # Check premium access
    if server.is_premium and not user.is_premium:
        raise HTTPException(
            status_code=403, 
            detail="Upgrade to Premium required to access this server. Visit your account settings to upgrade."
        )
    
    # Generate client configuration
    client_ip = f"10.0.{secrets.randbelow(255)}.{secrets.randbelow(254) + 1}"
    private_key, public_key = generate_wireguard_keys()
    
    # Create connection record
    connection = Connection(
        user_id=user.id,
        server_id=server.id,
        client_ip=client_ip,
        client_public_key=public_key,
        status="connected"
    )
    db.add(connection)
    
    # Update server load
    server.current_load = min(1.0, server.current_load + 0.1)
    
    await db.commit()
    await db.refresh(connection)
    
    # Generate WireGuard config
    wg_config = f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server.public_key}
Endpoint = {server.endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25"""
    
    return VPNConnectionResponse(
        connection_id=connection.id,
        server={
            "id": server.id,
            "hostname": server.hostname,
            "location": server.location,
            "ip_address": server.ip_address,
            "is_premium": server.is_premium
        },
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
    """Disconnect from VPN server (Mobile)"""
    # Find user
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user can disconnect (own connection only)
    if str(user.id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find connection
    result = await db.execute(
        select(Connection).options(selectinload(Connection.server)).where(
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
    
    # Update connection with stats
    ended_at = datetime.utcnow()
    duration = int((ended_at - connection.started_at).total_seconds())
    
    connection.status = "disconnected"
    connection.ended_at = ended_at
    connection.duration_seconds = duration
    connection.bytes_sent = bytes_sent
    connection.bytes_received = bytes_received
    
    # Update server load
    if connection.server:
        connection.server.current_load = max(0.0, connection.server.current_load - 0.1)
    
    await db.commit()
    
    return VPNDisconnectResponse(
        message="Disconnected successfully",
        duration_seconds=duration,
        bytes_sent=bytes_sent,
        bytes_received=bytes_received,
        total_bytes=bytes_sent + bytes_received
    )

# MOBILE ENDPOINTS
@router.get("/servers", response_model=List[VPNServerResponse], tags=["Mobile - VPN"])
async def get_vpn_servers(
    location: Optional[str] = Query(None, description="Filter by location"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status"),
    max_load: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum server load (0.0-1.0)"),
    max_ping: Optional[int] = Query(None, ge=0, description="Maximum ping in milliseconds"),
    skip: int = Query(0, ge=0, description="Skip records for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records for pagination"),
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get VPN servers with filtering (Mobile)"""
    # Get user to check premium status
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query - only active servers for mobile users
    query = select(VPNServer).where(VPNServer.status == "active")
    
    # Apply filters
    if location:
        query = query.where(VPNServer.location.ilike(f"%{location}%"))
    
    if is_premium is not None:
        query = query.where(VPNServer.is_premium == is_premium)
    # Allow all users to view all servers (premium check happens at connection time)
    
    if max_load is not None:
        query = query.where(VPNServer.current_load <= max_load)
    
    if max_ping is not None:
        query = query.where(VPNServer.ping <= max_ping)
    
    # Apply pagination and ordering by performance
    query = query.offset(skip).limit(limit).order_by(VPNServer.current_load, VPNServer.ping)
    
    result = await db.execute(query)
    servers = result.scalars().all()
    return servers