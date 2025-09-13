from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.admin_user import AdminUser, AdminRole
from app.services.auth import get_password_hash, verify_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CreateVPNUserRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    country: Optional[str] = None

class CreateAdminUserRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "admin"  # "super_admin", "admin", "moderator"

async def verify_admin_access(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify user has admin privileges"""
    admin_result = await db.execute(select(AdminUser).where(AdminUser.id == current_user_id))
    admin_user = admin_result.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin_user

@router.post("/create-vpn-user")
async def create_vpn_user(
    request: CreateVPNUserRequest,
    admin_user: AdminUser = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Create VPN user - saves to users table"""
    try:
        # Check if user email exists
        existing = await db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User email already exists")
        
        new_user = User(
            name=request.name,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            phone=request.phone,
            country=request.country,
            is_email_verified=True  # Auto-verify admin-created users
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return {
            "message": "VPN user created successfully",
            "user_id": new_user.user_id,
            "email": new_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"VPN user creation failed: {str(e)}")

@router.post("/create-admin-user")
async def create_admin_user(
    request: CreateAdminUserRequest,
    admin_user: AdminUser = Depends(verify_admin_access),
    db: AsyncSession = Depends(get_db)
):
    """Create admin user - saves to admin_users table"""
    try:
        # Check if admin username/email exists
        existing = await db.execute(
            select(AdminUser).where(
                (AdminUser.username == request.username) | (AdminUser.email == request.email)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Validate admin role
        if request.role not in ["super_admin", "admin", "moderator"]:
            raise HTTPException(status_code=400, detail="Invalid admin role")
        
        new_admin = AdminUser(
            username=request.username,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            role=AdminRole(request.role)
        )
        
        db.add(new_admin)
        await db.commit()
        await db.refresh(new_admin)
        
        return {
            "message": "Admin user created successfully",
            "admin_id": new_admin.admin_id,
            "username": new_admin.username,
            "role": new_admin.role.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Admin user creation failed: {str(e)}")