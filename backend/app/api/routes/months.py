from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_create_month_use_case,
    get_current_user,
    get_get_month_use_case,
    get_list_months_use_case,
    get_set_carryover_use_case,
    get_set_month_start_use_case,
)
from app.api.schemas import CarryoverRequest, MonthCreateRequest, MonthStartRequest
from app.domain.models import Month, User
from app.use_cases.months import (
    CreateMonthUseCase,
    GetMonthUseCase,
    ListMonthsUseCase,
    SetCarryoverUseCase,
    SetMonthStartUseCase,
)

router = APIRouter(prefix="/months", tags=["months"])


@router.get("", response_model=list[Month])
def list_months(
    use_case: ListMonthsUseCase = Depends(get_list_months_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Month]:
    return use_case.execute()


@router.post("", response_model=Month, status_code=status.HTTP_201_CREATED)
def create_month(
    payload: MonthCreateRequest,
    use_case: CreateMonthUseCase = Depends(get_create_month_use_case),
    _current_user: User = Depends(get_current_user),
) -> Month:
    return use_case.execute(
        payload.year, payload.month, payload.copy_categories_from_previous, payload.start_date
    )


@router.get("/{year}/{month}", response_model=Month)
def get_month(
    year: int,
    month: int,
    use_case: GetMonthUseCase = Depends(get_get_month_use_case),
    _current_user: User = Depends(get_current_user),
) -> Month:
    return use_case.execute(year, month)


@router.put("/{month_id}/carryover", response_model=Month)
def set_carryover(
    month_id: int,
    payload: CarryoverRequest,
    use_case: SetCarryoverUseCase = Depends(get_set_carryover_use_case),
    _current_user: User = Depends(get_current_user),
) -> Month:
    return use_case.execute(month_id, payload.amount)


@router.put("/{month_id}/start", response_model=Month)
def set_month_start(
    month_id: int,
    payload: MonthStartRequest,
    use_case: SetMonthStartUseCase = Depends(get_set_month_start_use_case),
    _current_user: User = Depends(get_current_user),
) -> Month:
    return use_case.execute(month_id, payload.start_date)
