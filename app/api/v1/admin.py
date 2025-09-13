from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.user import User
from app.models.vpn_server import VPNServer
from app.models.connection import Connection
from app.models.user_subscription import UserSubscription
from app.schemas.admin import *
from app.services.auth import verify_token
from app.utils.security import (
    validate_admin_input, sanitize_for_logging, validate_ip_address,
    validate_user_input, check_suspicious_patterns
)
from datetime import datetime, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_admin(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify user has admin privileges (view-only)"""
    from app.models.admin_user import AdminUser
    from uuid import UUID
    try:
        admin_uuid = UUID(current_user_id)
        result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            safe_user_id = sanitize_for_logging(current_user_id)
            logger.warning(f"Unauthorized admin access attempt: {safe_user_id}")
            raise HTTPException(status_code=403, detail="Admin access required")
        return admin_user
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid admin token")

async def verify_super_admin(current_user_id: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Verify user has super admin privileges (full access)"""
    from app.models.admin_user import AdminUser, AdminRole
    from uuid import UUID
    try:
        admin_uuid = UUID(current_user_id)
        result = await db.execute(select(AdminUser).where(AdminUser.id == admin_uuid))
        admin_user = result.scalar_one_or_none()
        if not admin_user or admin_user.role != AdminRole.SUPER_ADMIN:
            safe_user_id = sanitize_for_logging(current_user_id)
            logger.warning(f"Unauthorized super admin access attempt: {safe_user_id}")
            raise HTTPException(status_code=403, detail="Super admin access required")
        return admin_user
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid admin token")

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    admin_user = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics"""
    try:
        # User statistics
        total_users = await db.scalar(select(func.count(User.id)))
        active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
        premium_users = await db.scalar(select(func.count(User.id)).where(User.is_premium == True))
        
        # Server statistics
        total_servers = await db.scalar(select(func.count(VPNServer.id)))
        active_servers = await db.scalar(select(func.count(VPNServer.id)).where(VPNServer.status == "active"))
        
        # Connection statistics (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_connections = await db.scalar(
            select(func.count(Connection.id)).where(Connection.status == "connected")
        )
        daily_connections = await db.scalar(
            select(func.count(Connection.id)).where(Connection.created_at >= yesterday)
        )
        
        return AdminDashboardResponse(
            total_users=total_users or 0,
            active_users=active_users or 0,
            premium_users=premium_users or 0,
            total_servers=total_servers or 0,
            active_servers=active_servers or 0,
            active_connections=active_connections or 0,
            daily_connections=daily_connections or 0
        )
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Admin dashboard error: {safe_error}")
        raise HTTPException(status_code=500, detail="Dashboard data unavailable")

@router.get("/vpn-users", response_model=List[AdminUserResponse])
async def get_all_vpn_users(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, max_length=100),
    admin_user = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all VPN users (regular users, not admin users)"""
    try:
        query = select(User)
        
        if search:
            # Security validation for search input
            if not validate_user_input(search, max_length=100):
                raise HTTPException(status_code=400, detail="Invalid search input")
            
            # Check for suspicious patterns
            suspicious = check_suspicious_patterns(search)
            if suspicious:
                safe_search = sanitize_for_logging(search)
                logger.warning(f"Suspicious admin search: {safe_search} - {suspicious}")
                raise HTTPException(status_code=400, detail="Invalid search pattern")
            
            query = query.where(
                User.email.ilike(f"%{search}%") | 
                User.name.ilike(f"%{search}%")
            )
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users
    except HTTPException:
        raise
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Admin users list error: {safe_error}")
        raise HTTPException(status_code=500, detail="Users data unavailable")

@router.get("/admin-users")
async def get_all_admin_users(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    admin_user = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all admin users (backoffice users)"""
    try:
        from app.models.admin_user import AdminUser
        query = select(AdminUser).offset(skip).limit(limit).order_by(AdminUser.created_at.desc())
        result = await db.execute(query)
        admin_users = result.scalars().all()
        
        return [
            {
                "id": str(admin.id),
                "admin_id": admin.admin_id,
                "username": admin.username,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role.value,
                "is_active": admin.is_active,
                "last_login": admin.last_login,
                "created_at": admin.created_at
            }
            for admin in admin_users
        ]
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Admin users list error: {safe_error}")
        raise HTTPException(status_code=500, detail="Admin users data unavailable")

@router.post("/admin-users")
async def create_admin_user(
    username: str = Query(..., description="Admin username"),
    email: str = Query(..., description="Admin email"),
    password: str = Query(..., description="Admin password"),
    full_name: str = Query(..., description="Admin full name"),
    role: str = Query("admin", description="Admin role: super_admin, admin, moderator"),
    admin_user = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new admin user"""
    try:
        from app.models.admin_user import AdminUser, AdminRole
        from app.services.auth import get_password_hash
        
        # Validate role
        if role not in ["super_admin", "admin", "moderator"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Check if username/email exists
        existing = await db.execute(
            select(AdminUser).where(
                (AdminUser.username == username) | (AdminUser.email == email)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Create admin user
        new_admin = AdminUser(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=AdminRole(role)
        )
        
        db.add(new_admin)
        await db.commit()
        await db.refresh(new_admin)
        
        return {"message": "Admin user created successfully", "admin_id": new_admin.admin_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Admin user creation error: {safe_error}")
        raise HTTPException(status_code=500, detail="Admin user creation failed")

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    request: AdminUserUpdateRequest,
    admin_user = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user status (admin only)"""
    try:
        # Validate user_id
        if user_id <= 0 or user_id > 999999999:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from disabling themselves
        if str(user.id) == str(admin_user.id) and request.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        if request.is_active is not None:
            user.is_active = request.is_active
        if request.is_premium is not None:
            user.is_premium = request.is_premium
        if request.is_superuser is not None:
            user.is_superuser = request.is_superuser
        
        await db.commit()
        
        safe_email = sanitize_for_logging(user.email)
        safe_admin = sanitize_for_logging(admin_user.email)
        logger.info(f"User status updated by admin {safe_admin}: {safe_email}")
        
        return {"message": "User status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Admin user update error: {safe_error}")
        raise HTTPException(status_code=500, detail="Update failed")

@router.get("/servers")
async def get_all_servers(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    admin_user = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all VPN servers (premium, free, active, inactive, maintenance)"""
    try:
        query = select(VPNServer).offset(skip).limit(limit).order_by(VPNServer.created_at.desc())
        result = await db.execute(query)
        servers = result.scalars().all()
        
        return [
            {
                "id": str(server.id),
                "hostname": server.hostname,
                "location": server.location,
                "ip_address": server.ip_address,
                "endpoint": server.endpoint,
                "public_key": server.public_key,
                "available_ips": server.available_ips,
                "is_premium": server.is_premium,
                "status": server.status,
                "current_load": server.current_load,
                "created_at": server.created_at.isoformat() if server.created_at else None
            }
            for server in servers
        ]
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Server list error: {safe_error}")
        raise HTTPException(status_code=500, detail="Server list unavailable")

@router.post("/add_server")
async def add_vpn_server(
    hostname: str = Query(..., description="Server hostname"),
    location: str = Query(..., description="Server location"),
    ip_address: str = Query(..., description="Server IP address"),
    endpoint: str = Query(..., description="Server endpoint"),
    public_key: str = Query(..., description="Server public key"),
    available_ips: str = Query(..., description="Available IP range"),
    is_premium: bool = Query(False, description="Premium server flag"),
    status: str = Query("active", description="Server status"),
    admin_user = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Add new VPN server"""
    try:
        # Security validation
        if not validate_user_input(hostname, max_length=100, allowed_chars="a-zA-Z0-9.-"):
            raise HTTPException(status_code=400, detail="Invalid hostname format")
        
        if not validate_ip_address(ip_address):
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        if status not in ["active", "inactive", "maintenance"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, inactive, maintenance")
        
        server = VPNServer(
            hostname=hostname,
            location=location,
            ip_address=ip_address,
            endpoint=endpoint,
            public_key=public_key,
            available_ips=available_ips,
            is_premium=is_premium,
            status=status
        )
        db.add(server)
        await db.commit()
        await db.refresh(server)
        
        safe_hostname = sanitize_for_logging(hostname)
        logger.info(f"VPN server added: {safe_hostname}")
        
        return {
            "message": "VPN server added successfully",
            "server_id": str(server.id),
            "hostname": server.hostname,
            "status": server.status
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Server creation error: {safe_error}")
        raise HTTPException(status_code=500, detail="Server creation failed")

@router.put("/servers/{server_id}")
async def update_vpn_server(
    server_id: str,
    status: str = Query(None, description="Server status: Active, Inactive, Maintenance"),
    is_premium: bool = Query(None, description="Premium server flag"),
    max_load: float = Query(None, description="Maximum server load (0.0-1.0)"),
    admin_user = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update VPN server configuration"""
    try:
        # Validate server_id format (UUID)
        try:
            from uuid import UUID
            UUID(server_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid server ID format")
        
        result = await db.execute(select(VPNServer).where(VPNServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Validate and update status
        if status is not None:
            if status.lower() not in ["active", "inactive", "maintenance"]:
                raise HTTPException(status_code=400, detail="Invalid status. Must be: Active, Inactive, Maintenance")
            server.status = status.lower()
        
        # Update premium flag
        if is_premium is not None:
            server.is_premium = is_premium
        
        # Validate and update max load
        if max_load is not None:
            if not (0.0 <= max_load <= 1.0):
                raise HTTPException(status_code=400, detail="Max load must be between 0.0 and 1.0")
            server.current_load = max_load
        
        await db.commit()
        
        safe_hostname = sanitize_for_logging(server.hostname)
        logger.info(f"VPN server updated: {safe_hostname}")
        
        return {
            "message": "Server updated successfully",
            "server_id": str(server.id),
            "hostname": server.hostname,
            "status": server.status,
            "is_premium": server.is_premium,
            "max_load": server.current_load
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Server update error: {safe_error}")
        raise HTTPException(status_code=500, detail="Server update failed")

@router.delete("/servers/{server_id}")
async def delete_vpn_server(
    server_id: str,
    admin_user = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete VPN server"""
    try:
        # Validate server_id format (UUID)
        try:
            from uuid import UUID
            UUID(server_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid server ID format")
        
        result = await db.execute(select(VPNServer).where(VPNServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        # Check if server has active connections
        active_connections = await db.scalar(
            select(func.count(Connection.id))
            .where(Connection.server_id == server_id, Connection.status == "connected")
        )
        
        if active_connections > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete server with {active_connections} active connections"
            )
        
        safe_hostname = sanitize_for_logging(server.hostname)
        
        await db.delete(server)
        await db.commit()
        
        safe_admin = sanitize_for_logging(admin_user.email)
        logger.info(f"VPN server deleted by admin {safe_admin}: {safe_hostname}")
        
        return {"message": "Server deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Server deletion error: {safe_error}")
        raise HTTPException(status_code=500, detail="Server deletion failed")

@router.get("/rate-limits/config")
async def get_rate_limit_config(
    admin_user = Depends(verify_admin)
):
    """Get current rate limiting configuration"""
    from app.core.config import get_settings
    settings = get_settings()
    
    return {
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "ddos_protection_enabled": settings.DDOS_PROTECTION_ENABLED,
        "rate_limits": settings.RATE_LIMITS,
        "ddos_threshold": settings.DDOS_THRESHOLD,
        "ddos_ban_duration": settings.DDOS_BAN_DURATION,
        "ddos_whitelist_ips": settings.DDOS_WHITELIST_IPS
    }