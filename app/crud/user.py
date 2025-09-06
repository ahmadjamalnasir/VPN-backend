from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserCRUD:
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, user_create: UserCreate) -> User:
        db_user = User(
            email=user_create.email,
            hashed_password=user_create.password,  # Note: Password should be hashed before creation
            full_name=user_create.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def update(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: int) -> bool:
        user = self.get_by_id(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

# Create a singleton instance
user_crud = UserCRUD()
