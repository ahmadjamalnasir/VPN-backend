from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import redis.asyncio as redis
from app.core.config import settings


class RateLimiter:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    async def is_rate_limited(
        self, 
        key: str, 
        max_requests: int, 
        window: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if the request should be rate limited.
        Returns (is_limited, retry_after) tuple.
        """
        pipe = await self.redis.pipeline()
        now = datetime.now().timestamp()
        window_start = now - window
        
        # Remove old requests
        await pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        await pipe.zcard(key)
        
        # Add current request
        await pipe.zadd(key, {str(now): now})
        
        # Set expiry on the key
        await pipe.expire(key, window)
        
        # Execute pipeline
        _, current_requests, _, _ = await pipe.execute()
        
        if current_requests > max_requests:
            retry_after = int(window - (now - window_start))
            return True, retry_after
        
        return False, None

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.limiter = RateLimiter()
        
        # Define rate limits for different endpoints
        self.rate_limits = {
            # Auth endpoints - stricter limits
            "auth": {"max_requests": 5, "window": 60},  # 5 requests per minute
            
            # Regular API endpoints
            "api": {"max_requests": 30, "window": 60},  # 30 requests per minute
            
            # WebSocket connections
            "ws": {"max_requests": 2, "window": 60},  # 2 connections per minute
            
            # Payment endpoints
            "payments": {"max_requests": 10, "window": 60},  # 10 requests per minute
        }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        # Skip rate limiting for certain paths (like health checks)
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Determine rate limit category
        category = self._get_rate_limit_category(request.url.path)
        limits = self.rate_limits[category]

        # Get client identifier (IP address or API key)
        client_id = self._get_client_identifier(request)
        
        # Rate limit key combines category and client identifier
        key = f"ratelimit:{category}:{client_id}"
        
        # Check rate limit
        is_limited, retry_after = await self.limiter.is_rate_limited(
            key,
            limits["max_requests"],
            limits["window"]
        )

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)

    def _get_rate_limit_category(self, path: str) -> str:
        """Determine rate limit category based on request path"""
        if path.startswith("/api/v1/auth"):
            return "auth"
        elif path.startswith("/ws"):
            return "ws"
        elif path.startswith("/api/v1/payments"):
            return "payments"
        else:
            return "api"

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier (IP address or API key)"""
        # Prefer API key if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Fall back to forwarded IP or direct IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
            
        return request.client.host if request.client else "unknown"
