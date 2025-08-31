from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


def get_subscription(db: Session, subscription_id: int) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()


def get_user_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


def create_subscription(db: Session, subscription: SubscriptionCreate) -> Subscription:
    expires_at = datetime.utcnow() + timedelta(days=30 * subscription.duration_months)
    db_subscription = Subscription(
        **subscription.dict(),
        expires_at=expires_at
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def update_subscription(
    db: Session,
    subscription: Subscription,
    subscription_update: SubscriptionUpdate
) -> Subscription:
    update_data = subscription_update.dict(exclude_unset=True)
    
    if "duration_months" in update_data:
        subscription.expires_at = datetime.utcnow() + timedelta(
            days=30 * update_data["duration_months"]
        )
    
    for field, value in update_data.items():
        setattr(subscription, field, value)
    
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db: Session, subscription_id: int) -> bool:
    subscription = get_subscription(db, subscription_id)
    if subscription:
        db.delete(subscription)
        db.commit()
        return True
    return False


def get_expired_subscriptions(db: Session) -> List[Subscription]:
    return (
        db.query(Subscription)
        .filter(Subscription.expires_at < datetime.utcnow())
        .all()
    )
