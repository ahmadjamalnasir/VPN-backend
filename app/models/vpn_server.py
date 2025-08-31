from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class VPNServer(Base):
    __tablename__ = "vpn_servers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname = Column(String, nullable=False)
    location = Column(String, nullable=False, index=True)
    ip_address = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)  # ip:port
    public_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active", index=True)  # active, maintenance, offline
    current_load = Column(Float, default=0.0)  # Current server load (0.0-1.0)
    ping = Column(Integer, default=0)  # Latency in ms

    # Relationships
    connections = relationship("Connection", back_populates="server")
    available_ips = Column(String, nullable=False)  # CIDR range for client IPs
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    connections = relationship("VPNConnection", back_populates="server")
