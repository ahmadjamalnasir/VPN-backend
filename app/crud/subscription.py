from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.user import Subscription
from typing import List, Optional
from uuid import UUID

class SubscriptionCRUD:
    async def create(self, db: AsyncSession, data: dict) -> Subscription:
        subscription = Subscription(**data)
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    async def get(self, db: AsyncSession, subscription_id: str) -> Optional[Subscription]:
        query = select(Subscription).where(Subscription.id == UUID(subscription_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_active_subscription(self, db: AsyncSession, user_id: str) -> Optional[Subscription]:
        query = (
            select(Subscription)
            .options(joinedload(Subscription.plan))
            .where(
                Subscription.user_id == UUID(user_id),
                Subscription.status == "active"
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_status(self, db: AsyncSession, subscription_id: str, status: str) -> Optional[Subscription]:
        subscription = await self.get(db, subscription_id)
        if subscription:
            subscription.status = status
            await db.commit()
            await db.refresh(subscription)
        return subscription

subscription_crud = SubscriptionCRUD()
