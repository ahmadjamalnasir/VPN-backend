from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)  # Price in cents
    duration_months = Column(Integer, nullable=False)
    max_devices = Column(Integer, default=1)
    features = Column(String)  # JSON string of features
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey("users.id"))
