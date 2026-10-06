from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domain.models import CashFlows
from app.infrastructure.db.orm_models import (
    ExpenseORM,
    GreyZoneEntryORM,
    IncomeEntryORM,
    LoanPaymentORM,
    SavingsTransferORM,
)
from app.interfaces.repositories import LedgerRepository


def _after(date_col: Any, created_col: Any, after_date: date, after_created_at: datetime, until_date: date) -> Any:
    return and_(
        or_(date_col > after_date, and_(date_col == after_date, created_col > after_created_at)),
        date_col <= until_date,
    )


class SqlAlchemyLedgerRepository(LedgerRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def _sum(self, amount_col: Any, *conditions: Any) -> Decimal:
        return Decimal(self._db.scalar(select(func.coalesce(func.sum(amount_col), 0)).where(*conditions)))

    def flows_after(self, after_date: date, after_created_at: datetime, until_date: date) -> CashFlows:
        def window(orm: Any, date_col: Any) -> Any:
            return _after(date_col, orm.created_at, after_date, after_created_at, until_date)

        savings_window = window(SavingsTransferORM, SavingsTransferORM.transfer_date)
        return CashFlows(
            income=self._sum(IncomeEntryORM.amount, window(IncomeEntryORM, IncomeEntryORM.received_date)),
            expenses=self._sum(ExpenseORM.amount, window(ExpenseORM, ExpenseORM.expense_date)),
            grey_zone=self._sum(GreyZoneEntryORM.amount, window(GreyZoneEntryORM, GreyZoneEntryORM.taken_date)),
            savings_in=self._sum(SavingsTransferORM.amount, savings_window, SavingsTransferORM.direction == "in"),
            savings_out=self._sum(SavingsTransferORM.amount, savings_window, SavingsTransferORM.direction == "out"),
            loan_payments=self._sum(
                LoanPaymentORM.amount,
                window(LoanPaymentORM, LoanPaymentORM.payment_date),
                LoanPaymentORM.kind.in_(("regular", "early")),
            ),
        )
