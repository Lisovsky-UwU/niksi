from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Reconciliation
from app.infrastructure.db.orm_models import ReconciliationORM
from app.interfaces.repositories import ReconciliationRepository


class SqlAlchemyReconciliationRepository(ReconciliationRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Reconciliation]:
        orms = self._db.scalars(
            select(ReconciliationORM).order_by(ReconciliationORM.balance_date.desc(), ReconciliationORM.id.desc())
        ).all()
        return [Reconciliation.model_validate(orm) for orm in orms]

    def get_latest(self) -> Reconciliation | None:
        orm = self._db.scalar(
            select(ReconciliationORM)
            .order_by(ReconciliationORM.balance_date.desc(), ReconciliationORM.id.desc())
            .limit(1)
        )
        return Reconciliation.model_validate(orm) if orm else None

    def get_by_id(self, reconciliation_id: int) -> Reconciliation | None:
        orm = self._db.get(ReconciliationORM, reconciliation_id)
        return Reconciliation.model_validate(orm) if orm else None

    def create(
        self,
        balance_date: date,
        actual_balance: Decimal,
        expected_balance: Decimal | None,
        difference: Decimal,
        note: str | None,
        created_by_user_id: int,
    ) -> Reconciliation:
        orm = ReconciliationORM(
            balance_date=balance_date,
            actual_balance=actual_balance,
            expected_balance=expected_balance,
            difference=difference,
            note=note,
            created_by_user_id=created_by_user_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return Reconciliation.model_validate(orm)

    def delete(self, reconciliation_id: int) -> None:
        orm = self._db.get(ReconciliationORM, reconciliation_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def sum_difference_between(self, start: date, end: date) -> Decimal:
        total = self._db.scalar(
            select(func.coalesce(func.sum(ReconciliationORM.difference), 0)).where(
                ReconciliationORM.balance_date >= start,
                ReconciliationORM.balance_date <= end,
            )
        )
        return Decimal(total)
