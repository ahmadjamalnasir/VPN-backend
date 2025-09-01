from functools import wraps
from fastapi import HTTPException, Request
from typing import Callable, Optional
import asyncio
from app.services.rate_limit_service import rate_limit_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def rate_limit(
    endpoint_key: str,
    max_requests: Optional[int] = None,
    window: Optional[int] = None,
    burst: Optional[int] = None,
    per_user: bool = False,
    skip_if_authenticated: bool = False
):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        endpoint_key: Key to identify the endpoint type
        max_requests: Maximum requests allowed (defaults to config)
        window: Time window in seconds (defaults to config)
        burst: Burst allowance (defaults to config)
        per_user: Apply rate limit per authenticated user instead of IP
        skip_if_authenticated: Skip rate limiting for authenticated users
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request object found, proceed without rate limiting
                return await func(*args, **kwargs)
            
            # Skip if rate limiting is disabled
            if not settings.RATE_LIMIT_ENABLED:
                return await func(*args, **kwargs)
            
            # Get rate limit configuration
            limits = settings.RATE_LIMITS.get(endpoint_key, settings.RATE_LIMITS["api_general"])
            actual_max_requests = max_requests or limits["requests"]
            actual_window = window or limits["window"]
            actual_burst = burst or limits.get("burst", 0)
            
            # Determine identifier (IP or user)
            if per_user:
                # Extract user ID from JWT token or session
                identifier = await _get_user_identifier(request)
                if not identifier:
                    identifier = _get_client_ip(request)
            else:
                identifier = _get_client_ip(request)
            
            # Skip for authenticated users if configured
            if skip_if_authenticated:
                user_id = await _get_user_identifier(request)
                if user_id:
                    return await func(*args, **kwargs)
            
            # Check rate limit
            is_limited, retry_after, remaining = await rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_key,
                max_requests=actual_max_requests,
                window=actual_window,
                burst=actual_burst
            )
            
            if is_limited:
                logger.warning(f"Rate limit exceeded for {identifier} on {endpoint_key}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded for {endpoint_key}",
                        "retry_after": retry_after,
                        "endpoint": endpoint_key
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(actual_max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(retry_after)
                    }
                )
            
            # Execute the original function
            response = await func(*args, **kwargs)
            
            # Add rate limit headers if response supports it
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(actual_max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
            
            return response
        
        return wrapper
    return decorator

def strict_rate_limit(max_requests: int, window: int, burst: int = 0):
    """
    Strict rate limiting decorator with custom limits
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request or not settings.RATE_LIMIT_ENABLED:
                return await func(*args, **kwargs)
            
            identifier = _get_client_ip(request)
            endpoint_key = f"strict_{func.__name__}"
            
            is_limited, retry_after, remaining = await rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_key,
                max_requests=max_requests,
                window=window,
                burst=burst
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "STRICT_RATE_LIMIT_EXCEEDED",
                        "message": f"Strict rate limit exceeded: {max_requests} requests per {window} seconds",
                        "retry_after": retry_after
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def adaptive_rate_limit(base_requests: int, window: int, load_factor: float = 1.0):
    """
    Adaptive rate limiting that adjusts based on system load
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request or not settings.RATE_LIMIT_ENABLED:
                return await func(*args, **kwargs)
            
            # Adjust rate limit based on load factor
            adjusted_requests = int(base_requests * load_factor)
            
            identifier = _get_client_ip(request)
            endpoint_key = f"adaptive_{func.__name__}"
            
            is_limited, retry_after, remaining = await rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_key,
                max_requests=adjusted_requests,
                window=window,
                burst=0
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "ADAPTIVE_RATE_LIMIT_EXCEEDED",
                        "message": f"Adaptive rate limit exceeded (current limit: {adjusted_requests})",
                        "retry_after": retry_after
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

async def _get_user_identifier(request: Request) -> Optional[str]:
    """Extract user identifier from request (JWT token, session, etc.)"""
    try:
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT token here
            # For now, we'll use a placeholder
            token = auth_header.split(" ")[1]
            # TODO: Decode JWT and extract user ID
            return None  # Placeholder
        
        # Try to get from session or other auth mechanism
        # This would depend on your authentication implementation
        return None
    except Exception:
        return None

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check X-Forwarded-For header first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"

# Convenience decorators for common endpoints
def auth_rate_limit(func: Callable) -> Callable:
    """Rate limit for authentication endpoints"""
    return rate_limit("auth_login")(func)

def api_rate_limit(func: Callable) -> Callable:
    """Rate limit for general API endpoints"""
    return rate_limit("api_general")(func)

def payment_rate_limit(func: Callable) -> Callable:
    """Rate limit for payment endpoints"""
    return rate_limit("payments")(func)

def vpn_rate_limit(func: Callable) -> Callable:
    """Rate limit for VPN endpoints"""
    return rate_limit("vpn_connect")(func)