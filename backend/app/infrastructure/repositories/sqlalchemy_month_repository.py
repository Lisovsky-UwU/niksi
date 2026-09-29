from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.domain.models import Month
from app.infrastructure.db.orm_models import MonthORM
from app.interfaces.repositories import MonthRepository


def _after(year: int, month: int):  # type: ignore[no-untyped-def]
    return or_(MonthORM.year > year, and_(MonthORM.year == year, MonthORM.month > month))


class SqlAlchemyMonthRepository(MonthRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def _to_domain(self, orm: MonthORM) -> Month:
        """A period ends the day before the next month's period starts."""
        next_start = self._db.scalar(
            select(MonthORM.start_date)
            .where(_after(orm.year, orm.month))
            .order_by(MonthORM.year, MonthORM.month)
            .limit(1)
        )
        end = next_start - timedelta(days=1) if next_start else None
        return Month.model_validate(orm).model_copy(update={"end_date": end})

    def get_by_id(self, month_id: int) -> Month | None:
        orm = self._db.get(MonthORM, month_id)
        return self._to_domain(orm) if orm else None

    def get_by_year_month(self, year: int, month: int) -> Month | None:
        orm = self._db.scalar(select(MonthORM).where(MonthORM.year == year, MonthORM.month == month))
        return self._to_domain(orm) if orm else None

    def get_previous(self, year: int, month: int) -> Month | None:
        orm = self._db.scalar(
            select(MonthORM)
            .where(or_(MonthORM.year < year, and_(MonthORM.year == year, MonthORM.month < month)))
            .order_by(MonthORM.year.desc(), MonthORM.month.desc())
            .limit(1)
        )
        return self._to_domain(orm) if orm else None

    def get_next(self, year: int, month: int) -> Month | None:
        orm = self._db.scalar(
            select(MonthORM).where(_after(year, month)).order_by(MonthORM.year, MonthORM.month).limit(1)
        )
        return self._to_domain(orm) if orm else None

    def list_all(self) -> list[Month]:
        orms = self._db.scalars(select(MonthORM).order_by(MonthORM.year.desc(), MonthORM.month.desc())).all()
        months: list[Month] = []
        next_start: date | None = None
        # Newest first, so each month's end comes from the one just listed before it.
        for orm in orms:
            end = next_start - timedelta(days=1) if next_start else None
            months.append(Month.model_validate(orm).model_copy(update={"end_date": end}))
            next_start = orm.start_date
        return months

    def create(self, year: int, month: int, start_date: date) -> Month:
        orm = MonthORM(year=year, month=month, start_date=start_date)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm)

    def set_start_date(self, month_id: int, start_date: date) -> Month:
        orm = self._db.get(MonthORM, month_id)
        assert orm is not None
        orm.start_date = start_date
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm)

    def set_carryover_override(self, month_id: int, amount: Decimal | None) -> Month:
        orm = self._db.get(MonthORM, month_id)
        assert orm is not None
        orm.carryover_override = amount
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm)
