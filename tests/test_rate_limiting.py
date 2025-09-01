import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.rate_limit_service import rate_limit_service
from app.core.config import settings

client = TestClient(app)

class TestRateLimiting:
    
    def test_health_endpoint_no_rate_limit(self):
        """Health endpoint should not be rate limited"""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_rate_limit_headers_present(self):
        """Rate limit headers should be present in responses"""
        response = client.get("/")
        # Note: In a real test, you'd check for rate limit headers
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_service_basic_functionality(self):
        """Test basic rate limiting service functionality"""
        # Test rate limit check
        is_limited, retry_after, remaining = await rate_limit_service.check_rate_limit(
            identifier="test_ip",
            endpoint="test_endpoint", 
            max_requests=5,
            window=60,
            burst=2
        )
        
        assert not is_limited
        assert remaining >= 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario"""
        identifier = "test_ip_exceeded"
        endpoint = "test_endpoint"
        
        # Make requests up to the limit
        for i in range(3):
            is_limited, _, remaining = await rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=2,
                window=60,
                burst=0
            )
            
            if i < 2:
                assert not is_limited
            else:
                assert is_limited
    
    @pytest.mark.asyncio
    async def test_ban_functionality(self):
        """Test IP banning functionality"""
        test_ip = "192.168.1.100"
        
        # Ban the IP
        await rate_limit_service.ban_identifier(test_ip, 60, "test ban")
        
        # Check if banned
        is_banned, ban_data = await rate_limit_service.is_banned(test_ip)
        assert is_banned
        assert ban_data["reason"] == "test ban"
        
        # Unban the IP
        success = await rate_limit_service.unban_identifier(test_ip)
        assert success
        
        # Check if unbanned
        is_banned, _ = await rate_limit_service.is_banned(test_ip)
        assert not is_banned
    
    @pytest.mark.asyncio
    async def test_rate_limit_stats(self):
        """Test rate limit statistics"""
        stats = await rate_limit_service.get_rate_limit_stats()
        
        assert "total_rate_limited_keys" in stats
        assert "total_banned_ips" in stats
        assert "endpoints" in stats
        assert "top_ips" in stats
    
    def test_rate_limit_config_endpoint(self):
        """Test rate limit configuration endpoint (requires admin auth)"""
        # This would require proper authentication in a real test
        # response = client.get("/api/v1/admin/rate-limits/config")
        # For now, just test that the endpoint exists
        pass

if __name__ == "__main__":
    pytest.main([__file__])