from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import Month
from app.domain.periods import allowed_start_range, default_start
from app.interfaces.repositories import GreyZoneRepository, IncomeRepository, MonthRepository
from app.use_cases.categories import CopyCategoriesFromPreviousMonthUseCase


def _check_start(month_repo: MonthRepository, year: int, month: int, start: date) -> None:
    """A month may start from the 1st of the previous calendar month to the end of its own,
    and months must stay in order: each starts after the previous one and before the next."""
    earliest, latest = allowed_start_range(year, month)
    if not earliest <= start <= latest:
        raise ValidationError(f"The month can start between {earliest} and {latest}")
    previous = month_repo.get_previous(year, month)
    if previous is not None and start <= previous.start_date:
        raise ValidationError(f"The month must start after the previous one ({previous.start_date})")
    following = month_repo.get_next(year, month)
    if following is not None and start >= following.start_date:
        raise ValidationError(f"The month must start before the next one ({following.start_date})")


class ListMonthsUseCase:
    def __init__(self, month_repo: MonthRepository) -> None:
        self._month_repo = month_repo

    def execute(self) -> list[Month]:
        return self._month_repo.list_all()


class GetMonthUseCase:
    def __init__(self, month_repo: MonthRepository) -> None:
        self._month_repo = month_repo

    def execute(self, year: int, month: int) -> Month:
        found = self._month_repo.get_by_year_month(year, month)
        if found is None:
            raise NotFoundError(f"Month {year}-{month:02d} not found")
        return found


class CopyPlansFromPreviousMonthUseCase:
    """Carries over what usually stays the same month to month: each person's expected
    income and grey zone limit. Actual receipts and withdrawals are never copied."""

    def __init__(
        self,
        month_repo: MonthRepository,
        income_repo: IncomeRepository,
        grey_zone_repo: GreyZoneRepository,
    ) -> None:
        self._month_repo = month_repo
        self._income_repo = income_repo
        self._grey_zone_repo = grey_zone_repo

    def execute(self, target_month_id: int) -> None:
        target = self._month_repo.get_by_id(target_month_id)
        if target is None:
            raise NotFoundError(f"Month {target_month_id} not found")
        previous = self._month_repo.get_previous(target.year, target.month)
        if previous is None:
            return
        for income in self._income_repo.list_by_month(previous.id):
            self._income_repo.upsert(target_month_id, income.user_id, income.forecast_amount)
        for limit in self._grey_zone_repo.list_limits(previous.id):
            self._grey_zone_repo.upsert_limit(target_month_id, limit.user_id, limit.amount)


class CreateMonthUseCase:
    def __init__(
        self,
        month_repo: MonthRepository,
        copy_categories_use_case: CopyCategoriesFromPreviousMonthUseCase,
        copy_plans_use_case: CopyPlansFromPreviousMonthUseCase,
    ) -> None:
        self._month_repo = month_repo
        self._copy_categories_use_case = copy_categories_use_case
        self._copy_plans_use_case = copy_plans_use_case

    def execute(
        self,
        year: int,
        month: int,
        copy_categories_from_previous: bool,
        start_date: date | None = None,
    ) -> Month:
        if self._month_repo.get_by_year_month(year, month) is not None:
            raise ValidationError(f"Month {year}-{month:02d} already exists")
        start = start_date or default_start(year, month)
        _check_start(self._month_repo, year, month, start)
        new_month = self._month_repo.create(year, month, start)
        if copy_categories_from_previous:
            self._copy_categories_use_case.execute(new_month.id)
            self._copy_plans_use_case.execute(new_month.id)
        return new_month


class SetMonthStartUseCase:
    """Moves the day a month's period starts, e.g. to the day the salary actually came."""

    def __init__(self, month_repo: MonthRepository) -> None:
        self._month_repo = month_repo

    def execute(self, month_id: int, start_date: date) -> Month:
        month = self._month_repo.get_by_id(month_id)
        if month is None:
            raise NotFoundError(f"Month {month_id} not found")
        _check_start(self._month_repo, month.year, month.month, start_date)
        return self._month_repo.set_start_date(month_id, start_date)


class SetCarryoverUseCase:
    """None goes back to carrying over the previous month's closing balance automatically."""

    def __init__(self, month_repo: MonthRepository) -> None:
        self._month_repo = month_repo

    def execute(self, month_id: int, amount: Decimal | None) -> Month:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        return self._month_repo.set_carryover_override(month_id, amount)
