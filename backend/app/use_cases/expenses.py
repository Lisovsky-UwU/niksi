from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import Expense
from app.interfaces.repositories import CategoryRepository, ExpenseRepository, UserRepository


class ListExpensesUseCase:
    def __init__(self, expense_repo: ExpenseRepository) -> None:
        self._expense_repo = expense_repo

    def execute(self, month_id: int | None = None, category_id: int | None = None) -> list[Expense]:
        return self._expense_repo.list_filtered(month_id, category_id)


class AddExpenseUseCase:
    def __init__(
        self, expense_repo: ExpenseRepository, category_repo: CategoryRepository, user_repo: UserRepository
    ) -> None:
        self._expense_repo = expense_repo
        self._category_repo = category_repo
        self._user_repo = user_repo

    def execute(
        self,
        category_id: int,
        amount: Decimal,
        description: str | None,
        expense_date: date,
        created_by_user_id: int,
        spent_by_user_id: int | None = None,
    ) -> Expense:
        # By default the money was spent by whoever records it.
        if self._category_repo.get_by_id(category_id) is None:
            raise NotFoundError(f"Category {category_id} not found")
        spender = spent_by_user_id if spent_by_user_id is not None else created_by_user_id
        if self._user_repo.get_by_id(spender) is None:
            raise NotFoundError(f"User {spender} not found")
        return self._expense_repo.create(
            category_id, amount, description, expense_date, created_by_user_id, spender
        )


class UpdateExpenseUseCase:
    def __init__(
        self, expense_repo: ExpenseRepository, category_repo: CategoryRepository, user_repo: UserRepository
    ) -> None:
        self._expense_repo = expense_repo
        self._category_repo = category_repo
        self._user_repo = user_repo

    def execute(
        self,
        expense_id: int,
        amount: Decimal | None,
        description: str | None,
        expense_date: date | None,
        category_id: int | None = None,
        set_description: bool = False,
        spent_by_user_id: int | None = None,
    ) -> Expense:
        expense = self._expense_repo.get_by_id(expense_id)
        if expense is None:
            raise NotFoundError(f"Expense {expense_id} not found")
        if category_id is not None and category_id != expense.category_id:
            # An expense can move to another category of the same month, never to another month.
            new_category = self._category_repo.get_by_id(category_id)
            current_category = self._category_repo.get_by_id(expense.category_id)
            if new_category is None:
                raise NotFoundError(f"Category {category_id} not found")
            if current_category is not None and new_category.month_id != current_category.month_id:
                raise ValidationError("An expense can only move to a category of the same month")
        if spent_by_user_id is not None and self._user_repo.get_by_id(spent_by_user_id) is None:
            raise NotFoundError(f"User {spent_by_user_id} not found")
        if set_description and description is not None:
            description = description.strip() or None
        return self._expense_repo.update(
            expense_id, amount, description, expense_date, category_id, set_description, spent_by_user_id
        )


class DeleteExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository) -> None:
        self._expense_repo = expense_repo

    def execute(self, expense_id: int) -> None:
        if self._expense_repo.get_by_id(expense_id) is None:
            raise NotFoundError(f"Expense {expense_id} not found")
        self._expense_repo.delete(expense_id)
