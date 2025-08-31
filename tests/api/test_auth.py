import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core import security
import uuid


@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "testpass123"
    }


async def test_register_success(client: AsyncClient, user_data):
    """Test successful user registration"""
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]
    assert "password" not in data


async def test_register_duplicate_email(client: AsyncClient, user_data, db: AsyncSession):
    """Test registration fails with duplicate email"""
    # Create user first
    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        hashed_password=security.get_password_hash(user_data["password"])
    )
    db.add(user)
    db.commit()

    # Try to register again
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()


async def test_login_success(client: AsyncClient, user_data, db: AsyncSession):
    """Test successful login"""
    # Create user
    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        hashed_password=security.get_password_hash(user_data["password"])
    )
    db.add(user)
    db.commit()

    # Login
    response = await client.post("/api/v1/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient, user_data):
    """Test login fails with invalid credentials"""
    response = await client.post("/api/v1/auth/login", data={
        "username": user_data["email"],
        "password": "wrongpass"
    })
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


async def test_refresh_token_success(client: AsyncClient, user_data, db: AsyncSession):
    """Test successful token refresh"""
    # Create user and login first
    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        hashed_password=security.get_password_hash(user_data["password"])
    )
    db.add(user)
    db.commit()

    login_response = await client.post("/api/v1/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != access_token


async def test_logout_success(client: AsyncClient, user_data, db: AsyncSession):
    """Test successful logout"""
    # Create user and login first
    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        hashed_password=security.get_password_hash(user_data["password"])
    )
    db.add(user)
    db.commit()

    login_response = await client.post("/api/v1/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    access_token = login_response.json()["access_token"]

    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Verify token is invalidated
    protected_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert protected_response.status_code == 401
