from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.models import Loan, LoanPayment, LoanPaymentKind
from app.infrastructure.db.orm_models import LoanORM, LoanPaymentORM
from app.interfaces.repositories import LoanRepository

_BUDGET_KINDS = ("regular", "early")


class SqlAlchemyLoanRepository(LoanRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def _totals(self, loan_ids: list[int]) -> dict[int, tuple[Decimal, int]]:
        """Per loan: principal paid off so far and the number of regular payments."""
        if not loan_ids:
            return {}
        stmt = (
            select(
                LoanPaymentORM.loan_id,
                func.coalesce(func.sum(LoanPaymentORM.principal_part), 0),
                func.coalesce(func.sum(case((LoanPaymentORM.kind == "regular", 1), else_=0)), 0),
            )
            .where(LoanPaymentORM.loan_id.in_(loan_ids))
            .group_by(LoanPaymentORM.loan_id)
        )
        return {loan_id: (Decimal(paid), int(count)) for loan_id, paid, count in self._db.execute(stmt).all()}

    @staticmethod
    def _to_domain(orm: LoanORM, totals: tuple[Decimal, int] | None) -> Loan:
        paid, regular = totals or (Decimal(0), 0)
        return Loan(
            id=orm.id,
            name=orm.name,
            principal=orm.principal,
            start_date=orm.start_date,
            rate_percent=orm.rate_percent,
            monthly_payment=orm.monthly_payment,
            payment_day=orm.payment_day,
            is_closed=orm.is_closed,
            balance=orm.principal - paid,
            regular_payments=regular,
            last_reminded_due=orm.last_reminded_due,
        )

    def list_loans(self) -> list[Loan]:
        orms = self._db.scalars(select(LoanORM).order_by(LoanORM.is_closed, LoanORM.id)).all()
        totals = self._totals([orm.id for orm in orms])
        return [self._to_domain(orm, totals.get(orm.id)) for orm in orms]

    def get_loan(self, loan_id: int) -> Loan | None:
        orm = self._db.get(LoanORM, loan_id)
        if orm is None:
            return None
        return self._to_domain(orm, self._totals([loan_id]).get(loan_id))

    def create_loan(
        self,
        name: str,
        principal: Decimal,
        start_date: date,
        rate_percent: Decimal,
        monthly_payment: Decimal,
        payment_day: int,
    ) -> Loan:
        orm = LoanORM(
            name=name,
            principal=principal,
            start_date=start_date,
            rate_percent=rate_percent,
            monthly_payment=monthly_payment,
            payment_day=payment_day,
            is_closed=False,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm, None)

    def update_loan(
        self,
        loan_id: int,
        name: str,
        principal: Decimal,
        start_date: date,
        rate_percent: Decimal,
        monthly_payment: Decimal,
        payment_day: int,
        is_closed: bool,
    ) -> Loan:
        orm = self._db.get(LoanORM, loan_id)
        assert orm is not None
        orm.name = name
        orm.principal = principal
        orm.start_date = start_date
        orm.rate_percent = rate_percent
        orm.monthly_payment = monthly_payment
        orm.payment_day = payment_day
        orm.is_closed = is_closed
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm, self._totals([loan_id]).get(loan_id))

    def delete_loan(self, loan_id: int) -> None:
        orm = self._db.get(LoanORM, loan_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def has_payments(self, loan_id: int) -> bool:
        return self._db.scalar(select(LoanPaymentORM.id).where(LoanPaymentORM.loan_id == loan_id).limit(1)) is not None

    def set_last_reminded_due(self, loan_id: int, due: date) -> None:
        orm = self._db.get(LoanORM, loan_id)
        if orm is not None:
            orm.last_reminded_due = due
            self._db.commit()

    def list_payments(self, loan_id: int) -> list[LoanPayment]:
        orms = self._db.scalars(
            select(LoanPaymentORM)
            .where(LoanPaymentORM.loan_id == loan_id)
            .order_by(LoanPaymentORM.payment_date.desc(), LoanPaymentORM.id.desc())
        ).all()
        return [LoanPayment.model_validate(orm) for orm in orms]

    def get_payment(self, payment_id: int) -> LoanPayment | None:
        orm = self._db.get(LoanPaymentORM, payment_id)
        return LoanPayment.model_validate(orm) if orm else None

    def create_payment(
        self,
        loan_id: int,
        kind: LoanPaymentKind,
        amount: Decimal,
        interest_part: Decimal,
        principal_part: Decimal,
        payment_date: date,
        note: str | None,
        created_by_user_id: int,
    ) -> LoanPayment:
        orm = LoanPaymentORM(
            loan_id=loan_id,
            kind=kind,
            amount=amount,
            interest_part=interest_part,
            principal_part=principal_part,
            payment_date=payment_date,
            note=note,
            created_by_user_id=created_by_user_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return LoanPayment.model_validate(orm)

    def delete_payment(self, payment_id: int) -> None:
        orm = self._db.get(LoanPaymentORM, payment_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def sum_budget_payments_between(self, start: date, end: date) -> Decimal:
        total = self._db.scalar(
            select(func.coalesce(func.sum(LoanPaymentORM.amount), 0)).where(
                LoanPaymentORM.payment_date >= start,
                LoanPaymentORM.payment_date <= end,
                LoanPaymentORM.kind.in_(_BUDGET_KINDS),
            )
        )
        return Decimal(total)
