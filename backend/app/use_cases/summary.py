from decimal import Decimal

from app.domain.exceptions import NotFoundError
from app.domain.models import (
    BalanceSummary,
    CategorySummary,
    IncomeSummary,
    MonthSummary,
    MonthTotals,
    UserIncomeSummary,
)
from app.interfaces.repositories import (
    CategoryRepository,
    ExpenseRepository,
    IncomeRepository,
    MonthRepository,
    UserRepository,
)


class GetMonthSummaryUseCase:
    """Computes the single aggregated payload the dashboard needs.

    Aggregation (spent-per-category totals) happens via the repository layer
    (SQL SUM/GROUP BY), never by pulling every expense row into Python.
    """

    def __init__(
        self,
        month_repo: MonthRepository,
        category_repo: CategoryRepository,
        expense_repo: ExpenseRepository,
        income_repo: IncomeRepository,
        user_repo: UserRepository,
    ) -> None:
        self._month_repo = month_repo
        self._category_repo = category_repo
        self._expense_repo = expense_repo
        self._income_repo = income_repo
        self._user_repo = user_repo

    def execute(self, month_id: int) -> MonthSummary:
        month = self._month_repo.get_by_id(month_id)
        if month is None:
            raise NotFoundError(f"Month {month_id} not found")

        categories = self._category_repo.list_by_month(month_id)
        spent_by_category = self._expense_repo.sum_by_category_for_month(month_id)

        category_summaries: list[CategorySummary] = []
        total_limit = Decimal(0)
        total_spent = Decimal(0)
        for category in categories:
            spent = spent_by_category.get(category.id, Decimal(0))
            remaining = category.limit_amount - spent
            percent_used = float(spent / category.limit_amount * 100) if category.limit_amount else 0.0
            category_summaries.append(
                CategorySummary(
                    id=category.id,
                    name=category.name,
                    limit_amount=category.limit_amount,
                    spent=spent,
                    remaining=remaining,
                    percent_used=round(percent_used, 1),
                )
            )
            total_limit += category.limit_amount
            total_spent += spent

        incomes = self._income_repo.list_by_month(month_id)
        users_by_id = {user.id: user for user in self._user_repo.list_all()}
        per_user = [
            UserIncomeSummary(
                user_id=income.user_id,
                display_name=users_by_id[income.user_id].display_name,
                forecast=income.forecast_amount,
                actual=income.actual_amount,
            )
            for income in incomes
            if income.user_id in users_by_id
        ]
        household_forecast = sum((income.forecast_amount for income in incomes), Decimal(0))
        household_actual = sum((income.actual_amount for income in incomes), Decimal(0))

        return MonthSummary(
            month=month,
            categories=category_summaries,
            totals=MonthTotals(total_limit=total_limit, total_spent=total_spent),
            income=IncomeSummary(
                per_user=per_user,
                household_forecast=household_forecast,
                household_actual=household_actual,
            ),
            balance=BalanceSummary(
                income_actual=household_actual,
                total_spent=total_spent,
                net=household_actual - total_spent,
            ),
        )
