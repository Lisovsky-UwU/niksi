from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_month_summary_use_case
from app.domain.models import MonthSummary, User
from app.use_cases.summary import GetMonthSummaryUseCase

router = APIRouter(prefix="/months", tags=["summary"])


@router.get("/{month_id}/summary", response_model=MonthSummary)
def get_month_summary(
    month_id: int,
    use_case: GetMonthSummaryUseCase = Depends(get_month_summary_use_case),
    _current_user: User = Depends(get_current_user),
) -> MonthSummary:
    return use_case.execute(month_id)
