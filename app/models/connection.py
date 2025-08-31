from sqlalchemy import Column, ForeignKey, String, BigInteger, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid


class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("vpn_servers.id"))
    status = Column(String(50), nullable=False)  # active, ended, failed
    client_public_key = Column(String, nullable=False)
    client_ip = Column(INET)
    bytes_sent = Column(BigInteger, default=0)
    bytes_received = Column(BigInteger, default=0)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="connections")
    server = relationship("VPNServer", back_populates="connections")

    def __repr__(self):
        return f"<Connection {self.id}: {self.user_id} -> {self.server_id} ({self.status})>"
