from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import User, UserCredentials
from app.infrastructure.db.orm_models import UserORM
from app.interfaces.repositories import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> User | None:
        orm = self._db.get(UserORM, user_id)
        return User.model_validate(orm) if orm else None

    def list_all(self) -> list[User]:
        orms = self._db.scalars(select(UserORM).order_by(UserORM.id)).all()
        return [User.model_validate(orm) for orm in orms]

    def get_credentials_by_email(self, email: str) -> UserCredentials | None:
        orm = self._db.scalar(select(UserORM).where(UserORM.email == email))
        return UserCredentials.model_validate(orm) if orm else None

    def create(self, email: str, password_hash: str, display_name: str) -> User:
        orm = UserORM(email=email, password_hash=password_hash, display_name=display_name)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return User.model_validate(orm)
