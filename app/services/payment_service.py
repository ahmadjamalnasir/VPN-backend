import stripe
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.services import subscription_service

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(price: int, user_id: int):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "PrimeVPN Subscription"
                    },
                    "unit_amount": price,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{settings.BASE_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.BASE_URL}/payments/cancel",
            metadata={
                "user_id": user_id
            }
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def handle_stripe_webhook(payload: dict, sig_header: str, db: Session):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Create subscription for user
        user_id = session["metadata"]["user_id"]
        await process_successful_payment(db, user_id, session["amount_total"])

    return {"status": "success"}


async def process_successful_payment(db: Session, user_id: int, amount: int):
    # Create a subscription based on the payment amount
    # This is a simple example - you might want to have different subscription tiers
    subscription_create = {
        "user_id": user_id,
        "plan_name": "Premium",
        "price": amount,
        "duration_months": 1,
        "max_devices": 3,
        "features": "Premium features"
    }
    
    subscription_service.create_subscription(db, subscription_create)
