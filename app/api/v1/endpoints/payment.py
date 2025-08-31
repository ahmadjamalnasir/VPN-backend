from fastapi import APIRouter, Depends, Request, HTTPException
from app.schemas.payment import PaymentCreateRequest, PaymentCreateResponse
from app.services.payment import PaymentService
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.auth import get_current_user

router = APIRouter()


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment(
    request: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    payment_service = PaymentService(db)
    result = await payment_service.create_checkout_session(
        user_id=str(current_user.id),
        plan_type=request.plan_type,
        currency=request.currency,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        metadata=request.metadata
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to create payment session")

    return result


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe signature")

    payload = await request.body()
    payment_service = PaymentService(db)
    success = await payment_service.handle_webhook(payload, signature)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to process webhook")
