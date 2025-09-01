import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import asyncio
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        
    async def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str, 
        max_requests: int, 
        window: int,
        burst: int = 0
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for identifier and endpoint
        Returns: (is_limited, retry_after, remaining_requests)
        """
        key = f"rl:{endpoint}:{identifier}"
        burst_key = f"rl_burst:{endpoint}:{identifier}"
        
        now = datetime.now().timestamp()
        window_start = now - window
        
        pipe = self.redis.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Get burst usage
        pipe.get(burst_key)
        
        results = await pipe.execute()
        current_requests = results[1]
        burst_used = int(results[2] or 0)
        
        # Calculate available requests including burst
        available_burst = max(0, burst - burst_used)
        total_available = max_requests + available_burst
        
        if current_requests >= total_available:
            retry_after = int(window - (now - window_start))
            return True, retry_after, 0
        
        # Record this request
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        
        # Use burst if regular limit exceeded
        if current_requests >= max_requests and available_burst > 0:
            pipe.incr(burst_key)
            pipe.expire(burst_key, window)
        
        await pipe.execute()
        
        remaining = total_available - current_requests - 1
        return False, 0, remaining
    
    async def get_rate_limit_status(self, identifier: str, endpoint: str) -> Dict:
        """Get current rate limit status for identifier and endpoint"""
        limits = settings.RATE_LIMITS.get(endpoint, settings.RATE_LIMITS["api_general"])
        key = f"rl:{endpoint}:{identifier}"
        burst_key = f"rl_burst:{endpoint}:{identifier}"
        
        now = datetime.now().timestamp()
        window_start = now - limits["window"]
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.get(burst_key)
        
        results = await pipe.execute()
        current_requests = results[1]
        burst_used = int(results[2] or 0)
        
        return {
            "endpoint": endpoint,
            "limit": limits["requests"],
            "burst": limits.get("burst", 0),
            "window": limits["window"],
            "current_requests": current_requests,
            "burst_used": burst_used,
            "remaining": max(0, limits["requests"] + limits.get("burst", 0) - current_requests),
            "reset_time": int(now + limits["window"])
        }
    
    async def reset_rate_limit(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limit for identifier and endpoint (admin function)"""
        key = f"rl:{endpoint}:{identifier}"
        burst_key = f"rl_burst:{endpoint}:{identifier}"
        
        pipe = self.redis.pipeline()
        pipe.delete(key)
        pipe.delete(burst_key)
        
        results = await pipe.execute()
        return any(results)
    
    async def ban_identifier(self, identifier: str, duration: int, reason: str = "manual") -> None:
        """Ban an identifier for specified duration"""
        ban_key = f"banned:{identifier}"
        ban_data = {
            "reason": reason,
            "banned_at": datetime.now().isoformat(),
            "duration": duration
        }
        await self.redis.setex(ban_key, duration, json.dumps(ban_data))
        logger.info(f"Banned {identifier} for {duration} seconds. Reason: {reason}")
    
    async def unban_identifier(self, identifier: str) -> bool:
        """Remove ban for identifier"""
        ban_key = f"banned:{identifier}"
        result = await self.redis.delete(ban_key)
        if result:
            logger.info(f"Unbanned {identifier}")
        return bool(result)
    
    async def is_banned(self, identifier: str) -> Tuple[bool, Optional[Dict]]:
        """Check if identifier is banned"""
        ban_key = f"banned:{identifier}"
        ban_data = await self.redis.get(ban_key)
        
        if ban_data:
            try:
                data = json.loads(ban_data)
                return True, data
            except json.JSONDecodeError:
                return True, {"reason": "unknown"}
        
        return False, None
    
    async def get_top_rate_limited_ips(self, limit: int = 10) -> List[Dict]:
        """Get top rate limited IPs for monitoring"""
        pattern = "rl:*:*"
        top_ips = {}
        
        async for key in self.redis.scan_iter(match=pattern):
            parts = key.split(":")
            if len(parts) >= 3:
                endpoint = parts[1]
                ip = parts[2]
                
                count = await self.redis.zcard(key)
                if count > 0:
                    if ip not in top_ips:
                        top_ips[ip] = {"ip": ip, "total_requests": 0, "endpoints": {}}
                    
                    top_ips[ip]["total_requests"] += count
                    top_ips[ip]["endpoints"][endpoint] = count
        
        # Sort by total requests and return top N
        sorted_ips = sorted(top_ips.values(), key=lambda x: x["total_requests"], reverse=True)
        return sorted_ips[:limit]
    
    async def get_rate_limit_stats(self) -> Dict:
        """Get overall rate limiting statistics"""
        stats = {
            "total_rate_limited_keys": 0,
            "total_banned_ips": 0,
            "endpoints": {},
            "top_ips": []
        }
        
        # Count rate limit keys
        rl_pattern = "rl:*"
        async for key in self.redis.scan_iter(match=rl_pattern):
            stats["total_rate_limited_keys"] += 1
            
            parts = key.split(":")
            if len(parts) >= 2:
                endpoint = parts[1]
                if endpoint not in stats["endpoints"]:
                    stats["endpoints"][endpoint] = 0
                stats["endpoints"][endpoint] += 1
        
        # Count banned IPs
        ban_pattern = "banned:*"
        async for key in self.redis.scan_iter(match=ban_pattern):
            stats["total_banned_ips"] += 1
        
        # Get top rate limited IPs
        stats["top_ips"] = await self.get_top_rate_limited_ips(5)
        
        return stats
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired rate limit entries"""
        cleaned = 0
        patterns = ["rl:*", "rl_burst:*", "ddos_track:*", "suspicious:*"]
        
        for pattern in patterns:
            async for key in self.redis.scan_iter(match=pattern):
                # Check if key exists (Redis will auto-expire, but this helps with cleanup)
                if not await self.redis.exists(key):
                    cleaned += 1
        
        return cleaned

# Global instance
rate_limit_service = RateLimitService()