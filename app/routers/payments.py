from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import auth_service, payment_service

router = APIRouter()


@router.post("/create-checkout")
async def create_checkout_session(
    price: int,
    current_user = Depends(auth_service.get_current_user)
):
    session = await payment_service.create_checkout_session(
        price=price,
        user_id=current_user.id
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None)
):
    payload = await request.body()
    return await payment_service.handle_stripe_webhook(
        payload=payload,
        sig_header=stripe_signature,
        db=db
    )
