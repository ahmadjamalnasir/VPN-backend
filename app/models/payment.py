from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    payment_intent_id = Column(String, unique=True, nullable=True)
    checkout_session_id = Column(String, unique=True, nullable=True)
    amount = Column(String, nullable=False)  # Store as string to preserve decimal precision
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, succeeded, failed, canceled
    payment_method = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="payment_logs")
