from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vpn_server import VPNServerResponse, VPNConnectionConfig
from app.services import auth_service, vpn_service

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, server_id: int):
        await websocket.accept()
        self.active_connections[server_id] = websocket

    def disconnect(self, server_id: int):
        self.active_connections.pop(server_id, None)

    async def broadcast_server_metrics(self, server_id: int, message: str):
        if server_id in self.active_connections:
            await self.active_connections[server_id].send_text(message)


manager = ConnectionManager()


@router.get("/servers", response_model=List[VPNServerResponse])
async def list_servers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return vpn_service.get_available_servers(db, skip=skip, limit=limit)


@router.get("/servers/{server_id}", response_model=VPNServerResponse)
async def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    server = vpn_service.get_server_by_id(db, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.post("/connect/{server_id}", response_model=VPNConnectionConfig)
async def connect_to_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    server = vpn_service.get_server_by_id(db, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    
    if not server.is_active:
        raise HTTPException(status_code=400, detail="Server is not active")
    
    # Generate client IP (in production, implement proper IP allocation)
    client_ip = f"10.0.0.{server_id % 254 + 1}/24"
    
    return vpn_service.generate_client_config(server, client_ip)


@router.websocket("/ws/metrics/{server_id}")
async def metrics_websocket(server_id: int, websocket: WebSocket):
    await manager.connect(websocket, server_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Here you would validate and process the metrics data
            # For example, update server load
            try:
                load = int(data)
                db = next(get_db())
                updated_server = vpn_service.update_server_load(db, server_id, load)
                if updated_server:
                    await manager.broadcast_server_metrics(
                        server_id,
                        f"Server load updated: {load}%"
                    )
            except ValueError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(server_id)
