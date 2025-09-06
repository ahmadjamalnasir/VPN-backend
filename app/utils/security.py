import re
import html
from typing import Any

def sanitize_for_logging(value: Any) -> str:
    """Sanitize input for safe logging to prevent log injection"""
    if value is None:
        return "None"
    
    # Convert to string
    str_value = str(value)
    
    # Remove or replace dangerous characters
    # Remove newlines, carriage returns, and other control characters
    sanitized = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', str_value)
    
    # HTML encode to prevent XSS in log viewers
    sanitized = html.escape(sanitized)
    
    # Truncate if too long
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    
    return sanitized

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def sanitize_identifier(identifier: str) -> str:
    """Sanitize identifier for safe use in keys and logging"""
    if not identifier:
        return "unknown"
    
    # Keep only alphanumeric, dots, colons, and hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9.:-]', '', identifier)
    
    # Truncate if too long
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    return sanitized or "unknown"