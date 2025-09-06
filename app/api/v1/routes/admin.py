from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.services.rate_limit_service import rate_limit_service
from app.dependencies.admin import get_current_admin_user
from app.schemas.admin import RateLimitStatsResponse, BanRequest, RateLimitStatusResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/rate-limits/stats", response_model=RateLimitStatsResponse)
async def get_rate_limit_stats(
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive rate limiting statistics"""
    try:
        stats = await rate_limit_service.get_rate_limit_stats()
        return RateLimitStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit statistics")

@router.get("/rate-limits/top-ips")
async def get_top_rate_limited_ips(
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_admin_user)
):
    """Get top rate limited IP addresses"""
    try:
        top_ips = await rate_limit_service.get_top_rate_limited_ips(limit)
        return {"top_ips": top_ips, "limit": limit}
    except Exception as e:
        logger.error(f"Error getting top rate limited IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve top rate limited IPs")

@router.get("/rate-limits/status/{identifier}")
async def get_rate_limit_status(
    identifier: str,
    endpoint: str = Query(..., description="Endpoint key (e.g., auth_login, api_general)"),
    current_user = Depends(get_current_admin_user)
):
    from app.utils.security import sanitize_identifier
    
    # Validate and sanitize inputs
    safe_identifier = sanitize_identifier(identifier)
    safe_endpoint = sanitize_identifier(endpoint)
    
    # Validate endpoint is in allowed list
    allowed_endpoints = list(settings.RATE_LIMITS.keys())
    if safe_endpoint not in allowed_endpoints:
        raise HTTPException(status_code=400, detail="Invalid endpoint key")
    """Get rate limit status for specific identifier and endpoint"""
    try:
        status = await rate_limit_service.get_rate_limit_status(safe_identifier, safe_endpoint)
        return RateLimitStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting rate limit status for {identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit status")

@router.delete("/rate-limits/reset/{identifier}")
async def reset_rate_limit(
    identifier: str,
    endpoint: str = Query(..., description="Endpoint key to reset"),
    current_user = Depends(get_current_admin_user)
):
    from app.utils.security import sanitize_identifier
    
    # Validate and sanitize inputs
    safe_identifier = sanitize_identifier(identifier)
    safe_endpoint = sanitize_identifier(endpoint)
    
    # Validate endpoint is in allowed list
    allowed_endpoints = list(settings.RATE_LIMITS.keys())
    if safe_endpoint not in allowed_endpoints:
        raise HTTPException(status_code=400, detail="Invalid endpoint key")
    """Reset rate limit for specific identifier and endpoint"""
    try:
        success = await rate_limit_service.reset_rate_limit(safe_identifier, safe_endpoint)
        if success:
            from app.utils.security import sanitize_for_logging
            safe_log_identifier = sanitize_for_logging(safe_identifier)
            safe_log_endpoint = sanitize_for_logging(safe_endpoint)
            safe_email = sanitize_for_logging(current_user.email)
            logger.info(f"Rate limit reset for {safe_log_identifier} on {safe_log_endpoint} by admin {safe_email}")
            return {"message": f"Rate limit reset for {safe_identifier} on {safe_endpoint}", "success": True}
        else:
            return {"message": f"No rate limit found for {safe_identifier} on {safe_endpoint}", "success": False}
    except Exception as e:
        logger.error(f"Error resetting rate limit for {identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset rate limit")

@router.post("/bans")
async def ban_identifier(
    ban_request: BanRequest,
    current_user = Depends(get_current_admin_user)
):
    """Ban an identifier (IP address or user ID)"""
    try:
        await rate_limit_service.ban_identifier(
            identifier=ban_request.identifier,
            duration=ban_request.duration,
            reason=f"Admin ban by {current_user.email}: {ban_request.reason}"
        )
        
        from app.utils.security import sanitize_for_logging
        safe_identifier = sanitize_for_logging(ban_request.identifier)
        safe_email = sanitize_for_logging(current_user.email)
        logger.info(f"Identifier {safe_identifier} banned by admin {safe_email}")
        return {
            "message": f"Identifier {ban_request.identifier} banned successfully",
            "duration": ban_request.duration,
            "reason": ban_request.reason
        }
    except Exception as e:
        logger.error(f"Error banning identifier {ban_request.identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to ban identifier")

@router.delete("/bans/{identifier}")
async def unban_identifier(
    identifier: str,
    current_user = Depends(get_current_admin_user)
):
    """Remove ban for identifier"""
    try:
        success = await rate_limit_service.unban_identifier(identifier)
        if success:
            from app.utils.security import sanitize_for_logging
            safe_identifier = sanitize_for_logging(identifier)
            safe_email = sanitize_for_logging(current_user.email)
            logger.info(f"Identifier {safe_identifier} unbanned by admin {safe_email}")
            return {"message": f"Identifier {identifier} unbanned successfully", "success": True}
        else:
            return {"message": f"No ban found for identifier {identifier}", "success": False}
    except Exception as e:
        logger.error(f"Error unbanning identifier {identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unban identifier")

@router.get("/bans/{identifier}")
async def check_ban_status(
    identifier: str,
    current_user = Depends(get_current_admin_user)
):
    """Check if identifier is banned"""
    try:
        is_banned, ban_data = await rate_limit_service.is_banned(identifier)
        return {
            "identifier": identifier,
            "is_banned": is_banned,
            "ban_data": ban_data
        }
    except Exception as e:
        logger.error(f"Error checking ban status for {identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check ban status")

@router.post("/rate-limits/cleanup")
async def cleanup_expired_entries(
    current_user = Depends(get_current_admin_user)
):
    """Clean up expired rate limit entries"""
    try:
        cleaned_count = await rate_limit_service.cleanup_expired_entries()
        from app.utils.security import sanitize_for_logging
        safe_email = sanitize_for_logging(current_user.email)
        logger.info(f"Cleaned up {cleaned_count} expired rate limit entries by admin {safe_email}")
        return {
            "message": f"Cleaned up {cleaned_count} expired entries",
            "cleaned_count": cleaned_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up expired entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup expired entries")

@router.get("/rate-limits/config")
async def get_rate_limit_config(
    current_user = Depends(get_current_admin_user)
):
    """Get current rate limiting configuration"""
    return {
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "ddos_protection_enabled": settings.DDOS_PROTECTION_ENABLED,
        "global_rate_limit": settings.GLOBAL_RATE_LIMIT,
        "ip_rate_limit": settings.IP_RATE_LIMIT,
        "ddos_threshold": settings.DDOS_THRESHOLD,
        "ddos_ban_duration": settings.DDOS_BAN_DURATION,
        "rate_limits": settings.RATE_LIMITS,
        "whitelist_ips": settings.DDOS_WHITELIST_IPS
    }

@router.get("/security/metrics")
async def get_security_metrics(
    current_user = Depends(get_current_admin_user)
):
    """Get security-related metrics"""
    try:
        # This would integrate with your monitoring system
        # For now, return basic metrics from rate limiting
        stats = await rate_limit_service.get_rate_limit_stats()
        
        return {
            "rate_limiting": {
                "total_rate_limited_keys": stats["total_rate_limited_keys"],
                "total_banned_ips": stats["total_banned_ips"],
                "endpoints": stats["endpoints"]
            },
            "ddos_protection": {
                "enabled": settings.DDOS_PROTECTION_ENABLED,
                "threshold": settings.DDOS_THRESHOLD,
                "whitelist_count": len(settings.DDOS_WHITELIST_IPS)
            },
            "suspicious_activity": {
                "threshold": settings.SUSPICIOUS_ACTIVITY_THRESHOLD,
                "window": settings.SUSPICIOUS_ACTIVITY_WINDOW,
                "ban_duration": settings.SUSPICIOUS_ACTIVITY_BAN
            }
        }
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security metrics")