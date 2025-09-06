from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.models.user import User
from app.schemas.vpn import VPNServerResponse, VPNConnectRequest, VPNConnectionResponse, VPNDisconnectRequest
from app.schemas.connection import ConnectionResponse
from uuid import UUID
from datetime import datetime
from typing import List, Optional
import secrets

router = APIRouter()

@router.get("/servers", response_model=List[VPNServerResponse])
async def get_vpn_servers(
    location: Optional[str] = Query(None, description="Filter by location"),
    status: str = Query("active", description="Server status filter"),
    db: AsyncSession = Depends(get_db)
):
    """Get VPN servers with filters"""
    query = select(VPNServer).where(VPNServer.status == status)
    if location:
        query = query.where(VPNServer.location == location)
    
    result = await db.execute(query.order_by(VPNServer.current_load, VPNServer.ping))
    servers = result.scalars().all()
    return servers

@router.get("/servers/{server_id}", response_model=VPNServerResponse)
async def get_vpn_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get specific VPN server"""
    result = await db.execute(select(VPNServer).where(VPNServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

@router.post("/connect", response_model=VPNConnectionResponse)
async def connect_vpn(
    request: VPNConnectRequest,
    user_email: str = Query(..., description="User email for connection"),
    db: AsyncSession = Depends(get_db)
):
    """Connect user to VPN server"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    else:
        query = select(VPNServer).where(VPNServer.status == "active")
        if request.location:
            query = query.where(VPNServer.location == request.location)
        server_result = await db.execute(query.order_by(VPNServer.current_load).limit(1))
    
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="No available servers")
    
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

@router.post("/disconnect", response_model=ConnectionResponse)
async def disconnect_vpn(
    connection_id: UUID = Query(..., description="Connection ID to disconnect"),
    user_email: str = Query(..., description="User email"),
    bytes_sent: int = Query(0, description="Bytes sent during session"),
    bytes_received: int = Query(0, description="Bytes received during session"),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect VPN connection"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    # Update connection
    connection.status = "disconnected"
    connection.ended_at = datetime.utcnow()
    connection.bytes_sent = bytes_sent
    connection.bytes_received = bytes_received
    
    # Update server load
    if connection.server:
        connection.server.current_load = max(0.0, connection.server.current_load - 0.1)
    
    await db.commit()
    await db.refresh(connection)
    return connection

@router.get("/connections", response_model=List[ConnectionResponse])
async def get_user_connections(
    user_email: str = Query(..., description="User email to get connections"),
    status: Optional[str] = Query(None, description="Filter by connection status"),
    db: AsyncSession = Depends(get_db)
):
    """Get user connection history"""
    # Find user
    user_result = await db.execute(select(User).where(User.email == user_email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get connections
    query = select(Connection).where(Connection.user_id == user.id)
    if status:
        query = query.where(Connection.status == status)
    
    result = await db.execute(query.order_by(Connection.created_at.desc()))
    connections = result.scalars().all()
    return connections