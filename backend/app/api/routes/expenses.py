from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import (
    get_add_expense_use_case,
    get_current_user,
    get_delete_expense_use_case,
    get_list_expenses_use_case,
    get_notification_service,
    get_update_expense_use_case,
    get_web_expense_notification_use_case,
)
from app.api.schemas import ExpenseCreateRequest, ExpenseUpdateRequest
from app.domain.models import Expense, User
from app.interfaces.services import NotificationService
from app.use_cases.expenses import AddExpenseUseCase, DeleteExpenseUseCase, ListExpensesUseCase, UpdateExpenseUseCase
from app.use_cases.telegram import WebExpenseNotificationUseCase

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
    background_tasks: BackgroundTasks,
    use_case: AddExpenseUseCase = Depends(get_add_expense_use_case),
    notification: WebExpenseNotificationUseCase = Depends(get_web_expense_notification_use_case),
    notifier: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
) -> Expense:
    expense = use_case.execute(
        payload.category_id,
        payload.amount,
        payload.description,
        payload.expense_date,
        current_user.id,
        payload.spent_by_user_id,
    )
    # The message is built now (the database session is still open); only sending it to
    # Telegram happens after the response, so a slow network never delays the app.
    message = notification.execute(expense)
    if message is not None:
        background_tasks.add_task(notifier.send, *message)
    return expense


@router.put("/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdateRequest,
    use_case: UpdateExpenseUseCase = Depends(get_update_expense_use_case),
    _current_user: User = Depends(get_current_user),
) -> Expense:
    return use_case.execute(
        expense_id,
        payload.amount,
        payload.description,
        payload.expense_date,
        payload.category_id,
        set_description="description" in payload.model_fields_set,
        spent_by_user_id=payload.spent_by_user_id,
    )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    use_case: DeleteExpenseUseCase = Depends(get_delete_expense_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(expense_id)
