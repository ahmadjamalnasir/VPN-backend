from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.user import SubscriptionPlan
from typing import List, Optional
from uuid import UUID

class SubscriptionPlanCRUD:
    async def create(self, db: AsyncSession, data: dict) -> SubscriptionPlan:
        plan = SubscriptionPlan(**data)
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    async def get(self, db: AsyncSession, plan_id: str) -> Optional[SubscriptionPlan]:
        query = select(SubscriptionPlan).where(SubscriptionPlan.id == UUID(plan_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> List[SubscriptionPlan]:
        query = select(SubscriptionPlan)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_free_plan(self, db: AsyncSession) -> Optional[SubscriptionPlan]:
        query = select(SubscriptionPlan).where(SubscriptionPlan.is_free.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

subscription_plan_crud = SubscriptionPlanCRUD()
