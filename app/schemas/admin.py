from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

class RateLimitStatsResponse(BaseModel):
    total_rate_limited_keys: int = Field(..., description="Total number of rate limited keys")
    total_banned_ips: int = Field(..., description="Total number of banned IPs")
    endpoints: Dict[str, int] = Field(..., description="Rate limit counts by endpoint")
    top_ips: List[Dict[str, Any]] = Field(..., description="Top rate limited IPs")

class RateLimitStatusResponse(BaseModel):
    endpoint: str = Field(..., description="Endpoint identifier")
    limit: int = Field(..., description="Request limit")
    burst: int = Field(..., description="Burst allowance")
    window: int = Field(..., description="Time window in seconds")
    current_requests: int = Field(..., description="Current request count")
    burst_used: int = Field(..., description="Burst requests used")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: int = Field(..., description="Unix timestamp when limit resets")

class BanRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=50, description="IP address or user ID to ban")
    duration: int = Field(..., ge=60, le=86400, description="Ban duration in seconds (1 min to 24 hours)")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for the ban")
    
    @validator('identifier')
    def validate_identifier(cls, v):
        import re
        # Allow only alphanumeric, dots, colons, and hyphens (for IPs and safe identifiers)
        if not re.match(r'^[a-zA-Z0-9.:-]+$', v):
            raise ValueError('Identifier contains invalid characters')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        import re
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', v)
        if len(sanitized.strip()) == 0:
            raise ValueError('Reason cannot be empty after sanitization')
        return sanitized

class BanResponse(BaseModel):
    identifier: str
    is_banned: bool
    ban_data: Optional[Dict[str, Any]] = None

class SecurityMetricsResponse(BaseModel):
    rate_limiting: Dict[str, Any]
    ddos_protection: Dict[str, Any]
    suspicious_activity: Dict[str, Any]

class RateLimitConfigResponse(BaseModel):
    rate_limit_enabled: bool
    ddos_protection_enabled: bool
    global_rate_limit: int
    ip_rate_limit: int
    ddos_threshold: int
    ddos_ban_duration: int
    rate_limits: Dict[str, Dict[str, Any]]
    whitelist_ips: List[str]

class TopRateLimitedIP(BaseModel):
    ip: str
    total_requests: int
    endpoints: Dict[str, int]

class CleanupResponse(BaseModel):
    message: str
    cleaned_count: int