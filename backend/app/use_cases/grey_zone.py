"""The grey zone: money each partner takes out of the shared budget for themselves.

Both partners see how much each one took; what it was spent on is never recorded.
Each person manages only their own limit and their own withdrawals.
"""

from datetime import date
from decimal import Decimal

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models import GreyZoneEntry, GreyZoneLimit, GreyZoneMonth
from app.interfaces.repositories import GreyZoneRepository, MonthRepository


class GetGreyZoneForMonthUseCase:
    def __init__(self, grey_zone_repo: GreyZoneRepository) -> None:
        self._grey_zone_repo = grey_zone_repo

    def execute(self, month_id: int) -> GreyZoneMonth:
        return GreyZoneMonth(
            limits=self._grey_zone_repo.list_limits(month_id),
            entries=self._grey_zone_repo.list_entries(month_id),
        )


class SetMyGreyZoneLimitUseCase:
    def __init__(self, grey_zone_repo: GreyZoneRepository, month_repo: MonthRepository) -> None:
        self._grey_zone_repo = grey_zone_repo
        self._month_repo = month_repo

    def execute(self, month_id: int, user_id: int, amount: Decimal) -> GreyZoneLimit:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        return self._grey_zone_repo.upsert_limit(month_id, user_id, amount)


class TakeFromGreyZoneUseCase:
    def __init__(self, grey_zone_repo: GreyZoneRepository, month_repo: MonthRepository) -> None:
        self._grey_zone_repo = grey_zone_repo
        self._month_repo = month_repo

    def execute(self, month_id: int, user_id: int, amount: Decimal, taken_date: date) -> GreyZoneEntry:
        if self._month_repo.get_by_id(month_id) is None:
            raise NotFoundError(f"Month {month_id} not found")
        return self._grey_zone_repo.create_entry(month_id, user_id, amount, taken_date)


class DeleteGreyZoneEntryUseCase:
    def __init__(self, grey_zone_repo: GreyZoneRepository) -> None:
        self._grey_zone_repo = grey_zone_repo

    def execute(self, entry_id: int, user_id: int) -> None:
        entry = self._grey_zone_repo.get_entry(entry_id)
        if entry is None:
            raise NotFoundError(f"Grey zone entry {entry_id} not found")
        if entry.user_id != user_id:
            raise ForbiddenError("Only the person who took the money can remove this record")
        self._grey_zone_repo.delete_entry(entry_id)
