from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Income
from app.infrastructure.db.orm_models import IncomeORM
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

    def upsert(
        self,
        month_id: int,
        user_id: int,
        forecast_amount: Decimal,
        actual_amount: Decimal,
    ) -> Income:
        orm = self._db.scalar(
            select(IncomeORM).where(IncomeORM.month_id == month_id, IncomeORM.user_id == user_id)
        )
        if orm is None:
            orm = IncomeORM(month_id=month_id, user_id=user_id)
            self._db.add(orm)
        orm.forecast_amount = forecast_amount
        orm.actual_amount = actual_amount
        self._db.commit()
        self._db.refresh(orm)
        return Income.model_validate(orm)
