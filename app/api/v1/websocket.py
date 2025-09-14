from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.database import get_db
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.connection import Connection
from app.models.vpn_server import VPNServer
from app.services.auth import verify_token
from datetime import datetime, timedelta
import json
import asyncio
from typing import Dict, Set
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        self.admin_connections: Dict[str, WebSocket] = {}
    
    async def connect_user(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        connection_id = f"user_{user_id}_{datetime.now().timestamp()}"
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        logger.info(f"User WebSocket connected: {connection_id}")
        return connection_id
    
    async def connect_admin(self, websocket: WebSocket, admin_id: str):
        await websocket.accept()
        connection_id = f"admin_{admin_id}_{datetime.now().timestamp()}"
        self.admin_connections[connection_id] = websocket
        logger.info(f"Admin WebSocket connected: {connection_id}")
        return connection_id
    
    def disconnect_user(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"User WebSocket disconnected: {connection_id}")
    
    def disconnect_admin(self, connection_id: str):
        if connection_id in self.admin_connections:
            del self.admin_connections[connection_id]
        logger.info(f"Admin WebSocket disconnected: {connection_id}")
    
    async def send_to_user(self, message: dict, user_id: str):
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect_user(connection_id, user_id)
    
    async def broadcast_to_admins(self, message: dict):
        disconnected = []
        for connection_id, websocket in self.admin_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            if connection_id in self.admin_connections:
                del self.admin_connections[connection_id]

manager = ConnectionManager()

async def verify_websocket_token(token: str, db: AsyncSession):
    """Verify JWT token for WebSocket connection"""
    try:
        from jose import jwt, JWTError
        from app.core.config import get_settings
        
        settings = get_settings()
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Try admin user first
        try:
            admin_uuid = UUID(user_id)
            admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
            admin_user = admin_result.scalar_one_or_none()
            if admin_user:
                return admin_user
        except ValueError:
            pass
        
        # Try regular user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# MOBILE WEBSOCKET
@router.websocket("/connection")
async def websocket_connection_status(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time connection status updates (Mobile)"""
    try:
        # Verify token
        user = await verify_websocket_token(token, db)
        
        # Connect WebSocket
        connection_id = await manager.connect_user(websocket, str(user.id))
        
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
            manager.disconnect_user(connection_id, str(user.id))
            
    except Exception as e:
        logger.error(f"User WebSocket error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")

# ADMIN WEBSOCKET
@router.websocket("/admin-dashboard")
async def websocket_admin_dashboard(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for admin dashboard real-time updates (Admin only)"""
    try:
        # Verify admin token
        user = await verify_websocket_token(token, db)
        if not isinstance(user, AdminUser):
            await websocket.close(code=1008, reason="Admin access required")
            return
        
        # Connect WebSocket
        connection_id = await manager.connect_admin(websocket, str(user.id))
        
        # Send initial dashboard data
        await send_admin_dashboard_data(websocket, db)
        
        try:
            while True:
                # Keep connection alive and handle admin requests
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "get_dashboard":
                    await send_admin_dashboard_data(websocket, db)
                elif message.get("type") == "get_system_stats":
                    await send_system_stats(websocket, db)
                
        except WebSocketDisconnect:
            manager.disconnect_admin(connection_id)
            
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")

async def send_connection_status(user_id: str, db: AsyncSession):
    """Send current connection status to user (Mobile)"""
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
        
        await manager.send_to_user(status_message, user_id)
        
    except Exception as e:
        logger.error(f"Error sending connection status: {e}")

async def send_admin_dashboard_data(websocket: WebSocket, db: AsyncSession):
    """Send admin dashboard data (Admin only)"""
    try:
        # Get dashboard statistics
        total_users = await db.scalar(select(func.count(User.id)))
        active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
        premium_users = await db.scalar(select(func.count(User.id)).where(User.is_premium == True))
        
        total_servers = await db.scalar(select(func.count(VPNServer.id)))
        active_servers = await db.scalar(select(func.count(VPNServer.id)).where(VPNServer.status == "active"))
        
        active_connections = await db.scalar(
            select(func.count(Connection.id)).where(Connection.status == "connected")
        )
        
        dashboard_data = {
            "type": "dashboard_update",
            "data": {
                "total_users": total_users or 0,
                "active_users": active_users or 0,
                "premium_users": premium_users or 0,
                "total_servers": total_servers or 0,
                "active_servers": active_servers or 0,
                "active_connections": active_connections or 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(dashboard_data))
        
    except Exception as e:
        logger.error(f"Error sending admin dashboard data: {e}")

async def send_system_stats(websocket: WebSocket, db: AsyncSession):
    """Send system statistics (Admin only)"""
    try:
        # Connection stats (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        daily_connections = await db.scalar(
            select(func.count(Connection.id)).where(Connection.created_at >= yesterday)
        )
        
        # Server load stats
        avg_load = await db.scalar(
            select(func.avg(VPNServer.current_load)).where(VPNServer.status == "active")
        )
        
        system_stats = {
            "type": "system_stats",
            "data": {
                "daily_connections": daily_connections or 0,
                "avg_server_load": round((avg_load or 0) * 100, 1),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(system_stats))
        
    except Exception as e:
        logger.error(f"Error sending system stats: {e}")

# Utility functions for external use
async def notify_connection_change(user_id: str, status: str, connection_data: dict = None):
    """Notify user of connection status change (Mobile)"""
    message = {
        "type": "connection_change",
        "status": status,
        "data": connection_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(message, user_id)

async def notify_admin_alert(alert_type: str, message: str, severity: str = "info"):
    """Broadcast system alert to all admin connections (Admin only)"""
    alert_message = {
        "type": "system_alert",
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_admins(alert_message)