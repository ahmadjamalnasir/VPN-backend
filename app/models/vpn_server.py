from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class VPNServer(Base):
    __tablename__ = "vpn_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    load = Column(Integer, default=0)  # Current server load (0-100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
