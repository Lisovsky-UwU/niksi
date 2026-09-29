from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_current_user,
    get_delete_grey_zone_entry_use_case,
    get_grey_zone_for_month_use_case,
    get_set_my_grey_zone_limit_use_case,
    get_take_from_grey_zone_use_case,
)
from app.api.schemas import GreyZoneLimitRequest, GreyZoneTakeRequest
from app.domain.models import GreyZoneEntry, GreyZoneLimit, GreyZoneMonth, User
from app.use_cases.grey_zone import (
    DeleteGreyZoneEntryUseCase,
    GetGreyZoneForMonthUseCase,
    SetMyGreyZoneLimitUseCase,
    TakeFromGreyZoneUseCase,
)

router = APIRouter(prefix="/months/{month_id}/grey-zone", tags=["grey-zone"])
entries_router = APIRouter(prefix="/grey-zone/entries", tags=["grey-zone"])


@router.get("", response_model=GreyZoneMonth)
def get_grey_zone(
    month_id: int,
    use_case: GetGreyZoneForMonthUseCase = Depends(get_grey_zone_for_month_use_case),
    _current_user: User = Depends(get_current_user),
) -> GreyZoneMonth:
    return use_case.execute(month_id)


@router.put("/me", response_model=GreyZoneLimit)
def set_my_grey_zone_limit(
    month_id: int,
    payload: GreyZoneLimitRequest,
    use_case: SetMyGreyZoneLimitUseCase = Depends(get_set_my_grey_zone_limit_use_case),
    current_user: User = Depends(get_current_user),
) -> GreyZoneLimit:
    return use_case.execute(month_id, current_user.id, payload.amount)


@router.post("/entries", response_model=GreyZoneEntry, status_code=status.HTTP_201_CREATED)
def take_from_grey_zone(
    month_id: int,
    payload: GreyZoneTakeRequest,
    use_case: TakeFromGreyZoneUseCase = Depends(get_take_from_grey_zone_use_case),
    current_user: User = Depends(get_current_user),
) -> GreyZoneEntry:
    return use_case.execute(month_id, current_user.id, payload.amount, payload.taken_date)


@entries_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grey_zone_entry(
    entry_id: int,
    use_case: DeleteGreyZoneEntryUseCase = Depends(get_delete_grey_zone_entry_use_case),
    current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(entry_id, current_user.id)
