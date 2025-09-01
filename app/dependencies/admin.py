from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.user import User

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user has admin privileges
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user