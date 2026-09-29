from decimal import Decimal

from app.domain.models import Income
from app.interfaces.repositories import IncomeRepository


class GetIncomeForMonthUseCase:
    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, month_id: int) -> list[Income]:
        return self._income_repo.list_by_month(month_id)


class SetMyIncomeUseCase:
    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, month_id: int, user_id: int, forecast_amount: Decimal, actual_amount: Decimal) -> Income:
        return self._income_repo.upsert(month_id, user_id, forecast_amount, actual_amount)
