from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum

class PaymentMethod(enum.Enum):
    card = "card"
    paypal = "paypal"
    in_app_purchase = "in_app_purchase"
    crypto = "crypto"

class PaymentStatus(enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("user_subscriptions.id"), nullable=False)
    amount_usd = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    transaction_ref = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payments")