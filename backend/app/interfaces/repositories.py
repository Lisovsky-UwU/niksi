"""Abstract repository contracts. Use cases depend only on these, never on SQLAlchemy.

Concrete implementations live in `infrastructure/repositories/`. Any future storage
backend (or a fake/in-memory implementation for tests) just needs to satisfy these
interfaces.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal

from app.domain.models import (
    Avatar,
    CashFlows,
    Category,
    CategoryColor,
    Expense,
    GreyZoneEntry,
    GreyZoneLimit,
    Income,
    IncomeEntry,
    Month,
    Reconciliation,
    SavingsPot,
    SavingsPotKind,
    SavingsTransfer,
    SavingsTransferDirection,
    User,
    UserCredentials,
)


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...

    @abstractmethod
    def get_credentials_by_email(self, email: str) -> UserCredentials | None: ...

    @abstractmethod
    def create(self, email: str, password_hash: str, display_name: str) -> User: ...

    @abstractmethod
    def get_credentials_by_id(self, user_id: int) -> UserCredentials | None: ...

    @abstractmethod
    def update_display_name(self, user_id: int, display_name: str) -> User: ...

    @abstractmethod
    def update_password_hash(self, user_id: int, password_hash: str) -> None: ...

    @abstractmethod
    def get_avatar(self, user_id: int) -> Avatar | None: ...

    @abstractmethod
    def set_avatar(self, user_id: int, avatar: Avatar | None) -> User:
        """Stores a new avatar (bumping its version), or removes it when None."""
        ...


class MonthRepository(ABC):
    @abstractmethod
    def get_by_id(self, month_id: int) -> Month | None: ...

    @abstractmethod
    def get_by_year_month(self, year: int, month: int) -> Month | None: ...

    @abstractmethod
    def get_previous(self, year: int, month: int) -> Month | None:
        """Nearest existing month strictly before (year, month), or None."""
        ...

    @abstractmethod
    def get_next(self, year: int, month: int) -> Month | None:
        """Nearest existing month strictly after (year, month), or None."""
        ...

    @abstractmethod
    def list_all(self) -> list[Month]:
        """All months, sorted newest first, each with its period end filled in."""
        ...

    @abstractmethod
    def create(self, year: int, month: int, start_date: date) -> Month: ...

    @abstractmethod
    def set_start_date(self, month_id: int, start_date: date) -> Month: ...

    @abstractmethod
    def set_carryover_override(self, month_id: int, amount: Decimal | None) -> Month: ...


class CategoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, category_id: int) -> Category | None: ...

    @abstractmethod
    def list_by_month(self, month_id: int) -> list[Category]:
        """Categories for a month, ordered by position."""
        ...

    @abstractmethod
    def create(
        self,
        month_id: int,
        name: str,
        limit_amount: Decimal,
        position: int,
        color: CategoryColor | None = None,
    ) -> Category: ...

    @abstractmethod
    def update(
        self,
        category_id: int,
        name: str | None,
        limit_amount: Decimal | None,
        position: int | None,
        color: CategoryColor | None = None,
        clear_color: bool = False,
    ) -> Category:
        """None leaves a field unchanged; `clear_color` switches the colour back to automatic."""
        ...

    @abstractmethod
    def delete(self, category_id: int) -> None: ...


class ExpenseRepository(ABC):
    @abstractmethod
    def get_by_id(self, expense_id: int) -> Expense | None: ...

    @abstractmethod
    def list_filtered(self, month_id: int | None, category_id: int | None) -> list[Expense]:
        """Expenses filtered by month (joining through category) and/or category, newest first."""
        ...

    @abstractmethod
    def sum_by_category_for_month(self, month_id: int) -> dict[int, Decimal]:
        """category_id -> total spent, for dashboard aggregation."""
        ...

    @abstractmethod
    def create(
        self,
        category_id: int,
        amount: Decimal,
        description: str | None,
        expense_date: date,
        created_by_user_id: int,
        spent_by_user_id: int,
    ) -> Expense: ...

    @abstractmethod
    def update(
        self,
        expense_id: int,
        amount: Decimal | None,
        description: str | None,
        expense_date: date | None,
        category_id: int | None = None,
        set_description: bool = False,
        spent_by_user_id: int | None = None,
    ) -> Expense:
        """None leaves a field unchanged; with `set_description` the description is
        replaced even by None, so a comment can be erased."""
        ...

    @abstractmethod
    def delete(self, expense_id: int) -> None: ...


class IncomeRepository(ABC):
    @abstractmethod
    def list_by_month(self, month_id: int) -> list[Income]: ...

    @abstractmethod
    def get(self, month_id: int, user_id: int) -> Income | None: ...

    @abstractmethod
    def upsert(self, month_id: int, user_id: int, forecast_amount: Decimal) -> Income: ...

    @abstractmethod
    def list_entries(self, month_id: int) -> list[IncomeEntry]:
        """Actual receipts for a month, newest first."""
        ...

    @abstractmethod
    def get_entry(self, entry_id: int) -> IncomeEntry | None: ...

    @abstractmethod
    def create_entry(
        self,
        month_id: int,
        user_id: int,
        amount: Decimal,
        description: str | None,
        received_date: date,
        created_by_user_id: int,
    ) -> IncomeEntry: ...

    @abstractmethod
    def delete_entry(self, entry_id: int) -> None: ...

    @abstractmethod
    def sum_entries_by_user(self, month_id: int) -> dict[int, Decimal]:
        """user_id -> total actually received this month."""
        ...


class GreyZoneRepository(ABC):
    @abstractmethod
    def list_limits(self, month_id: int) -> list[GreyZoneLimit]: ...

    @abstractmethod
    def upsert_limit(self, month_id: int, user_id: int, amount: Decimal) -> GreyZoneLimit: ...

    @abstractmethod
    def list_entries(self, month_id: int) -> list[GreyZoneEntry]:
        """Money taken this month, newest first."""
        ...

    @abstractmethod
    def get_entry(self, entry_id: int) -> GreyZoneEntry | None: ...

    @abstractmethod
    def create_entry(self, month_id: int, user_id: int, amount: Decimal, taken_date: date) -> GreyZoneEntry: ...

    @abstractmethod
    def delete_entry(self, entry_id: int) -> None: ...

    @abstractmethod
    def sum_taken_by_user(self, month_id: int) -> dict[int, Decimal]: ...


class SavingsRepository(ABC):
    @abstractmethod
    def list_pots(self, include_archived: bool) -> list[SavingsPot]: ...

    @abstractmethod
    def get_pot(self, pot_id: int) -> SavingsPot | None: ...

    @abstractmethod
    def create_pot(
        self,
        name: str,
        kind: SavingsPotKind,
        target_amount: Decimal | None,
        target_date: date | None,
    ) -> SavingsPot: ...

    @abstractmethod
    def update_pot(
        self,
        pot_id: int,
        name: str,
        target_amount: Decimal | None,
        target_date: date | None,
        is_archived: bool,
    ) -> SavingsPot:
        """Replaces all editable fields at once (PUT semantics), so None clears a target."""
        ...

    @abstractmethod
    def delete_pot(self, pot_id: int) -> None: ...

    @abstractmethod
    def has_transfers(self, pot_id: int) -> bool: ...

    @abstractmethod
    def list_transfers(self, pot_id: int) -> list[SavingsTransfer]:
        """Newest first."""
        ...

    @abstractmethod
    def get_transfer(self, transfer_id: int) -> SavingsTransfer | None: ...

    @abstractmethod
    def create_transfer(
        self,
        pot_id: int,
        direction: SavingsTransferDirection,
        amount: Decimal,
        transfer_date: date,
        note: str | None,
        created_by_user_id: int,
    ) -> SavingsTransfer: ...

    @abstractmethod
    def delete_transfer(self, transfer_id: int) -> None: ...

    @abstractmethod
    def sum_budget_flows_between(self, start: date, end: date) -> tuple[Decimal, Decimal]:
        """(moved into pots, moved back out) for transfers dated start..end inclusive. Interest is ignored."""
        ...


class ReconciliationRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Reconciliation]:
        """Newest first."""
        ...

    @abstractmethod
    def get_latest(self) -> Reconciliation | None: ...

    @abstractmethod
    def get_by_id(self, reconciliation_id: int) -> Reconciliation | None: ...

    @abstractmethod
    def create(
        self,
        balance_date: date,
        actual_balance: Decimal,
        expected_balance: Decimal | None,
        difference: Decimal,
        note: str | None,
        created_by_user_id: int,
    ) -> Reconciliation: ...

    @abstractmethod
    def delete(self, reconciliation_id: int) -> None: ...

    @abstractmethod
    def sum_difference_between(self, start: date, end: date) -> Decimal: ...


class LedgerRepository(ABC):
    """Read-only view over every movement of the shared money, across all tables."""

    @abstractmethod
    def flows_after(self, after_date: date, after_created_at: datetime, until_date: date) -> CashFlows:
        """Movements recorded after a reconciliation and dated no later than `until_date`.

        A movement counts as "after" when its date is later than `after_date`, or it is
        dated the same day but was entered after `after_created_at` — so something entered
        later for the day of a reconciliation is not treated as already counted in it.
        """
        ...
