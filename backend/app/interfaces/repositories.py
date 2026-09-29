"""Abstract repository contracts. Use cases depend only on these, never on SQLAlchemy.

Concrete implementations live in `infrastructure/repositories/`. Any future storage
backend (or a fake/in-memory implementation for tests) just needs to satisfy these
interfaces.
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from app.domain.models import Category, Expense, Income, Month, User, UserCredentials


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...

    @abstractmethod
    def get_credentials_by_email(self, email: str) -> UserCredentials | None: ...

    @abstractmethod
    def create(self, email: str, password_hash: str, display_name: str) -> User: ...


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
    def list_all(self) -> list[Month]:
        """All months, sorted newest first."""
        ...

    @abstractmethod
    def create(self, year: int, month: int) -> Month: ...


class CategoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, category_id: int) -> Category | None: ...

    @abstractmethod
    def list_by_month(self, month_id: int) -> list[Category]:
        """Categories for a month, ordered by position."""
        ...

    @abstractmethod
    def create(self, month_id: int, name: str, limit_amount: Decimal, position: int) -> Category: ...

    @abstractmethod
    def update(
        self,
        category_id: int,
        name: str | None,
        limit_amount: Decimal | None,
        position: int | None,
    ) -> Category: ...

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
    ) -> Expense: ...

    @abstractmethod
    def update(
        self,
        expense_id: int,
        amount: Decimal | None,
        description: str | None,
        expense_date: date | None,
    ) -> Expense: ...

    @abstractmethod
    def delete(self, expense_id: int) -> None: ...


class IncomeRepository(ABC):
    @abstractmethod
    def list_by_month(self, month_id: int) -> list[Income]: ...

    @abstractmethod
    def get(self, month_id: int, user_id: int) -> Income | None: ...

    @abstractmethod
    def upsert(
        self,
        month_id: int,
        user_id: int,
        forecast_amount: Decimal,
        actual_amount: Decimal,
    ) -> Income: ...
