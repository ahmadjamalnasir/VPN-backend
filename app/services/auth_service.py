from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
        self.secret_key = settings.JWT_SECRET
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise self._get_credentials_exception()
            return {"email": email}
        except JWTError:
            raise self._get_credentials_exception()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        try:
            # Validate email format to prevent injection
            validate_email(email)
            return db.query(User).filter(User.email == email).first()
        except EmailNotValidError:
            return None

    def create_user(self, db: Session, user: UserCreate) -> User:
        hashed_password = self.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_current_user_func(self, token: str, db: Session) -> User:
        try:
            token_data = self.validate_token(token)
            user = self.get_user_by_email(db, token_data["email"])
            if user is None:
                raise self._get_credentials_exception()
            return user
        except JWTError:
            raise self._get_credentials_exception()

    async def get_current_user(self, db: Session, token: str) -> User:
        return self.get_current_user_func(token, db)

    async def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def _get_credentials_exception(self):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Create a singleton instance
auth_service = AuthService()

async def get_current_user(
    token: str = Depends(auth_service.oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    return await auth_service.get_current_user(db, token)
