from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Income, IncomeEntry
from app.infrastructure.db.orm_models import IncomeEntryORM, IncomeORM
from app.interfaces.repositories import IncomeRepository


class SqlAlchemyIncomeRepository(IncomeRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_month(self, month_id: int) -> list[Income]:
        orms = self._db.scalars(select(IncomeORM).where(IncomeORM.month_id == month_id)).all()
        return [Income.model_validate(orm) for orm in orms]

    def get(self, month_id: int, user_id: int) -> Income | None:
        orm = self._db.scalar(
            select(IncomeORM).where(IncomeORM.month_id == month_id, IncomeORM.user_id == user_id)
        )
        return Income.model_validate(orm) if orm else None

    def upsert(self, month_id: int, user_id: int, forecast_amount: Decimal) -> Income:
        orm = self._db.scalar(
            select(IncomeORM).where(IncomeORM.month_id == month_id, IncomeORM.user_id == user_id)
        )
        if orm is None:
            orm = IncomeORM(month_id=month_id, user_id=user_id)
            self._db.add(orm)
        orm.forecast_amount = forecast_amount
        self._db.commit()
        self._db.refresh(orm)
        return Income.model_validate(orm)

    def list_entries(self, month_id: int) -> list[IncomeEntry]:
        orms = self._db.scalars(
            select(IncomeEntryORM)
            .where(IncomeEntryORM.month_id == month_id)
            .order_by(IncomeEntryORM.received_date.desc(), IncomeEntryORM.id.desc())
        ).all()
        return [IncomeEntry.model_validate(orm) for orm in orms]

    def get_entry(self, entry_id: int) -> IncomeEntry | None:
        orm = self._db.get(IncomeEntryORM, entry_id)
        return IncomeEntry.model_validate(orm) if orm else None

    def create_entry(
        self,
        month_id: int,
        user_id: int,
        amount: Decimal,
        description: str | None,
        received_date: date,
        created_by_user_id: int,
    ) -> IncomeEntry:
        orm = IncomeEntryORM(
            month_id=month_id,
            user_id=user_id,
            amount=amount,
            description=description,
            received_date=received_date,
            created_by_user_id=created_by_user_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return IncomeEntry.model_validate(orm)

    def delete_entry(self, entry_id: int) -> None:
        orm = self._db.get(IncomeEntryORM, entry_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def sum_entries_by_user(self, month_id: int) -> dict[int, Decimal]:
        stmt = (
            select(IncomeEntryORM.user_id, func.coalesce(func.sum(IncomeEntryORM.amount), 0))
            .where(IncomeEntryORM.month_id == month_id)
            .group_by(IncomeEntryORM.user_id)
        )
        return {user_id: Decimal(total) for user_id, total in self._db.execute(stmt).all()}
