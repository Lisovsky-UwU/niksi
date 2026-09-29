from decimal import Decimal

from app.domain.exceptions import NotFoundError
from app.domain.models import Category
from app.interfaces.repositories import CategoryRepository, MonthRepository


class ListCategoriesUseCase:
    def __init__(self, category_repo: CategoryRepository) -> None:
        self._category_repo = category_repo

    def execute(self, month_id: int) -> list[Category]:
        return self._category_repo.list_by_month(month_id)


class CreateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository, month_repo: MonthRepository) -> None:
        self._category_repo = category_repo
        self._month_repo = month_repo

    def execute(self, month_id: int, name: str, limit_amount: Decimal) -> Category:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        position = len(self._category_repo.list_by_month(month_id))
        return self._category_repo.create(month_id, name, limit_amount, position)


class UpdateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository) -> None:
        self._category_repo = category_repo

    def execute(
        self,
        category_id: int,
        name: str | None,
        limit_amount: Decimal | None,
        position: int | None,
    ) -> Category:
        if self._category_repo.get_by_id(category_id) is None:
            raise NotFoundError(f"Category {category_id} not found")
        return self._category_repo.update(category_id, name, limit_amount, position)


class DeleteCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository) -> None:
        self._category_repo = category_repo

    def execute(self, category_id: int) -> None:
        if self._category_repo.get_by_id(category_id) is None:
            raise NotFoundError(f"Category {category_id} not found")
        self._category_repo.delete(category_id)


class CopyCategoriesFromPreviousMonthUseCase:
    """One-shot convenience copy — creates independent new Category rows, never links them."""

    def __init__(self, month_repo: MonthRepository, category_repo: CategoryRepository) -> None:
        self._month_repo = month_repo
        self._category_repo = category_repo

    def execute(self, target_month_id: int) -> list[Category]:
        target = self._month_repo.get_by_id(target_month_id)
        if target is None:
            raise NotFoundError(f"Month {target_month_id} not found")
        previous = self._month_repo.get_previous(target.year, target.month)
        if previous is None:
            return []
        source_categories = self._category_repo.list_by_month(previous.id)
        return [
            self._category_repo.create(target_month_id, category.name, category.limit_amount, category.position)
            for category in source_categories
        ]
