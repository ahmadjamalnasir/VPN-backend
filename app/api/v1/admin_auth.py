from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models.admin_user import AdminUser
from app.services.auth import verify_password, create_access_token
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    admin_id: int
    role: str
    full_name: str

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """Admin login endpoint - separate from user login"""
    
    # Find admin by username
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == request.username)
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(request.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not admin.is_active:
        raise HTTPException(status_code=400, detail="Admin account is inactive")
    
    # Update last login
    await db.execute(
        update(AdminUser)
        .where(AdminUser.id == admin.id)
        .values(last_login=datetime.utcnow())
    )
    await db.commit()
    
    # Create admin token with role
    access_token = create_access_token(
        data={
            "sub": admin.username,
            "admin_id": str(admin.id),
            "role": admin.role.value,
            "type": "admin"
        },
        expires_delta=timedelta(hours=8)  # Longer session for admin
    )
    
    return AdminLoginResponse(
        access_token=access_token,
        admin_id=admin.admin_id,
        role=admin.role.value,
        full_name=admin.full_name
    )