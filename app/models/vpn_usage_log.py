from sqlalchemy import Column, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class VPNUsageLog(Base):
    __tablename__ = "vpn_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("vpn_servers.id"), nullable=False)
    connected_at = Column(DateTime, nullable=True)
    disconnected_at = Column(DateTime, nullable=True)
    data_used_mb = Column(BigInteger, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    server = relationship("VPNServer", back_populates="usage_logs")