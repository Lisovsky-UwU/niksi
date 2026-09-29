"""Savings pots: a savings account, a deposit, or a goal to save up for.

Money moved "in" leaves the shared budget, "out" returns to it, and "interest" grows the
pot without touching the budget.
"""

from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import SavingsPot, SavingsPotKind, SavingsTransfer, SavingsTransferDirection
from app.interfaces.repositories import SavingsRepository


def _signed(direction: SavingsTransferDirection, amount: Decimal) -> Decimal:
    return -amount if direction == "out" else amount


class ListSavingsPotsUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(self, include_archived: bool = False) -> list[SavingsPot]:
        return self._savings_repo.list_pots(include_archived)


class CreateSavingsPotUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(
        self,
        name: str,
        kind: SavingsPotKind,
        target_amount: Decimal | None,
        target_date: date | None,
    ) -> SavingsPot:
        if kind == "goal" and target_amount is None:
            raise ValidationError("A goal needs a target amount")
        return self._savings_repo.create_pot(name, kind, target_amount, target_date)


class UpdateSavingsPotUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(
        self,
        pot_id: int,
        name: str,
        target_amount: Decimal | None,
        target_date: date | None,
        is_archived: bool,
    ) -> SavingsPot:
        pot = self._savings_repo.get_pot(pot_id)
        if pot is None:
            raise NotFoundError(f"Savings pot {pot_id} not found")
        if pot.kind == "goal" and target_amount is None:
            raise ValidationError("A goal needs a target amount")
        return self._savings_repo.update_pot(pot_id, name, target_amount, target_date, is_archived)


class DeleteSavingsPotUseCase:
    """Only empty pots with no history can be deleted; anything else should be archived,
    otherwise past months and reconciliations would silently change."""

    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(self, pot_id: int) -> None:
        if self._savings_repo.get_pot(pot_id) is None:
            raise NotFoundError(f"Savings pot {pot_id} not found")
        if self._savings_repo.has_transfers(pot_id):
            raise ValidationError("The pot has transfers; archive it instead of deleting")
        self._savings_repo.delete_pot(pot_id)


class ListSavingsTransfersUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(self, pot_id: int) -> list[SavingsTransfer]:
        if self._savings_repo.get_pot(pot_id) is None:
            raise NotFoundError(f"Savings pot {pot_id} not found")
        return self._savings_repo.list_transfers(pot_id)


class AddSavingsTransferUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(
        self,
        pot_id: int,
        direction: SavingsTransferDirection,
        amount: Decimal,
        transfer_date: date,
        note: str | None,
        created_by_user_id: int,
    ) -> SavingsTransfer:
        pot = self._savings_repo.get_pot(pot_id)
        if pot is None:
            raise NotFoundError(f"Savings pot {pot_id} not found")
        if pot.is_archived:
            raise ValidationError("The pot is archived")
        if direction == "out" and amount > pot.balance:
            raise ValidationError("Cannot take out more than the pot holds")
        return self._savings_repo.create_transfer(pot_id, direction, amount, transfer_date, note, created_by_user_id)


class DeleteSavingsTransferUseCase:
    def __init__(self, savings_repo: SavingsRepository) -> None:
        self._savings_repo = savings_repo

    def execute(self, transfer_id: int) -> None:
        transfer = self._savings_repo.get_transfer(transfer_id)
        if transfer is None:
            raise NotFoundError(f"Savings transfer {transfer_id} not found")
        pot = self._savings_repo.get_pot(transfer.pot_id)
        assert pot is not None
        if pot.balance - _signed(transfer.direction, transfer.amount) < 0:
            raise ValidationError("Removing this transfer would make the pot balance negative")
        self._savings_repo.delete_transfer(transfer_id)
