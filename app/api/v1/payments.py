from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.schemas.subscription_new import PaymentInitiate, PaymentResponse
from app.services.auth import verify_token
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/initiate", response_model=PaymentResponse, tags=["Payments"])
async def initiate_payment(
    payment_data: PaymentInitiate,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create payment request"""
    # Find user
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find plan
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == payment_data.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Validate amount
    if payment_data.amount_usd != plan.price_usd:
        raise HTTPException(status_code=400, detail="Amount mismatch")
    
    # Create pending subscription
    from datetime import datetime, timedelta
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    subscription = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        status="active"  # Will be activated after payment success
    )
    db.add(subscription)
    await db.flush()  # Get subscription ID
    
    # Create payment record
    payment = Payment(
        user_id=user.id,
        subscription_id=subscription.id,
        amount_usd=payment_data.amount_usd,
        payment_method=PaymentMethod(payment_data.payment_method),
        status=PaymentStatus.pending,
        transaction_ref=f"PAY_{subscription.id}"
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    return payment

@router.post("/callback", tags=["Payments"])
async def payment_callback(
    payment_id: UUID,
    status: str,
    transaction_ref: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle payment gateway callback/webhook"""
    # Find payment
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update payment status
    if status == "success":
        payment.status = PaymentStatus.success
        if transaction_ref:
            payment.transaction_ref = transaction_ref
        
        # Activate subscription
        subscription_result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == payment.subscription_id)
        )
        subscription = subscription_result.scalar_one_or_none()
        if subscription:
            subscription.status = "active"
            
            # Update user premium status
            user_result = await db.execute(select(User).where(User.id == payment.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id))
                plan = plan_result.scalar_one_or_none()
                if plan:
                    user.is_premium = plan.price_usd > 0
    
    elif status == "failed":
        payment.status = PaymentStatus.failed
        
        # Cancel subscription
        subscription_result = await db.execute(
            select(UserSubscription).where(UserSubscription.id == payment.subscription_id)
        )
        subscription = subscription_result.scalar_one_or_none()
        if subscription:
            subscription.status = "canceled"
    
    await db.commit()
    return {"message": "Payment status updated"}

@router.get("/{payment_id}", response_model=PaymentResponse, tags=["Payments"])
async def get_payment_status(
    payment_id: UUID,
    current_user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Check payment status"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify user owns this payment
    if str(payment.user_id) != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return payment