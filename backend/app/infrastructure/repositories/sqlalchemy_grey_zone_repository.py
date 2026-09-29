from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import GreyZoneEntry, GreyZoneLimit
from app.infrastructure.db.orm_models import GreyZoneEntryORM, GreyZoneLimitORM
from app.interfaces.repositories import GreyZoneRepository


class SqlAlchemyGreyZoneRepository(GreyZoneRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_limits(self, month_id: int) -> list[GreyZoneLimit]:
        orms = self._db.scalars(select(GreyZoneLimitORM).where(GreyZoneLimitORM.month_id == month_id)).all()
        return [GreyZoneLimit.model_validate(orm) for orm in orms]

    def upsert_limit(self, month_id: int, user_id: int, amount: Decimal) -> GreyZoneLimit:
        orm = self._db.scalar(
            select(GreyZoneLimitORM).where(GreyZoneLimitORM.month_id == month_id, GreyZoneLimitORM.user_id == user_id)
        )
        if orm is None:
            orm = GreyZoneLimitORM(month_id=month_id, user_id=user_id)
            self._db.add(orm)
        orm.amount = amount
        self._db.commit()
        self._db.refresh(orm)
        return GreyZoneLimit.model_validate(orm)

    def list_entries(self, month_id: int) -> list[GreyZoneEntry]:
        orms = self._db.scalars(
            select(GreyZoneEntryORM)
            .where(GreyZoneEntryORM.month_id == month_id)
            .order_by(GreyZoneEntryORM.taken_date.desc(), GreyZoneEntryORM.id.desc())
        ).all()
        return [GreyZoneEntry.model_validate(orm) for orm in orms]

    def get_entry(self, entry_id: int) -> GreyZoneEntry | None:
        orm = self._db.get(GreyZoneEntryORM, entry_id)
        return GreyZoneEntry.model_validate(orm) if orm else None

    def create_entry(self, month_id: int, user_id: int, amount: Decimal, taken_date: date) -> GreyZoneEntry:
        orm = GreyZoneEntryORM(month_id=month_id, user_id=user_id, amount=amount, taken_date=taken_date)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return GreyZoneEntry.model_validate(orm)

    def delete_entry(self, entry_id: int) -> None:
        orm = self._db.get(GreyZoneEntryORM, entry_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def sum_taken_by_user(self, month_id: int) -> dict[int, Decimal]:
        stmt = (
            select(GreyZoneEntryORM.user_id, func.coalesce(func.sum(GreyZoneEntryORM.amount), 0))
            .where(GreyZoneEntryORM.month_id == month_id)
            .group_by(GreyZoneEntryORM.user_id)
        )
        return {user_id: Decimal(total) for user_id, total in self._db.execute(stmt).all()}
