from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.user import User
from app.models.connection import Connection
from app.services.auth import verify_token
from datetime import datetime
import json
import asyncio
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        connection_id = f"ws_{user_id}_{datetime.now().timestamp()}"
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        logger.info(f"WebSocket connected: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(connection_id, user_id)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

manager = ConnectionManager()

async def verify_websocket_token(token: str, db: AsyncSession) -> User:
    """Verify JWT token for WebSocket connection"""
    try:
        from jose import jwt, JWTError
        from app.core.config import get_settings
        
        settings = get_settings()
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/connection-status")
async def websocket_connection_status(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time connection status updates"""
    try:
        # Verify token
        user = await verify_websocket_token(token, db)
        
        # Connect WebSocket
        connection_id = await manager.connect(websocket, str(user.id))
        
        # Send initial status
        await send_connection_status(user.id, db)
        
        try:
            while True:
                # Keep connection alive and listen for client messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "get_status":
                    await send_connection_status(user.id, db)
                
        except WebSocketDisconnect:
            manager.disconnect(connection_id, str(user.id))
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")

async def send_connection_status(user_id: str, db: AsyncSession):
    """Send current connection status to user"""
    try:
        # Get active connection
        result = await db.execute(
            select(Connection).where(
                and_(
                    Connection.user_id == user_id,
                    Connection.status == "connected"
                )
            )
        )
        connection = result.scalar_one_or_none()
        
        if connection:
            # Calculate duration
            duration = int((datetime.utcnow() - connection.started_at).total_seconds())
            
            status_message = {
                "type": "connection_status",
                "status": "connected",
                "data": {
                    "connection_id": str(connection.id),
                    "server_location": connection.server.location if connection.server else "unknown",
                    "client_ip": connection.client_ip,
                    "duration_seconds": duration,
                    "connected_at": connection.started_at.isoformat()
                }
            }
        else:
            status_message = {
                "type": "connection_status",
                "status": "disconnected",
                "data": None
            }
        
        await manager.send_personal_message(status_message, user_id)
        
    except Exception as e:
        logger.error(f"Error sending connection status: {e}")

@router.websocket("/system-alerts")
async def websocket_system_alerts(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for system-wide alerts (admin only)"""
    try:
        # Verify admin token
        user = await verify_websocket_token(token, db)
        if not user.is_superuser:
            await websocket.close(code=1008, reason="Admin access required")
            return
        
        # Connect WebSocket
        connection_id = await manager.connect(websocket, f"admin_{user.id}")
        
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
        except WebSocketDisconnect:
            manager.disconnect(connection_id, f"admin_{user.id}")
            
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")

# Background task to send periodic updates
async def broadcast_system_stats():
    """Background task to broadcast system statistics"""
    while True:
        try:
            # This would be called periodically to send system updates
            # Implementation depends on your specific monitoring needs
            await asyncio.sleep(30)  # Send updates every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Utility functions for external use
async def notify_connection_change(user_id: str, status: str, connection_data: dict = None):
    """Notify user of connection status change"""
    message = {
        "type": "connection_change",
        "status": status,
        "data": connection_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def notify_system_alert(alert_type: str, message: str, severity: str = "info"):
    """Broadcast system alert to all admin connections"""
    alert_message = {
        "type": "system_alert",
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(alert_message)