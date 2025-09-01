#!/usr/bin/env python3
"""
Setup script for rate limiting and DDoS protection
Run this after initial deployment to configure Redis and test rate limiting
"""

import asyncio
import redis.asyncio as redis
from app.core.config import settings
from app.services.rate_limit_service import rate_limit_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_connection():
    """Test Redis connection"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        logger.info("✅ Redis connection successful")
        await r.close()
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

async def setup_rate_limiting():
    """Setup and test rate limiting functionality"""
    logger.info("🔧 Setting up rate limiting...")
    
    # Test basic rate limiting
    try:
        is_limited, retry_after, remaining = await rate_limit_service.check_rate_limit(
            identifier="setup_test",
            endpoint="test_setup",
            max_requests=5,
            window=60,
            burst=2
        )
        logger.info(f"✅ Rate limiting test: limited={is_limited}, remaining={remaining}")
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False
    
    # Test ban functionality
    try:
        await rate_limit_service.ban_identifier("test_ban_ip", 60, "Setup test")
        is_banned, ban_data = await rate_limit_service.is_banned("test_ban_ip")
        if is_banned:
            logger.info("✅ Ban functionality working")
            await rate_limit_service.unban_identifier("test_ban_ip")
        else:
            logger.error("❌ Ban functionality not working")
            return False
    except Exception as e:
        logger.error(f"❌ Ban functionality test failed: {e}")
        return False
    
    # Test statistics
    try:
        stats = await rate_limit_service.get_rate_limit_stats()
        logger.info(f"✅ Statistics working: {stats['total_rate_limited_keys']} keys tracked")
    except Exception as e:
        logger.error(f"❌ Statistics test failed: {e}")
        return False
    
    return True

async def cleanup_test_data():
    """Clean up test data"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        
        # Clean up test keys
        test_patterns = ["*setup_test*", "*test_ban_ip*", "*test_setup*"]
        for pattern in test_patterns:
            async for key in r.scan_iter(match=pattern):
                await r.delete(key)
        
        await r.close()
        logger.info("✅ Test data cleaned up")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

def print_configuration():
    """Print current rate limiting configuration"""
    logger.info("📋 Current Rate Limiting Configuration:")
    logger.info(f"   Rate Limiting Enabled: {settings.RATE_LIMIT_ENABLED}")
    logger.info(f"   DDoS Protection Enabled: {settings.DDOS_PROTECTION_ENABLED}")
    logger.info(f"   Global Rate Limit: {settings.GLOBAL_RATE_LIMIT} req/min")
    logger.info(f"   IP Rate Limit: {settings.IP_RATE_LIMIT} req/min")
    logger.info(f"   DDoS Threshold: {settings.DDOS_THRESHOLD} req/min")
    logger.info(f"   DDoS Ban Duration: {settings.DDOS_BAN_DURATION} seconds")
    logger.info(f"   Whitelist IPs: {settings.DDOS_WHITELIST_IPS}")
    
    logger.info("\n📋 Endpoint-Specific Limits:")
    for endpoint, limits in settings.RATE_LIMITS.items():
        logger.info(f"   {endpoint}: {limits['requests']} req/{limits['window']}s (burst: {limits.get('burst', 0)})")

async def main():
    """Main setup function"""
    logger.info("🚀 Starting Rate Limiting Setup")
    
    # Print configuration
    print_configuration()
    
    # Test Redis connection
    if not await test_redis_connection():
        logger.error("❌ Setup failed: Redis connection issue")
        return
    
    # Setup rate limiting
    if not await setup_rate_limiting():
        logger.error("❌ Setup failed: Rate limiting issue")
        return
    
    # Clean up test data
    await cleanup_test_data()
    
    logger.info("✅ Rate limiting setup completed successfully!")
    logger.info("\n📚 Next steps:")
    logger.info("   1. Start your FastAPI application")
    logger.info("   2. Monitor rate limiting with: GET /api/v1/admin/rate-limits/stats")
    logger.info("   3. Check health endpoint: GET /health")
    logger.info("   4. Review logs for any rate limiting violations")

if __name__ == "__main__":
    asyncio.run(main())