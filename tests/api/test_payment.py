import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import PaymentLog
from app.models.user import User
from app.models.subscription import Subscription
from app.services.payment import PaymentService


@pytest.fixture
def test_user(db: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="testpass123"
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def stripe_checkout_session():
    return {
        "id": "cs_test_123",
        "payment_intent": "pi_test_123",
        "client_secret": "secret_123",
        "customer_email": "test@example.com",
        "amount_total": 1000,
        "currency": "usd",
        "payment_method": "pm_123",
        "subscription": "sub_123",
        "metadata": {
            "user_id": "test_user_id"
        }
    }


@pytest.fixture
def stripe_webhook_event(stripe_checkout_session):
    return {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {
            "object": stripe_checkout_session
        }
    }


@pytest.fixture
def payment_log(db: AsyncSession, test_user):
    log = PaymentLog(
        id=uuid.uuid4(),
        user_id=test_user.id,
        checkout_session_id="cs_test_123",
        amount="1000",
        currency="usd",
        status="pending",
        metadata={"plan": "premium"}
    )
    db.add(log)
    db.commit()
    return log


@patch("stripe.Webhook.construct_event")
async def test_webhook_session_completed(
    mock_construct_event,
    db: AsyncSession,
    test_user,
    payment_log,
    stripe_webhook_event
):
    """Test successful payment webhook processing"""
    mock_construct_event.return_value = stripe_webhook_event
    
    service = PaymentService(db)
    result = await service.handle_webhook(
        payload={"raw": "payload"},
        sig_header="test_signature"
    )

    assert result is True

    # Verify payment log updated
    db.refresh(payment_log)
    assert payment_log.status == "completed"
    assert payment_log.payment_method == "pm_123"
    assert payment_log.payment_intent_id == "pi_test_123"

    # Verify subscription created/updated
    subscription = db.query(Subscription).filter(
        Subscription.user_id == test_user.id
    ).first()
    assert subscription is not None
    assert subscription.status == "active"
    assert subscription.stripe_subscription_id == "sub_123"


@patch("stripe.Webhook.construct_event")
async def test_webhook_invalid_signature(
    mock_construct_event,
    db: AsyncSession
):
    """Test webhook fails with invalid signature"""
    mock_construct_event.side_effect = stripe.error.SignatureVerificationError("Invalid", "test")
    
    service = PaymentService(db)
    result = await service.handle_webhook(
        payload={"raw": "payload"},
        sig_header="invalid_signature"
    )

    assert result is False


@patch("stripe.Webhook.construct_event")
async def test_webhook_missing_payment_log(
    mock_construct_event,
    db: AsyncSession,
    stripe_webhook_event
):
    """Test webhook handling when payment log not found"""
    mock_construct_event.return_value = stripe_webhook_event
    
    service = PaymentService(db)
    result = await service.handle_webhook(
        payload={"raw": "payload"},
        sig_header="test_signature"
    )

    assert result is False
