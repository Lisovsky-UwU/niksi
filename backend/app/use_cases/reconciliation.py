"""Reconciliation ("сверка"): comparing the money really on hand with what the records say.

The latest reconciliation is the baseline. Everything recorded after it (income, expenses,
grey zone, moves to and from savings) gives the expected balance now. When the couple
enters the real amount, the difference is stored with the reconciliation and becomes the
new baseline, so small unrecorded spending never piles up into a confusing gap.
"""

from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import BalanceStatus, CashFlows, Reconciliation
from app.interfaces.repositories import LedgerRepository, ReconciliationRepository


class GetBalanceStatusUseCase:
    def __init__(self, reconciliation_repo: ReconciliationRepository, ledger_repo: LedgerRepository) -> None:
        self._reconciliation_repo = reconciliation_repo
        self._ledger_repo = ledger_repo

    def execute(self, today: date) -> BalanceStatus:
        latest = self._reconciliation_repo.get_latest()
        if latest is None:
            return BalanceStatus(last_reconciliation=None, expected_now=None, flows_since=CashFlows())
        flows = self._ledger_repo.flows_after(latest.balance_date, latest.created_at, max(today, latest.balance_date))
        return BalanceStatus(
            last_reconciliation=latest,
            expected_now=latest.actual_balance + flows.net,
            flows_since=flows,
        )


class ListReconciliationsUseCase:
    def __init__(self, reconciliation_repo: ReconciliationRepository) -> None:
        self._reconciliation_repo = reconciliation_repo

    def execute(self) -> list[Reconciliation]:
        return self._reconciliation_repo.list_all()


class CreateReconciliationUseCase:
    def __init__(self, reconciliation_repo: ReconciliationRepository, ledger_repo: LedgerRepository) -> None:
        self._reconciliation_repo = reconciliation_repo
        self._ledger_repo = ledger_repo

    def execute(
        self,
        balance_date: date,
        actual_balance: Decimal,
        note: str | None,
        created_by_user_id: int,
    ) -> Reconciliation:
        latest = self._reconciliation_repo.get_latest()
        if latest is None:
            # The first reconciliation only sets the starting point.
            return self._reconciliation_repo.create(
                balance_date, actual_balance, None, Decimal(0), note, created_by_user_id
            )
        if balance_date < latest.balance_date:
            raise ValidationError("A reconciliation cannot be dated before the previous one")
        flows = self._ledger_repo.flows_after(latest.balance_date, latest.created_at, balance_date)
        expected = latest.actual_balance + flows.net
        return self._reconciliation_repo.create(
            balance_date, actual_balance, expected, actual_balance - expected, note, created_by_user_id
        )


class DeleteReconciliationUseCase:
    """Only the latest reconciliation can be undone: each one is the baseline for the next."""

    def __init__(self, reconciliation_repo: ReconciliationRepository) -> None:
        self._reconciliation_repo = reconciliation_repo

    def execute(self, reconciliation_id: int) -> None:
        if self._reconciliation_repo.get_by_id(reconciliation_id) is None:
            raise NotFoundError(f"Reconciliation {reconciliation_id} not found")
        latest = self._reconciliation_repo.get_latest()
        if latest is None or latest.id != reconciliation_id:
            raise ValidationError("Only the latest reconciliation can be removed")
        self._reconciliation_repo.delete(reconciliation_id)
