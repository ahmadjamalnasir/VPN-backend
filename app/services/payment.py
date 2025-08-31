import stripe
from typing import Optional, Dict, Any
from app.core.config import settings
from app.models.payment import PaymentLog
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checkout_session(
        self,
        user_id: str,
        plan_type: str,
        currency: str = "usd",
        success_url: str = None,
        cancel_url: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        try:
            price_id = (
                settings.STRIPE_MONTHLY_PRICE_ID
                if plan_type == "monthly"
                else settings.STRIPE_YEARLY_PRICE_ID
            )

            session = stripe.checkout.Session.create(
                customer_email=None,  # We'll add this when we have user email
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id, **(metadata or {})}
            )

            payment_log = PaymentLog(
                user_id=user_id,
                checkout_session_id=session.id,
                amount=str(session.amount_total),
                currency=session.currency,
                status="pending",
                metadata=metadata
            )
            self.db.add(payment_log)
            await self.db.commit()

            return {
                "checkout_url": session.url,
                "client_secret": session.client_secret,
                "payment_intent_id": session.payment_intent
            }

        except stripe.error.StripeError as e:
            # Log the error and return None or raise custom exception
            print(f"Stripe error: {str(e)}")
            return None

    async def handle_webhook(self, payload: Dict[str, Any], sig_header: str):
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )

            if event.type == "checkout.session.completed":
                session = event.data.object
                payment_log = await self._get_payment_log_by_session(session.id)
                
                if payment_log:
                    payment_log.status = "completed"
                    payment_log.payment_method = session.payment_method
                    payment_log.payment_intent_id = session.payment_intent
                    await self.db.commit()

                    # Here we'll handle updating user subscription
                    # This will be implemented in the subscription service

            return True

        except stripe.error.SignatureVerificationError:
            # Invalid signature
            print("Invalid signature!")
            return False
        except Exception as e:
            print(f"Error handling webhook: {str(e)}")
            return False

    async def _get_payment_log_by_session(self, session_id: str) -> Optional[PaymentLog]:
        result = await self.db.query(PaymentLog).filter(
            PaymentLog.checkout_session_id == session_id
        ).first()
        return result
