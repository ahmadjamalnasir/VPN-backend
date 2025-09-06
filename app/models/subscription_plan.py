from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(Integer, unique=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)  # "Free", "Monthly Premium", "Yearly Premium"
    plan_type = Column(String(10), nullable=False)  # "free", "monthly", "yearly"
    price = Column(Float, nullable=False, default=0.0)
    duration_days = Column(Integer, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    features = Column(String, nullable=True)  # JSON string of features
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="plan")