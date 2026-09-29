from decimal import Decimal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.domain.models import Month
from app.infrastructure.db.orm_models import MonthORM
from app.interfaces.repositories import MonthRepository


class SqlAlchemyMonthRepository(MonthRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, month_id: int) -> Month | None:
        orm = self._db.get(MonthORM, month_id)
        return Month.model_validate(orm) if orm else None

    def get_by_year_month(self, year: int, month: int) -> Month | None:
        orm = self._db.scalar(select(MonthORM).where(MonthORM.year == year, MonthORM.month == month))
        return Month.model_validate(orm) if orm else None

    def get_previous(self, year: int, month: int) -> Month | None:
        orm = self._db.scalar(
            select(MonthORM)
            .where(or_(MonthORM.year < year, and_(MonthORM.year == year, MonthORM.month < month)))
            .order_by(MonthORM.year.desc(), MonthORM.month.desc())
            .limit(1)
        )
        return Month.model_validate(orm) if orm else None

    def list_all(self) -> list[Month]:
        orms = self._db.scalars(select(MonthORM).order_by(MonthORM.year.desc(), MonthORM.month.desc())).all()
        return [Month.model_validate(orm) for orm in orms]

    def create(self, year: int, month: int) -> Month:
        orm = MonthORM(year=year, month=month)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return Month.model_validate(orm)

    def set_carryover_override(self, month_id: int, amount: Decimal | None) -> Month:
        orm = self._db.get(MonthORM, month_id)
        assert orm is not None
        orm.carryover_override = amount
        self._db.commit()
        self._db.refresh(orm)
        return Month.model_validate(orm)
