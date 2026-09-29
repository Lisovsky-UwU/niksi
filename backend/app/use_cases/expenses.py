from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError
from app.domain.models import Expense
from app.interfaces.repositories import CategoryRepository, ExpenseRepository


class ListExpensesUseCase:
    def __init__(self, expense_repo: ExpenseRepository) -> None:
        self._expense_repo = expense_repo

    def execute(self, month_id: int | None = None, category_id: int | None = None) -> list[Expense]:
        return self._expense_repo.list_filtered(month_id, category_id)


class AddExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository, category_repo: CategoryRepository) -> None:
        self._expense_repo = expense_repo
        self._category_repo = category_repo

    def execute(
        self,
        category_id: int,
        amount: Decimal,
        description: str | None,
        expense_date: date,
        created_by_user_id: int,
    ) -> Expense:
        if self._category_repo.get_by_id(category_id) is None:
            raise NotFoundError(f"Category {category_id} not found")
        return self._expense_repo.create(category_id, amount, description, expense_date, created_by_user_id)


class UpdateExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository) -> None:
        self._expense_repo = expense_repo

    def execute(
        self,
        expense_id: int,
        amount: Decimal | None,
        description: str | None,
        expense_date: date | None,
    ) -> Expense:
        if self._expense_repo.get_by_id(expense_id) is None:
            raise NotFoundError(f"Expense {expense_id} not found")
        return self._expense_repo.update(expense_id, amount, description, expense_date)


class DeleteExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository) -> None:
        self._expense_repo = expense_repo

    def execute(self, expense_id: int) -> None:
        if self._expense_repo.get_by_id(expense_id) is None:
            raise NotFoundError(f"Expense {expense_id} not found")
        self._expense_repo.delete(expense_id)
