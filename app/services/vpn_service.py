import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.vpn_server import VPNServer

async def get_server_by_id(db: AsyncSession, server_id: str) -> Optional[VPNServer]:
    result = await db.execute(select(VPNServer).where(VPNServer.id == server_id))
    return result.scalar_one_or_none()

async def get_available_servers(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(VPNServer)
        .where(VPNServer.status == "active")
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

def generate_wireguard_keys():
    """Generate WireGuard key pair (placeholder implementation)"""
    # In production, use actual WireGuard key generation
    private_key = os.urandom(32).hex()
    public_key = os.urandom(32).hex()
    return private_key, public_key

async def update_server_load(db: AsyncSession, server_id: str, load: float):
    result = await db.execute(select(VPNServer).where(VPNServer.id == server_id))
    server = result.scalar_one_or_none()
    if server:
        server.current_load = max(0.0, min(1.0, load))  # Ensure load is between 0.0-1.0
        await db.commit()
        return server
    return None