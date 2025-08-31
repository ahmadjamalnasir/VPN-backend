from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import auth_service
from app.crud.user import user_crud
from app.dependencies.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",
    auto_error=True
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token_data = auth_service.validate_token(token)
    user = await user_crud.get(db, token_data.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not token:
        return None
    try:
        token_data = auth_service.validate_token(token)
        return await user_crud.get(db, token_data.sub)
    except HTTPException:
        return None

async def get_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify email is confirmed"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user
