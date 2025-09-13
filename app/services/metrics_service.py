from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from datetime import datetime
import json
import asyncio
import random
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.connection import Connection
from app.models.vpn_server import VPNServer

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.metrics_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.metrics_tasks:
            self.metrics_tasks[user_id].cancel()
            del self.metrics_tasks[user_id]

    async def start_metrics(self, user_id: str, connection_id: str, db: AsyncSession):
        """Start sending metrics for a user's connection"""
        self.metrics_tasks[user_id] = asyncio.create_task(
            self._send_metrics(user_id, connection_id, db)
        )

    async def _send_metrics(self, user_id: str, connection_id: str, db: AsyncSession):
        """Simulated metrics generator and sender"""
        try:
            websocket = self.active_connections[user_id]
            last_bytes_sent = 0
            last_bytes_received = 0
            last_time = datetime.now()

            while True:
                # Get current connection stats
                result = await db.get(Connection, connection_id)
                connection = result
                if not connection or connection.status != "connected":
                    await websocket.close()
                    break

                current_time = datetime.now()
                time_delta = (current_time - last_time).total_seconds()

                # Simulate increasing bytes count
                bytes_sent = connection.bytes_sent + random.randint(100000, 500000)
                bytes_received = connection.bytes_received + random.randint(200000, 800000)

                # Calculate speeds in Mbps
                sent_speed = (bytes_sent - last_bytes_sent) * 8 / (1024 * 1024 * time_delta) if time_delta > 0 else 0
                received_speed = (bytes_received - last_bytes_received) * 8 / (1024 * 1024 * time_delta) if time_delta > 0 else 0

                # Update database
                connection.bytes_sent = bytes_sent
                connection.bytes_received = bytes_received
                await db.commit()

                # Get server metrics
                server = connection.server
                if server:
                    server.current_load = min(1.0, max(0.0, server.current_load + random.uniform(-0.05, 0.05)))
                    server.ping = max(10, min(200, server.ping + random.randint(-5, 5)))
                    await db.commit()

                # Prepare metrics
                metrics = {
                    "timestamp": current_time.isoformat(),
                    "connection_id": str(connection_id),
                    "bytes_sent": bytes_sent,
                    "bytes_received": bytes_received,
                    "upload_speed_mbps": round(sent_speed, 2),
                    "download_speed_mbps": round(received_speed, 2),
                    "ping_ms": server.ping if server else 50,
                    "server_load_pct": round((server.current_load if server else 0.5) * 100, 1)
                }

                # Send metrics
                await websocket.send_text(json.dumps(metrics))

                # Update last values
                last_bytes_sent = bytes_sent
                last_bytes_received = bytes_received
                last_time = current_time

                # Wait before next update
                await asyncio.sleep(1)  # Update every second

        except (WebSocketDisconnect, asyncio.CancelledError):
            self.disconnect(user_id)
        except Exception as e:
            print(f"Error in metrics task: {e}")
            self.disconnect(user_id)

# Global connection manager
manager = ConnectionManager()