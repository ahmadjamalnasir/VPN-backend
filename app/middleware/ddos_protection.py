from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Set
import asyncio
import ipaddress
from app.core.config import get_settings
from app.utils.security import sanitize_for_logging, validate_ip_address, rate_limit_key_sanitizer
import logging

logger = logging.getLogger(__name__)

class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.redis = None
        self.redis_available = False
        self.whitelist_ips: Set[str] = set(self.settings.DDOS_WHITELIST_IPS)
        self.banned_ips: Dict[str, datetime] = {}
        
    async def _init_redis(self):
        """Initialize Redis connection with fallback"""
        if self.redis is None:
            try:
                self.redis = redis.from_url(self.settings.REDIS_URL)
                await self.redis.ping()
                self.redis_available = True
                logger.info("✅ Redis connected for DDoS protection")
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.warning(f"⚠️ Redis unavailable, using in-memory DDoS protection: {safe_error}")
                self.redis_available = False
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not self.settings.DDOS_PROTECTION_ENABLED:
            return await call_next(request)
        
        await self._init_redis()
        
        client_ip = self._get_client_ip(request)
        
        # Skip whitelisted IPs
        if self._is_whitelisted(client_ip):
            return await call_next(request)
            
        # Check if IP is banned
        if await self._is_ip_banned(client_ip):
            safe_ip = sanitize_for_logging(client_ip)
            logger.warning(f"Blocked banned IP: {safe_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "IP_BANNED",
                    "message": "Your IP has been temporarily banned due to suspicious activity",
                    "retry_after": self.settings.DDOS_BAN_DURATION
                },
                headers={"Retry-After": str(self.settings.DDOS_BAN_DURATION)}
            )
        
        # Check DDoS threshold
        if await self._check_ddos_threshold(client_ip):
            await self._ban_ip(client_ip)
            safe_ip = sanitize_for_logging(client_ip)
            logger.warning(f"IP banned for DDoS activity: {safe_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "DDOS_DETECTED",
                    "message": "DDoS activity detected. IP banned temporarily",
                    "retry_after": self.settings.DDOS_BAN_DURATION
                }
            )
        
        # Track request
        await self._track_request(client_ip)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers with security validation"""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
            if validate_ip_address(ip):
                return ip
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            ip = real_ip.strip()
            if validate_ip_address(ip):
                return ip
        
        # Fall back to direct client IP
        if request.client and request.client.host:
            ip = request.client.host
            if validate_ip_address(ip):
                return ip
        
        return "unknown"
    
    def _is_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist with security validation"""
        if ip == "unknown":
            return False
            
        try:
            client_ip = ipaddress.ip_address(ip)
            for whitelist_ip in self.whitelist_ips:
                try:
                    if "/" in whitelist_ip:  # CIDR notation
                        if client_ip in ipaddress.ip_network(whitelist_ip, strict=False):
                            return True
                    else:  # Single IP
                        if str(client_ip) == whitelist_ip:
                            return True
                except (ValueError, ipaddress.AddressValueError):
                    safe_whitelist = sanitize_for_logging(whitelist_ip)
                    logger.warning(f"Invalid whitelist IP format: {safe_whitelist}")
                    continue
        except (ValueError, ipaddress.AddressValueError):
            return False
        return False
    
    async def _is_ip_banned(self, ip: str) -> bool:
        """Check if IP is currently banned"""
        if ip == "unknown":
            return False
            
        if self.redis_available:
            try:
                ban_key = rate_limit_key_sanitizer(f"ddos_ban:{ip}")
                return bool(await self.redis.exists(ban_key))
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.error(f"Redis error checking ban status: {safe_error}")
                self.redis_available = False
        
        # Fallback to in-memory
        return ip in self.banned_ips and self.banned_ips[ip] > datetime.now()
    
    async def _ban_ip(self, ip: str) -> None:
        """Ban an IP address"""
        if ip == "unknown":
            return
            
        if self.redis_available:
            try:
                ban_key = rate_limit_key_sanitizer(f"ddos_ban:{ip}")
                await self.redis.setex(ban_key, self.settings.DDOS_BAN_DURATION, "banned")
                return
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.error(f"Redis error banning IP: {safe_error}")
                self.redis_available = False
        
        # Fallback to in-memory
        self.banned_ips[ip] = datetime.now() + timedelta(seconds=self.settings.DDOS_BAN_DURATION)
    
    async def _check_ddos_threshold(self, ip: str) -> bool:
        """Check if IP has exceeded DDoS threshold"""
        if ip == "unknown":
            return False
            
        if self.redis_available:
            try:
                key = rate_limit_key_sanitizer(f"ddos_track:{ip}")
                now = datetime.now().timestamp()
                window_start = now - 60  # 1 minute window
                
                # Count requests in the last minute
                request_count = await self.redis.zcount(key, window_start, now)
                
                return request_count >= self.settings.DDOS_THRESHOLD
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.error(f"Redis error checking DDoS threshold: {safe_error}")
                self.redis_available = False
        
        # Fallback: allow all requests if Redis unavailable
        return False
    
    async def _track_request(self, ip: str) -> None:
        """Track request for DDoS detection"""
        if ip == "unknown":
            return
            
        if self.redis_available:
            try:
                key = rate_limit_key_sanitizer(f"ddos_track:{ip}")
                now = datetime.now().timestamp()
                
                pipe = self.redis.pipeline()
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Remove old requests (older than 1 minute)
                pipe.zremrangebyscore(key, 0, now - 60)
                # Set expiry
                pipe.expire(key, 60)
                await pipe.execute()
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.error(f"Redis error tracking request: {safe_error}")
                self.redis_available = False


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.redis = None
        self.redis_available = False
        self.in_memory_cache = {}
        
    async def _init_redis(self):
        """Initialize Redis connection with fallback"""
        if self.redis is None:
            try:
                self.redis = redis.from_url(self.settings.REDIS_URL)
                await self.redis.ping()
                self.redis_available = True
                logger.info("✅ Redis connected for rate limiting")
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.warning(f"⚠️ Redis unavailable, using in-memory rate limiting: {safe_error}")
                self.redis_available = False
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not self.settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        await self._init_redis()
            
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
            safe_ip = sanitize_for_logging(client_ip)
            logger.warning(f"Rate limit exceeded for {safe_ip} on {endpoint_key}")
            
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
        """Extract client IP from request headers with validation"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
            if validate_ip_address(ip):
                return ip
        
        if request.client and request.client.host:
            ip = request.client.host
            if validate_ip_address(ip):
                return ip
        
        return "unknown"
    
    def _get_endpoint_key(self, path: str, method: str) -> str:
        """Determine rate limit key based on endpoint with security validation"""
        # Sanitize path to prevent cache pollution
        safe_path = sanitize_for_logging(path)
        
        if "/auth/login" in safe_path:
            return "auth_login"
        elif "/auth/signup" in safe_path:
            return "auth_register"
        elif "/vpn/connect" in safe_path:
            return "vpn_connect"
        elif "/payments" in safe_path:
            return "payments"
        else:
            return "api_general"
    
    def _get_limit_for_endpoint(self, endpoint_key: str) -> int:
        """Get rate limit for specific endpoint"""
        return self.settings.RATE_LIMITS.get(endpoint_key, self.settings.RATE_LIMITS["api_general"])["requests"]
    
    async def _check_rate_limit(self, client_ip: str, endpoint_key: str) -> Tuple[bool, int, int]:
        """Check rate limit with Redis fallback and security validation"""
        if client_ip == "unknown":
            return False, 0, 100  # Allow unknown IPs with default limit
            
        limits = self.settings.RATE_LIMITS.get(endpoint_key, self.settings.RATE_LIMITS["api_general"])
        max_requests = limits["requests"]
        window = limits["window"]
        
        if self.redis_available:
            try:
                key = rate_limit_key_sanitizer(f"ratelimit:{endpoint_key}:{client_ip}")
                
                now = datetime.now().timestamp()
                window_start = now - window
                
                pipe = self.redis.pipeline()
                
                # Clean old requests
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Count current requests
                pipe.zcard(key)
                
                results = await pipe.execute()
                current_requests = results[1]
                
                if current_requests >= max_requests:
                    retry_after = int(window - (now - window_start))
                    return True, retry_after, 0
                
                # Track this request
                pipe = self.redis.pipeline()
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window)
                await pipe.execute()
                
                remaining = max_requests - current_requests - 1
                return False, 0, remaining
            except Exception as e:
                safe_error = sanitize_for_logging(str(e))
                logger.error(f"Redis error in rate limiting: {safe_error}")
                self.redis_available = False
        
        # Fallback: allow all requests if Redis unavailable
        return False, 0, max_requests