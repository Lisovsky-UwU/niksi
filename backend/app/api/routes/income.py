from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_income_for_month_use_case, get_set_my_income_use_case
from app.api.schemas import IncomeSetRequest
from app.domain.models import Income, User
from app.use_cases.income import GetIncomeForMonthUseCase, SetMyIncomeUseCase

router = APIRouter(prefix="/months/{month_id}/income", tags=["income"])


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
    return use_case.execute(month_id, current_user.id, payload.forecast_amount, payload.actual_amount)
