import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.subscription import Subscription
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.api.v1.routes import vpn
from app.core import security
from fastapi import HTTPException


@pytest.fixture
def test_user_premium(db: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="premium@test.com",
        hashed_password=security.get_password_hash("testpass123")
    )
    subscription = Subscription(
        user_id=user.id,
        plan_type="premium",
        status="active",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc).replace(year=datetime.now().year + 1)
    )
    db.add(user)
    db.add(subscription)
    db.commit()
    return user


@pytest.fixture
def test_user_free(db: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="free@test.com",
        hashed_password=security.get_password_hash("testpass123")
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_vpn_server_premium(db: AsyncSession):
    server = VPNServer(
        id=uuid.uuid4(),
        hostname="premium.vpn.test",
        location="premium-loc",
        ip_address="10.0.0.1",
        endpoint="10.0.0.1:51820",
        public_key="test_pub_key_1",
        status="active",
        tier="premium"
    )
    db.add(server)
    db.commit()
    return server


@pytest.fixture
def test_vpn_server_free(db: AsyncSession):
    server = VPNServer(
        id=uuid.uuid4(),
        hostname="free.vpn.test",
        location="free-loc",
        ip_address="10.0.0.2",
        endpoint="10.0.0.2:51820",
        public_key="test_pub_key_2",
        status="active",
        tier="free"
    )
    db.add(server)
    db.commit()
    return server


async def test_connect_premium_success(
    db: AsyncSession,
    test_user_premium,
    test_vpn_server_premium
):
    """Test successful connection to premium server by premium user"""
    response = await vpn.connect(
        server_id=test_vpn_server_premium.id,
        client_public_key="test_client_key",
        db=db,
        current_user=test_user_premium
    )
    assert response.status == "active"
    assert response.server_endpoint == test_vpn_server_premium.endpoint

    # Verify connection record
    conn = db.query(Connection).filter(
        Connection.user_id == test_user_premium.id
    ).first()
    assert conn is not None
    assert conn.status == "active"
    assert conn.server_id == test_vpn_server_premium.id


async def test_connect_free_to_premium_fails(
    db: AsyncSession,
    test_user_free,
    test_vpn_server_premium
):
    """Test free user cannot connect to premium server"""
    with pytest.raises(HTTPException) as exc:
        await vpn.connect(
            server_id=test_vpn_server_premium.id,
            client_public_key="test_client_key",
            db=db,
            current_user=test_user_free
        )
    assert exc.value.status_code == 403


async def test_disconnect_updates_usage(
    db: AsyncSession,
    test_user_premium,
    test_vpn_server_premium
):
    """Test disconnect updates connection record with usage data"""
    # Create active connection
    conn = Connection(
        id=uuid.uuid4(),
        user_id=test_user_premium.id,
        server_id=test_vpn_server_premium.id,
        status="active",
        client_public_key="test_client_key",
        client_ip="10.10.0.2",
        started_at=datetime.now(timezone.utc)
    )
    db.add(conn)
    db.commit()

    # Disconnect
    response = await vpn.disconnect(
        bytes_sent=1024,
        bytes_received=2048,
        db=db,
        current_user=test_user_premium
    )
    
    # Verify connection updated
    conn = db.refresh(conn)
    assert conn.status == "ended"
    assert conn.bytes_sent == 1024
    assert conn.bytes_received == 2048
    assert conn.ended_at is not None

    # Verify response
    assert response.total_bytes == 3072  # sent + received
    assert response.duration > 0
