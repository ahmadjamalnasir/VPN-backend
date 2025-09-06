from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("vpn_servers.id", ondelete="SET NULL"), nullable=True)
    client_ip = Column(String, nullable=False)
    client_public_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="connected")
    bytes_sent = Column(BigInteger, nullable=False, default=0)
    bytes_received = Column(BigInteger, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="connections")
    server = relationship("VPNServer", back_populates="connections")