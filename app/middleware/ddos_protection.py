from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Set
import asyncio
import ipaddress
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = redis.from_url(settings.REDIS_URL)
        self.whitelist_ips: Set[str] = set(settings.DDOS_WHITELIST_IPS)
        self.banned_ips: Dict[str, datetime] = {}
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not settings.DDOS_PROTECTION_ENABLED:
            return await call_next(request)
            
        client_ip = self._get_client_ip(request)
        
        # Skip whitelisted IPs
        if self._is_whitelisted(client_ip):
            return await call_next(request)
            
        # Check if IP is banned
        if await self._is_ip_banned(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "IP_BANNED",
                    "message": "Your IP has been temporarily banned due to suspicious activity",
                    "retry_after": settings.DDOS_BAN_DURATION
                },
                headers={"Retry-After": str(settings.DDOS_BAN_DURATION)}
            )
        
        # Check DDoS threshold
        if await self._check_ddos_threshold(client_ip):
            await self._ban_ip(client_ip)
            from app.utils.security import sanitize_for_logging
            safe_ip = sanitize_for_logging(client_ip)
            logger.warning(f"IP {safe_ip} banned for DDoS activity")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "DDOS_DETECTED",
                    "message": "DDoS activity detected. IP banned temporarily",
                    "retry_after": settings.DDOS_BAN_DURATION
                }
            )
        
        # Track request
        await self._track_request(client_ip)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        from app.utils.security import validate_ip_address, sanitize_identifier
        
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
            if validate_ip_address(ip):
                return sanitize_identifier(ip)
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip and validate_ip_address(real_ip.strip()):
            return sanitize_identifier(real_ip.strip())
        
        # Fall back to direct client IP
        if request.client and request.client.host:
            ip = request.client.host
            if validate_ip_address(ip):
                return sanitize_identifier(ip)
        
        return "unknown"
    
    def _is_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist"""
        try:
            client_ip = ipaddress.ip_address(ip)
            for whitelist_ip in self.whitelist_ips:
                if "/" in whitelist_ip:  # CIDR notation
                    if client_ip in ipaddress.ip_network(whitelist_ip, strict=False):
                        return True
                else:  # Single IP
                    if str(client_ip) == whitelist_ip:
                        return True
        except ValueError:
            pass
        return False
    
    async def _is_ip_banned(self, ip: str) -> bool:
        """Check if IP is currently banned"""
        ban_key = f"ddos_ban:{ip}"
        return bool(await self.redis.exists(ban_key))
    
    async def _ban_ip(self, ip: str) -> None:
        """Ban an IP address"""
        ban_key = f"ddos_ban:{ip}"
        await self.redis.setex(ban_key, settings.DDOS_BAN_DURATION, "banned")
    
    async def _check_ddos_threshold(self, ip: str) -> bool:
        """Check if IP has exceeded DDoS threshold"""
        key = f"ddos_track:{ip}"
        now = datetime.now().timestamp()
        window_start = now - 60  # 1 minute window
        
        # Count requests in the last minute
        request_count = await self.redis.zcount(key, window_start, now)
        
        return request_count >= settings.DDOS_THRESHOLD
    
    async def _track_request(self, ip: str) -> None:
        """Track request for DDoS detection"""
        key = f"ddos_track:{ip}"
        now = datetime.now().timestamp()
        
        pipe = self.redis.pipeline()
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Remove old requests (older than 1 minute)
        pipe.zremrangebyscore(key, 0, now - 60)
        # Set expiry
        pipe.expire(key, 60)
        await pipe.execute()


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = redis.from_url(settings.REDIS_URL)
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
            
        # Skip health checks and static files
        if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
            return await call_next(request)
            
        client_ip = self._get_client_ip(request)
        endpoint_key = self._get_endpoint_key(request.url.path, request.method)
        
        # Check rate limit
        is_limited, retry_after, remaining = await self._check_rate_limit(
            client_ip, endpoint_key
        )
        
        if is_limited:
            # Track failed attempt for suspicious activity detection
            await self._track_failed_attempt(client_ip)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded for {endpoint_key}",
                    "retry_after": retry_after,
                    "remaining": 0
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self._get_limit_for_endpoint(endpoint_key)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(datetime.now().timestamp()) + retry_after)
                }
            )
        
        # Add rate limit headers to successful responses
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._get_limit_for_endpoint(endpoint_key))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        from app.utils.security import validate_ip_address, sanitize_identifier
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
            if validate_ip_address(ip):
                return sanitize_identifier(ip)
        
        if request.client and request.client.host:
            ip = request.client.host
            if validate_ip_address(ip):
                return sanitize_identifier(ip)
        
        return "unknown"
    
    def _get_endpoint_key(self, path: str, method: str) -> str:
        """Determine rate limit key based on endpoint"""
        if "/auth/login" in path:
            return "auth_login"
        elif "/auth/register" in path:
            return "auth_register"
        elif "/auth/refresh" in path:
            return "auth_refresh"
        elif "/auth/reset-password" in path:
            return "password_reset"
        elif "/vpn/connect" in path:
            return "vpn_connect"
        elif "/vpn/disconnect" in path:
            return "vpn_disconnect"
        elif "/payments" in path:
            return "payments"
        elif path.startswith("/ws"):
            return "websocket"
        else:
            return "api_general"
    
    def _get_limit_for_endpoint(self, endpoint_key: str) -> int:
        """Get rate limit for specific endpoint"""
        return settings.RATE_LIMITS.get(endpoint_key, settings.RATE_LIMITS["api_general"])["requests"]
    
    async def _check_rate_limit(self, client_ip: str, endpoint_key: str) -> Tuple[bool, int, int]:
        """Check rate limit with burst support"""
        limits = settings.RATE_LIMITS.get(endpoint_key, settings.RATE_LIMITS["api_general"])
        max_requests = limits["requests"]
        window = limits["window"]
        burst = limits.get("burst", 0)
        
        key = f"ratelimit:{endpoint_key}:{client_ip}"
        burst_key = f"burst:{endpoint_key}:{client_ip}"
        
        now = datetime.now().timestamp()
        window_start = now - window
        
        pipe = self.redis.pipeline()
        
        # Clean old requests
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Check burst allowance
        pipe.get(burst_key)
        
        results = await pipe.execute()
        current_requests = results[1]
        burst_used = int(results[2] or 0)
        
        # Calculate available requests
        available_burst = max(0, burst - burst_used)
        total_available = max_requests + available_burst
        
        if current_requests >= total_available:
            retry_after = int(window - (now - window_start))
            return True, retry_after, 0
        
        # Track this request
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        
        # Use burst if needed
        if current_requests >= max_requests and available_burst > 0:
            pipe.incr(burst_key)
            pipe.expire(burst_key, window)
        
        await pipe.execute()
        
        remaining = total_available - current_requests - 1
        return False, 0, remaining
    
    async def _track_failed_attempt(self, client_ip: str) -> None:
        """Track failed attempts for suspicious activity detection"""
        key = f"suspicious:{client_ip}"
        now = datetime.now().timestamp()
        window_start = now - settings.SUSPICIOUS_ACTIVITY_WINDOW
        
        pipe = self.redis.pipeline()
        # Remove old attempts
        pipe.zremrangebyscore(key, 0, window_start)
        # Add current attempt
        pipe.zadd(key, {str(now): now})
        # Count attempts
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, settings.SUSPICIOUS_ACTIVITY_WINDOW)
        
        results = await pipe.execute()
        attempt_count = results[2]
        
        # Ban if threshold exceeded
        if attempt_count >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD:
            ban_key = f"suspicious_ban:{client_ip}"
            await self.redis.setex(ban_key, settings.SUSPICIOUS_ACTIVITY_BAN, "banned")
            from app.utils.security import sanitize_for_logging
            safe_ip = sanitize_for_logging(client_ip)
            logger.warning(f"IP {safe_ip} banned for suspicious activity ({attempt_count} failed attempts)")