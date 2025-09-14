from sqlalchemy import Column, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum

class SubscriptionStatus(enum.Enum):
    active = "active"
    expired = "expired"
    canceled = "canceled"

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False)
    auto_renew = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        from datetime import datetime
        return (
            self.status == SubscriptionStatus.active and 
            self.start_date <= datetime.utcnow() <= self.end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in subscription"""
        from datetime import datetime
        if self.status != SubscriptionStatus.active:
            return 0
        remaining = (self.end_date - datetime.utcnow()).days
        return max(0, remaining)