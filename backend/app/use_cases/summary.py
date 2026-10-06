from datetime import date
from decimal import Decimal

from app.domain.exceptions import NotFoundError
from app.domain.models import (
    BalanceSummary,
    CarryoverSummary,
    CategorySummary,
    GreyZoneSummary,
    GreyZoneUserSummary,
    IncomeSummary,
    Month,
    MonthSummary,
    MonthTotals,
    UserIncomeSummary,
)
from app.interfaces.repositories import (
    CategoryRepository,
    ExpenseRepository,
    GreyZoneRepository,
    IncomeRepository,
    LoanRepository,
    MonthRepository,
    ReconciliationRepository,
    SavingsRepository,
    UserRepository,
)


def _month_bounds(month: Month) -> tuple[date, date]:
    """The budget period, not the calendar month. The latest month is open-ended, so
    anything dated after its start (savings moves, reconciliations) belongs to it."""
    return month.start_date, month.end_date or date.max


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
        grey_zone_repo: GreyZoneRepository,
        savings_repo: SavingsRepository,
        reconciliation_repo: ReconciliationRepository,
        loan_repo: LoanRepository,
    ) -> None:
        self._month_repo = month_repo
        self._category_repo = category_repo
        self._expense_repo = expense_repo
        self._income_repo = income_repo
        self._user_repo = user_repo
        self._grey_zone_repo = grey_zone_repo
        self._savings_repo = savings_repo
        self._reconciliation_repo = reconciliation_repo
        self._loan_repo = loan_repo

    def _balance(self, month: Month) -> BalanceSummary:
        start, end = _month_bounds(month)
        income = sum(self._income_repo.sum_entries_by_user(month.id).values(), Decimal(0))
        spent = sum(self._expense_repo.sum_by_category_for_month(month.id).values(), Decimal(0))
        grey_zone = sum(self._grey_zone_repo.sum_taken_by_user(month.id).values(), Decimal(0))
        saved_in, saved_out = self._savings_repo.sum_budget_flows_between(start, end)
        savings_net = saved_in - saved_out
        loan_payments = self._loan_repo.sum_budget_payments_between(start, end)
        adjustments = self._reconciliation_repo.sum_difference_between(start, end)
        return BalanceSummary(
            income_actual=income,
            total_spent=spent,
            grey_zone_taken=grey_zone,
            savings_net=savings_net,
            loan_payments=loan_payments,
            adjustments=adjustments,
            net=income - spent - grey_zone - savings_net - loan_payments + adjustments,
        )

    def _carried_over(self, month: Month) -> Decimal:
        """Walks the months in order: each one starts with the previous closing balance,
        unless a carry-over was set by hand."""
        if month.carryover_override is not None:
            return month.carryover_override
        earlier = [
            m for m in reversed(self._month_repo.list_all()) if (m.year, m.month) < (month.year, month.month)
        ]
        closing = Decimal(0)
        for m in earlier:
            carried = m.carryover_override if m.carryover_override is not None else closing
            closing = carried + self._balance(m).net
        return closing

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

        # Every person always appears, even before they entered anything for the month.
        users = self._user_repo.list_all()
        forecasts = {income.user_id: income.forecast_amount for income in self._income_repo.list_by_month(month_id)}
        received = self._income_repo.sum_entries_by_user(month_id)
        per_user_income = [
            UserIncomeSummary(
                user_id=user.id,
                display_name=user.display_name,
                forecast=forecasts.get(user.id, Decimal(0)),
                actual=received.get(user.id, Decimal(0)),
            )
            for user in users
        ]

        limits = {limit.user_id: limit.amount for limit in self._grey_zone_repo.list_limits(month_id)}
        taken = self._grey_zone_repo.sum_taken_by_user(month_id)
        per_user_grey = [
            GreyZoneUserSummary(
                user_id=user.id,
                display_name=user.display_name,
                limit=limits.get(user.id, Decimal(0)),
                taken=taken.get(user.id, Decimal(0)),
                remaining=limits.get(user.id, Decimal(0)) - taken.get(user.id, Decimal(0)),
            )
            for user in users
        ]

        balance = self._balance(month)
        carried_over = self._carried_over(month)

        return MonthSummary(
            month=month,
            categories=category_summaries,
            totals=MonthTotals(total_limit=total_limit, total_spent=total_spent),
            income=IncomeSummary(
                per_user=per_user_income,
                household_forecast=sum((u.forecast for u in per_user_income), Decimal(0)),
                household_actual=sum((u.actual for u in per_user_income), Decimal(0)),
            ),
            grey_zone=GreyZoneSummary(
                per_user=per_user_grey,
                total_limit=sum((u.limit for u in per_user_grey), Decimal(0)),
                total_taken=sum((u.taken for u in per_user_grey), Decimal(0)),
            ),
            balance=balance,
            carryover=CarryoverSummary(
                carried_over=carried_over,
                is_manual=month.carryover_override is not None,
                closing=carried_over + balance.net,
            ),
        )
