import pytest
from app.utils.security import sanitize_for_logging, validate_ip_address, sanitize_identifier
from app.schemas.admin import BanRequest
from pydantic import ValidationError

class TestSecurityFixes:
    
    def test_sanitize_for_logging(self):
        """Test log injection prevention"""
        # Test newline removal
        malicious_input = "test\nmalicious\rlog\tentry"
        result = sanitize_for_logging(malicious_input)
        assert "\n" not in result
        assert "\r" not in result
        assert "\t" not in result
        
        # Test HTML escaping
        html_input = "<script>alert('xss')</script>"
        result = sanitize_for_logging(html_input)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        
        # Test length truncation
        long_input = "a" * 300
        result = sanitize_for_logging(long_input)
        assert len(result) <= 203  # 200 + "..."
        
    def test_validate_ip_address(self):
        """Test IP address validation"""
        # Valid IPs
        assert validate_ip_address("192.168.1.1") == True
        assert validate_ip_address("::1") == True
        assert validate_ip_address("127.0.0.1") == True
        
        # Invalid IPs
        assert validate_ip_address("invalid") == False
        assert validate_ip_address("999.999.999.999") == False
        assert validate_ip_address("") == False
        assert validate_ip_address("192.168.1") == False
        
    def test_sanitize_identifier(self):
        """Test identifier sanitization"""
        # Valid identifier
        result = sanitize_identifier("192.168.1.1")
        assert result == "192.168.1.1"
        
        # Remove invalid characters
        malicious = "192.168.1.1'; DROP TABLE users; --"
        result = sanitize_identifier(malicious)
        assert "DROP" not in result
        assert ";" not in result
        assert "--" not in result
        
        # Empty input
        result = sanitize_identifier("")
        assert result == "unknown"
        
        # Too long input
        long_input = "a" * 100
        result = sanitize_identifier(long_input)
        assert len(result) <= 50
        
    def test_ban_request_validation(self):
        """Test BanRequest input validation"""
        # Valid request
        valid_request = BanRequest(
            identifier="192.168.1.1",
            duration=3600,
            reason="Suspicious activity"
        )
        assert valid_request.identifier == "192.168.1.1"
        
        # Invalid identifier with SQL injection attempt
        with pytest.raises(ValidationError):
            BanRequest(
                identifier="'; DROP TABLE users; --",
                duration=3600,
                reason="test"
            )
        
        # Invalid reason with control characters
        request_with_newlines = BanRequest(
            identifier="192.168.1.1",
            duration=3600,
            reason="test\nreason\rwith\tcontrol"
        )
        # Should be sanitized
        assert "\n" not in request_with_newlines.reason
        assert "\r" not in request_with_newlines.reason
        assert "\t" not in request_with_newlines.reason
        
        # Duration validation
        with pytest.raises(ValidationError):
            BanRequest(
                identifier="192.168.1.1",
                duration=30,  # Too short
                reason="test"
            )
        
        with pytest.raises(ValidationError):
            BanRequest(
                identifier="192.168.1.1",
                duration=100000,  # Too long
                reason="test"
            )

if __name__ == "__main__":
    pytest.main([__file__])