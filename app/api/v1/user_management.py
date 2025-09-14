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
    """Verify user has admin privileges (view-only)"""
    from uuid import UUID
    try:
        admin_uuid = UUID(current_user_id)
        admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
        admin_user = admin_result.scalar_one_or_none()
        if not admin_user:
            raise HTTPException(status_code=403, detail="Admin access required")
        return admin_user
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid admin token")

async def verify_super_admin_access(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify user has super admin privileges (full access)"""
    from uuid import UUID
    try:
        admin_uuid = UUID(current_user_id)
        admin_result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
        admin_user = admin_result.scalar_one_or_none()
        if not admin_user or admin_user.role != AdminRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Super admin access required")
        return admin_user
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid admin token")



@router.post("/create-admin-user", tags=["Admin - User Management"])
async def create_admin_user(
    request: CreateAdminUserRequest,
    admin_user = Depends(verify_super_admin_access),
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