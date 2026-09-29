from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import Month
from app.interfaces.repositories import MonthRepository
from app.use_cases.categories import CopyCategoriesFromPreviousMonthUseCase


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


class CreateMonthUseCase:
    def __init__(
        self,
        month_repo: MonthRepository,
        copy_categories_use_case: CopyCategoriesFromPreviousMonthUseCase,
    ) -> None:
        self._month_repo = month_repo
        self._copy_categories_use_case = copy_categories_use_case

    def execute(self, year: int, month: int, copy_categories_from_previous: bool) -> Month:
        if self._month_repo.get_by_year_month(year, month) is not None:
            raise ValidationError(f"Month {year}-{month:02d} already exists")
        new_month = self._month_repo.create(year, month)
        if copy_categories_from_previous:
            self._copy_categories_use_case.execute(new_month.id)
        return new_month
