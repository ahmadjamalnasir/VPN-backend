from sqlalchemy import Column, String, Boolean, DateTime, Integer, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, Sequence('user_id_seq'), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="user")
    connections = relationship("Connection", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    usage_logs = relationship("VPNUsageLog", back_populates="user")