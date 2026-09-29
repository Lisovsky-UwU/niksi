from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError
from app.domain.models import Income, IncomeEntry
from app.interfaces.repositories import IncomeRepository, MonthRepository, UserRepository


class GetIncomeForMonthUseCase:
    """Expected income per person. Actual income comes from the entries."""

    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, month_id: int) -> list[Income]:
        return self._income_repo.list_by_month(month_id)


class SetMyIncomeUseCase:
    def __init__(self, income_repo: IncomeRepository, month_repo: MonthRepository) -> None:
        self._income_repo = income_repo
        self._month_repo = month_repo

    def execute(self, month_id: int, user_id: int, forecast_amount: Decimal) -> Income:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        return self._income_repo.upsert(month_id, user_id, forecast_amount)


class ListIncomeEntriesUseCase:
    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, month_id: int) -> list[IncomeEntry]:
        return self._income_repo.list_entries(month_id)


class AddIncomeEntryUseCase:
    def __init__(self, income_repo: IncomeRepository, month_repo: MonthRepository, user_repo: UserRepository) -> None:
        self._income_repo = income_repo
        self._month_repo = month_repo
        self._user_repo = user_repo

    def execute(
        self,
        month_id: int,
        user_id: int,
        amount: Decimal,
        description: str | None,
        received_date: date,
        created_by_user_id: int,
    ) -> IncomeEntry:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        if self._user_repo.get_by_id(user_id) is None:
            raise NotFoundError(f"User {user_id} not found")
        return self._income_repo.create_entry(
            month_id, user_id, amount, description, received_date, created_by_user_id
        )


class DeleteIncomeEntryUseCase:
    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, entry_id: int) -> None:
        if self._income_repo.get_entry(entry_id) is None:
            raise NotFoundError(f"Income entry {entry_id} not found")
        self._income_repo.delete_entry(entry_id)
