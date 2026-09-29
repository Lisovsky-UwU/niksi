from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_add_income_entry_use_case,
    get_current_user,
    get_delete_income_entry_use_case,
    get_income_for_month_use_case,
    get_list_income_entries_use_case,
    get_set_my_income_use_case,
)
from app.api.schemas import IncomeEntryCreateRequest, IncomeSetRequest
from app.domain.models import Income, IncomeEntry, User
from app.use_cases.income import (
    AddIncomeEntryUseCase,
    DeleteIncomeEntryUseCase,
    GetIncomeForMonthUseCase,
    ListIncomeEntriesUseCase,
    SetMyIncomeUseCase,
)

router = APIRouter(prefix="/months/{month_id}/income", tags=["income"])
entries_router = APIRouter(prefix="/income-entries", tags=["income"])


@router.get("", response_model=list[Income])
def get_income_for_month(
    month_id: int,
    use_case: GetIncomeForMonthUseCase = Depends(get_income_for_month_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Income]:
    return use_case.execute(month_id)


@router.put("/me", response_model=Income)
def set_my_income(
    month_id: int,
    payload: IncomeSetRequest,
    use_case: SetMyIncomeUseCase = Depends(get_set_my_income_use_case),
    current_user: User = Depends(get_current_user),
) -> Income:
    return use_case.execute(month_id, current_user.id, payload.forecast_amount)


@router.get("/entries", response_model=list[IncomeEntry])
def list_income_entries(
    month_id: int,
    use_case: ListIncomeEntriesUseCase = Depends(get_list_income_entries_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[IncomeEntry]:
    return use_case.execute(month_id)


@router.post("/entries", response_model=IncomeEntry, status_code=status.HTTP_201_CREATED)
def add_income_entry(
    month_id: int,
    payload: IncomeEntryCreateRequest,
    use_case: AddIncomeEntryUseCase = Depends(get_add_income_entry_use_case),
    current_user: User = Depends(get_current_user),
) -> IncomeEntry:
    return use_case.execute(
        month_id,
        payload.user_id if payload.user_id is not None else current_user.id,
        payload.amount,
        payload.description,
        payload.received_date,
        current_user.id,
    )


@entries_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income_entry(
    entry_id: int,
    use_case: DeleteIncomeEntryUseCase = Depends(get_delete_income_entry_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(entry_id)
