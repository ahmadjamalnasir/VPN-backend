from sqlalchemy import Column, String, DateTime, Integer, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum

class PlanStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price_usd = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    features = Column(JSONB, nullable=True)
    status = Column(Enum(PlanStatus), default=PlanStatus.active, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="plan")