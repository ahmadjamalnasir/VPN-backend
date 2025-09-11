from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(10), nullable=False, default="active")
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True, nullable=False)
    payment_method = Column(String, nullable=True)  # "stripe", "paypal", etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'expired', 'canceled', 'pending')", name="valid_subscription_status"),
    )
    
    # Relationships
    user = relationship("User", back_populates="user_subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        from datetime import datetime
        return (
            self.status == "active" and 
            self.start_date <= datetime.utcnow() <= self.end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in subscription"""
        from datetime import datetime
        if self.status != "active":
            return 0
        remaining = (self.end_date - datetime.utcnow()).days
        return max(0, remaining)