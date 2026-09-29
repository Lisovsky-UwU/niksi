from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Avatar, User, UserCredentials
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

    def get_credentials_by_id(self, user_id: int) -> UserCredentials | None:
        orm = self._db.get(UserORM, user_id)
        return UserCredentials.model_validate(orm) if orm else None

    def update_display_name(self, user_id: int, display_name: str) -> User:
        orm = self._db.get(UserORM, user_id)
        assert orm is not None
        orm.display_name = display_name
        self._db.commit()
        self._db.refresh(orm)
        return User.model_validate(orm)

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        orm = self._db.get(UserORM, user_id)
        assert orm is not None
        orm.password_hash = password_hash
        self._db.commit()

    def get_avatar(self, user_id: int) -> Avatar | None:
        row = self._db.execute(
            select(UserORM.avatar, UserORM.avatar_content_type).where(UserORM.id == user_id)
        ).one_or_none()
        if row is None or row.avatar is None or row.avatar_content_type is None:
            return None
        return Avatar(content_type=row.avatar_content_type, data=row.avatar)

    def set_avatar(self, user_id: int, avatar: Avatar | None) -> User:
        orm = self._db.get(UserORM, user_id)
        assert orm is not None
        if avatar is None:
            orm.avatar = None
            orm.avatar_content_type = None
            orm.avatar_version = None
        else:
            orm.avatar = avatar.data
            orm.avatar_content_type = avatar.content_type
            orm.avatar_version = (orm.avatar_version or 0) + 1
        self._db.commit()
        self._db.refresh(orm)
        return User.model_validate(orm)

    def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        orm = self._db.scalar(select(UserORM).where(UserORM.telegram_user_id == telegram_user_id))
        return User.model_validate(orm) if orm else None

    def set_link_code(self, user_id: int, code: str, expires_at: datetime) -> None:
        orm = self._db.get(UserORM, user_id)
        assert orm is not None
        orm.telegram_link_code = code
        orm.telegram_link_code_expires_at = expires_at
        self._db.commit()

    def find_link_code(self, code: str) -> tuple[User, datetime] | None:
        orm = self._db.scalar(select(UserORM).where(UserORM.telegram_link_code == code))
        if orm is None or orm.telegram_link_code_expires_at is None:
            return None
        return User.model_validate(orm), orm.telegram_link_code_expires_at

    def set_telegram_id(self, user_id: int, telegram_user_id: int | None) -> User:
        orm = self._db.get(UserORM, user_id)
        assert orm is not None
        orm.telegram_user_id = telegram_user_id
        orm.telegram_link_code = None
        orm.telegram_link_code_expires_at = None
        self._db.commit()
        self._db.refresh(orm)
        return User.model_validate(orm)
