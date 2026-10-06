"""Bank loans: the debt, payments from the shared budget, and a forecast of the payoff.

Regular and early payments leave the shared budget like a move into savings; a correction
only sets the balance to the bank's figure. See app.domain.loans for the arithmetic.
"""

from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.loans import monthly_interest, split_regular
from app.domain.models import Loan, LoanPayment, LoanPaymentKind
from app.interfaces.repositories import LoanRepository


def _validate_terms(rate_percent: Decimal, payment_day: int) -> None:
    if not 0 <= rate_percent < 100:
        raise ValidationError("The rate must be between 0 and 100 percent")
    if not 1 <= payment_day <= 31:
        raise ValidationError("The payment day must be between 1 and 31")


class ListLoansUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(self) -> list[Loan]:
        return self._loan_repo.list_loans()


class CreateLoanUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(
        self,
        name: str,
        principal: Decimal,
        start_date: date,
        rate_percent: Decimal,
        monthly_payment: Decimal,
        payment_day: int,
    ) -> Loan:
        _validate_terms(rate_percent, payment_day)
        return self._loan_repo.create_loan(name, principal, start_date, rate_percent, monthly_payment, payment_day)


class UpdateLoanUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(
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
        if self._loan_repo.get_loan(loan_id) is None:
            raise NotFoundError(f"Loan {loan_id} not found")
        _validate_terms(rate_percent, payment_day)
        return self._loan_repo.update_loan(
            loan_id, name, principal, start_date, rate_percent, monthly_payment, payment_day, is_closed
        )


class DeleteLoanUseCase:
    """Only a loan with no payments can be deleted; otherwise past months and
    reconciliations would silently change, so it should be closed instead."""

    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(self, loan_id: int) -> None:
        if self._loan_repo.get_loan(loan_id) is None:
            raise NotFoundError(f"Loan {loan_id} not found")
        if self._loan_repo.has_payments(loan_id):
            raise ValidationError("The loan has payments; close it instead of deleting")
        self._loan_repo.delete_loan(loan_id)


class ListLoanPaymentsUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(self, loan_id: int) -> list[LoanPayment]:
        if self._loan_repo.get_loan(loan_id) is None:
            raise NotFoundError(f"Loan {loan_id} not found")
        return self._loan_repo.list_payments(loan_id)


class AddLoanPaymentUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(
        self,
        loan_id: int,
        kind: LoanPaymentKind,
        amount: Decimal | None,
        new_balance: Decimal | None,
        payment_date: date,
        note: str | None,
        created_by_user_id: int,
    ) -> LoanPayment:
        """`amount` for regular and early payments, `new_balance` (the bank's figure) for a correction."""
        loan = self._loan_repo.get_loan(loan_id)
        if loan is None:
            raise NotFoundError(f"Loan {loan_id} not found")
        if loan.is_closed:
            raise ValidationError("The loan is closed")

        if kind == "correction":
            if new_balance is None or new_balance < 0:
                raise ValidationError("A correction needs the new balance")
            interest, principal, paid = Decimal(0), loan.balance - new_balance, Decimal(0)
        else:
            if amount is None or amount <= 0:
                raise ValidationError("A payment needs an amount")
            if loan.balance <= 0:
                raise ValidationError("The loan is already paid off")
            if kind == "regular":
                if amount > loan.balance + monthly_interest(loan.balance, loan.rate_percent):
                    raise ValidationError("The payment is larger than the debt with interest")
                interest, principal = split_regular(loan.balance, loan.rate_percent, amount)
            else:
                if amount > loan.balance:
                    raise ValidationError("An early repayment cannot exceed the balance")
                interest, principal = Decimal(0), amount
            paid = amount

        return self._loan_repo.create_payment(
            loan_id, kind, paid, interest, principal, payment_date, note, created_by_user_id
        )


class DeleteLoanPaymentUseCase:
    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    def execute(self, payment_id: int) -> None:
        if self._loan_repo.get_payment(payment_id) is None:
            raise NotFoundError(f"Loan payment {payment_id} not found")
        self._loan_repo.delete_payment(payment_id)
