import ipaddress
import subprocess
from app.models.vpn_server import VPNServer
import os


def generate_wireguard_keypair():
    """Generate a WireGuard key pair."""
    private_key = subprocess.check_output(['wg', 'genkey']).strip().decode()
    public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).strip().decode()
    return private_key, public_key


def assign_client_ip(server: VPNServer) -> str:
    """Assign next available IP from server's IP range."""
    network = ipaddress.ip_network(server.available_ips)
    # In production, you'd want to check the database for used IPs
    # For now, just assign the second IP in the range (first is server)
    return str(list(network.hosts())[0])


def generate_wireguard_config(server: VPNServer) -> dict:
    """Generate WireGuard configuration for a client."""
    private_key, public_key = generate_wireguard_keypair()
    client_ip = assign_client_ip(server)

    config = f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server.public_key}
Endpoint = {server.endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

    return {
        "client_ip": client_ip,
        "client_public_key": public_key,
        "wg_config": config,
    }
