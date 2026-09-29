from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_add_expense_use_case,
    get_current_user,
    get_delete_expense_use_case,
    get_list_expenses_use_case,
    get_update_expense_use_case,
)
from app.api.schemas import ExpenseCreateRequest, ExpenseUpdateRequest
from app.domain.models import Expense, User
from app.use_cases.expenses import AddExpenseUseCase, DeleteExpenseUseCase, ListExpensesUseCase, UpdateExpenseUseCase

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[Expense])
def list_expenses(
    month_id: int | None = None,
    category_id: int | None = None,
    use_case: ListExpensesUseCase = Depends(get_list_expenses_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Expense]:
    return use_case.execute(month_id=month_id, category_id=category_id)


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
def add_expense(
    payload: ExpenseCreateRequest,
    use_case: AddExpenseUseCase = Depends(get_add_expense_use_case),
    current_user: User = Depends(get_current_user),
) -> Expense:
    return use_case.execute(
        payload.category_id,
        payload.amount,
        payload.description,
        payload.expense_date,
        current_user.id,
    )


@router.put("/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdateRequest,
    use_case: UpdateExpenseUseCase = Depends(get_update_expense_use_case),
    _current_user: User = Depends(get_current_user),
) -> Expense:
    return use_case.execute(expense_id, payload.amount, payload.description, payload.expense_date)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    use_case: DeleteExpenseUseCase = Depends(get_delete_expense_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(expense_id)
