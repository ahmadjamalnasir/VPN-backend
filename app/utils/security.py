import re
import html
import ipaddress
from typing import Any, List
from email_validator import validate_email, EmailNotValidError

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

def validate_email_format(email: str) -> bool:
    """Validate email format securely"""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_user_input(input_value: str, max_length: int = 255, allowed_chars: str = None) -> bool:
    """Validate user input with allowlist approach"""
    if not input_value or len(input_value) > max_length:
        return False
    
    if allowed_chars:
        # Use allowlist approach - only allow specified characters
        pattern = f"^[{re.escape(allowed_chars)}]+$"
        return bool(re.match(pattern, input_value))
    
    # Default: alphanumeric, spaces, and common punctuation
    return bool(re.match(r'^[a-zA-Z0-9\s\-_.@+]+$', input_value))

def sanitize_sql_input(value: str) -> str:
    """Sanitize input to prevent SQL injection"""
    if not value:
        return ""
    
    # Remove SQL injection patterns
    dangerous_patterns = [
        r"[';\"\\]",  # Quotes and backslashes
        r"--",        # SQL comments
        r"/\*.*?\*/", # Multi-line comments
        r"\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b"  # SQL keywords
    ]
    
    sanitized = value
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def validate_admin_input(input_value: str, input_type: str) -> bool:
    """Validate admin inputs with strict allowlists"""
    allowlists = {
        "server_status": ["active", "maintenance", "offline"],
        "plan_type": ["free", "monthly", "yearly"],
        "subscription_status": ["active", "expired", "canceled", "pending"],
        "user_role": ["user", "admin", "superuser"],
        "location": ["us-east", "us-west", "eu-west", "ap-south", "ca-central", "uk", "de", "fr", "jp"]
    }
    
    if input_type in allowlists:
        return input_value in allowlists[input_type]
    
    return validate_user_input(input_value)

def check_suspicious_patterns(text: str) -> List[str]:
    """Check for suspicious patterns in user input"""
    suspicious_patterns = [
        (r"<script", "XSS attempt"),
        (r"javascript:", "JavaScript injection"),
        (r"data:text/html", "Data URI injection"),
        (r"vbscript:", "VBScript injection"),
        (r"\b(union|select|insert|update|delete|drop)\b", "SQL injection attempt"),
        (r"\.\.\/", "Path traversal attempt"),
        (r"\/etc\/passwd", "System file access attempt"),
        (r"cmd\.exe|powershell", "Command injection attempt")
    ]
    
    found_patterns = []
    for pattern, description in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(description)
    
    return found_patterns

def rate_limit_key_sanitizer(key: str) -> str:
    """Sanitize keys used in rate limiting to prevent cache pollution"""
    # Only allow alphanumeric, colons, and hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9:-]', '', key)
    
    # Limit length to prevent memory issues
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized or "default"