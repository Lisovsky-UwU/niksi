from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.models import TelegramChat
from app.infrastructure.db.orm_models import TelegramChatORM
from app.interfaces.repositories import TelegramChatRepository


class SqlAlchemyTelegramChatRepository(TelegramChatRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def _row(self) -> TelegramChatORM | None:
        return self._db.scalar(select(TelegramChatORM).order_by(TelegramChatORM.id.desc()).limit(1))

    def get(self) -> TelegramChat | None:
        orm = self._row()
        return TelegramChat.model_validate(orm) if orm else None

    def bind(self, chat_id: int, user_id: int) -> TelegramChat:
        self._db.execute(delete(TelegramChatORM))
        orm = TelegramChatORM(
            chat_id=chat_id, bound_by_user_id=user_id, notify_enabled=True, daily_summary_enabled=True
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return TelegramChat.model_validate(orm)

    def set_flags(self, notify_enabled: bool | None, daily_summary_enabled: bool | None) -> TelegramChat:
        orm = self._row()
        assert orm is not None
        if notify_enabled is not None:
            orm.notify_enabled = notify_enabled
        if daily_summary_enabled is not None:
            orm.daily_summary_enabled = daily_summary_enabled
        self._db.commit()
        self._db.refresh(orm)
        return TelegramChat.model_validate(orm)

    def mark_summary_sent(self, day: date) -> None:
        orm = self._row()
        if orm is not None:
            orm.last_summary_date = day
            self._db.commit()
