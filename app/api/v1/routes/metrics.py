from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import get_current_user_from_token
from app.models.user import User
from app.models.vpn_connection import VPNConnection
from app.services.metrics_service import manager
from uuid import UUID
from typing import Optional

router = APIRouter()

async def get_websocket_user(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    token: Optional[str] = Query(None)
) -> User:
    """Authenticate WebSocket connection using JWT token"""
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    user = await get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return user

@router.websocket("/ws/connection/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_websocket_user)
):
    """WebSocket endpoint for real-time connection metrics"""
    # Verify user_id matches authenticated user
    if str(current_user.id) != str(user_id):
        await websocket.close(code=4003, reason="Unauthorized user_id")
        return

    # Find active connection for user
    connection = db.query(VPNConnection).filter(
        VPNConnection.user_id == user_id,
        VPNConnection.status == "connected"
    ).first()

    if not connection:
        await websocket.close(code=4004, reason="No active connection found")
        return

    try:
        # Accept connection
        await manager.connect(str(user_id), websocket)
        
        # Start sending metrics
        await manager.start_metrics(str(user_id), str(connection.id), db)
        
        # Keep connection alive until client disconnects
        try:
            while True:
                # Wait for client messages (ping/pong will be handled automatically)
                data = await websocket.receive_text()
        except Exception:
            pass
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up on disconnect
        manager.disconnect(str(user_id))
