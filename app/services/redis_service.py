import redis
from typing import Optional
from datetime import datetime, timedelta
import json
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    def store_refresh_token(self, user_id: str, token_jti: str, expires_in: int) -> None:
        """Store refresh token JTI with user context"""
        key = f"refresh_token:{token_jti}"
        value = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        self.redis_client.setex(key, expires_in, json.dumps(value))

    def validate_refresh_token(self, token_jti: str) -> Optional[str]:
        """Validate refresh token and return user_id if valid"""
        key = f"refresh_token:{token_jti}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)["user_id"]
        return None

    def revoke_refresh_token(self, token_jti: str) -> None:
        """Revoke a refresh token"""
        key = f"refresh_token:{token_jti}"
        self.redis_client.delete(key)

    def blacklist_access_token(self, token_jti: str, expires_in: int) -> None:
        """Add access token to blacklist"""
        key = f"blacklist:{token_jti}"
        self.redis_client.setex(key, expires_in, "")

    def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        key = f"blacklist:{token_jti}"
        return bool(self.redis_client.exists(key))

    def store_email_verification_token(self, email: str, token: str) -> None:
        """Store email verification token"""
        key = f"email_verify:{token}"
        self.redis_client.setex(key, settings.EMAIL_VERIFICATION_TOKEN_EXPIRES, email)

    def get_email_from_verification_token(self, token: str) -> Optional[str]:
        """Get email from verification token"""
        key = f"email_verify:{token}"
        return self.redis_client.get(key)

    def store_user_session(self, user_id: str, session_id: str, device_info: dict) -> None:
        """Store user session information"""
        key = f"user_sessions:{user_id}:{session_id}"
        self.redis_client.setex(
            key,
            settings.SESSION_EXPIRES_IN,
            json.dumps({**device_info, "last_active": datetime.utcnow().isoformat()})
        )

    def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user"""
        pattern = f"user_sessions:{user_id}:*"
        sessions = []
        for key in self.redis_client.scan_iter(match=pattern):
            data = self.redis_client.get(key)
            if data:
                session_id = key.split(":")[-1]
                sessions.append({
                    "id": session_id,
                    **json.loads(data)
                })
        return sessions

    def delete_user_session(self, user_id: str, session_id: str) -> None:
        """Delete a specific user session"""
        key = f"user_sessions:{user_id}:{session_id}"
        self.redis_client.delete(key)

redis_service = RedisService()
