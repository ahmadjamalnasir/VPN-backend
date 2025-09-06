from sqlalchemy import Column, String, DateTime, Integer, Float, CheckConstraint
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
    endpoint = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    current_load = Column(Float, nullable=False, default=0.0)
    ping = Column(Integer, nullable=False, default=0)
    available_ips = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'maintenance', 'offline')", name="valid_server_status"),
    )
    
    # Relationships
    connections = relationship("Connection", back_populates="server")