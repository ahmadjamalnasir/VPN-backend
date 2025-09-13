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
    """Verify user has admin privileges"""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_superuser:
        safe_user_id = sanitize_for_logging(current_user_id)
        logger.warning(f"Unauthorized admin access attempt: {safe_user_id}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    admin_user: User = Depends(verify_admin),
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

@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, max_length=100),
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination and search"""
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

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    request: AdminUserUpdateRequest,
    admin_user: User = Depends(verify_admin),
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

@router.post("/servers", response_model=VPNServerResponse)
async def create_vpn_server(
    request: CreateVPNServerRequest,
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new VPN server"""
    try:
        # Security validation
        if not validate_user_input(request.hostname, max_length=100, allowed_chars="a-zA-Z0-9.-"):
            raise HTTPException(status_code=400, detail="Invalid hostname format")
        
        if not validate_admin_input(request.location, "location"):
            raise HTTPException(status_code=400, detail="Invalid location")
        
        if not validate_ip_address(request.ip_address):
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        # Check for suspicious patterns
        suspicious = check_suspicious_patterns(f"{request.hostname} {request.endpoint}")
        if suspicious:
            safe_hostname = sanitize_for_logging(request.hostname)
            logger.warning(f"Suspicious server creation: {safe_hostname} - {suspicious}")
            raise HTTPException(status_code=400, detail="Invalid server configuration")
        
        server = VPNServer(
            hostname=request.hostname,
            location=request.location,
            ip_address=request.ip_address,
            endpoint=request.endpoint,
            public_key=request.public_key,
            available_ips=request.available_ips,
            is_premium=request.is_premium,
            status="active"
        )
        db.add(server)
        await db.commit()
        await db.refresh(server)
        
        safe_hostname = sanitize_for_logging(request.hostname)
        safe_admin = sanitize_for_logging(admin_user.email)
        logger.info(f"VPN server created by admin {safe_admin}: {safe_hostname}")
        
        return server
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
    request: UpdateVPNServerRequest,
    admin_user: User = Depends(verify_admin),
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
        
        # Validate status if provided
        if request.status is not None:
            if not validate_admin_input(request.status, "server_status"):
                raise HTTPException(status_code=400, detail="Invalid server status")
            server.status = request.status
        
        if request.is_premium is not None:
            server.is_premium = request.is_premium
        
        if request.current_load is not None:
            if not (0.0 <= request.current_load <= 1.0):
                raise HTTPException(status_code=400, detail="Load must be between 0.0 and 1.0")
            server.current_load = request.current_load
        
        await db.commit()
        
        safe_hostname = sanitize_for_logging(server.hostname)
        safe_admin = sanitize_for_logging(admin_user.email)
        logger.info(f"VPN server updated by admin {safe_admin}: {safe_hostname}")
        
        return {"message": "Server updated successfully"}
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
    admin_user: User = Depends(verify_admin),
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