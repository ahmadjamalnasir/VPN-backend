from fastapi import APIRouter, Depends
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/connect", response_model=VPNConnectionResponse)
async def connect_vpn(
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user has active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    # Check if user already has an active connection
    active_connection = db.query(VPNConnection).filter(
        VPNConnection.user_id == current_user.id,
        VPNConnection.status == "connected"
    ).first()
    
    if active_connection:
        raise HTTPException(status_code=400, detail="Active connection already exists")
    
    # Find optimal server
    query = db.query(VPNServer).filter(VPNServer.status == "active")
    
    if location:
        query = query.filter(VPNServer.location == location)
    
    server = query.order_by(
        VPNServer.current_load.asc(),
        VPNServer.ping.asc()
    ).first()
    
    if not server:
        raise HTTPException(status_code=503, detail="No available servers")
    
    # Generate client IP and keys
    client_config = generate_wireguard_config(server)
    
    # Create connection record
    connection = VPNConnection(
        user_id=current_user.id,
        server_id=server.id,
        client_ip=client_config["client_ip"],
        client_public_key=client_config["client_public_key"],
        status="connected",
    )
    
    db.add(connection)
    
    # Update server load
    server.current_load = min(1.0, server.current_load + 0.1)
    
    db.commit()
    db.refresh(connection)
    
    return {
        "connection_id": str(connection.id),
        "server": {
            "id": str(server.id),
            "hostname": server.hostname,
            "ip_address": server.ip_address,
            "location": server.location,
            "endpoint": server.endpoint
        },
        "wg_config": client_config["wg_config"],
        "started_at": connection.started_at,
        "expires_at": None  # Can be set based on subscription plan
    }

@router.post("/disconnect/{connection_id}", response_model=VPNConnectionSummary)
async def disconnect_vpn(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find active connection
    connection = db.query(VPNConnection).filter(
        VPNConnection.id == connection_id,
        VPNConnection.user_id == current_user.id,
        VPNConnection.status == "connected"
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Active connection not found")
    
    now = datetime.utcnow()
    
    # Update connection
    connection.status = "disconnected"
    connection.ended_at = now
    connection.bytes_sent = connection.bytes_sent or 0  # Ensure not None
    connection.bytes_received = connection.bytes_received or 0  # Ensure not None
    
    # Update server load
    if connection.server:
        connection.server.current_load = max(0.0, connection.server.current_load - 0.1)
    
    db.commit()
    db.refresh(connection)
    
    # Calculate duration
    duration = int((connection.ended_at - connection.started_at).total_seconds())
    
    return {
        "connection_id": str(connection.id),
        "started_at": connection.started_at,
        "ended_at": connection.ended_at,
        "duration_seconds": duration,
        "bytes_sent": connection.bytes_sent,
        "bytes_received": connection.bytes_received,
        "total_bytes": connection.bytes_sent + connection.bytes_received
    }
