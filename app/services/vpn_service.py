import os
from typing import Optional
from sqlalchemy.orm import Session
from app.models.vpn_server import VPNServer
from app.schemas.vpn_server import VPNConnectionConfig


def get_server_by_id(db: Session, server_id: int) -> Optional[VPNServer]:
    return db.query(VPNServer).filter(VPNServer.id == server_id).first()


def get_all_servers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(VPNServer).offset(skip).limit(limit).all()


def get_available_servers(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(VPNServer)
        .filter(VPNServer.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def generate_wireguard_keys():
    # This is a placeholder. In production, use actual WireGuard key generation
    private_key = os.urandom(32).hex()
    # In production, use actual WireGuard public key derivation
    public_key = os.urandom(32).hex()
    return private_key, public_key


def generate_client_config(server: VPNServer, client_ip: str) -> VPNConnectionConfig:
    private_key, public_key = generate_wireguard_keys()
    
    return VPNConnectionConfig(
        server_ip=server.ip_address,
        server_port=server.port,
        server_public_key=server.public_key,
        client_private_key=private_key,
        client_ip=client_ip,
        dns=["1.1.1.1", "1.0.0.1"]  # Cloudflare DNS
    )


def update_server_load(db: Session, server_id: int, load: int):
    server = get_server_by_id(db, server_id)
    if server:
        server.load = max(0, min(100, load))  # Ensure load is between 0-100
        db.commit()
        return server
    return None
