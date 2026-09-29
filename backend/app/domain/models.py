"""Domain entities and aggregates, shared by every entry point (web API today, Telegram bot later).

These are plain Pydantic v2 models with no dependency on SQLAlchemy, FastAPI, or any
other framework. `infrastructure/repositories` are responsible for converting to/from
ORM rows; `api/routes` may return these directly as HTTP response bodies since Pydantic
models already know how to serialize themselves.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Public-safe user identity. Never carries the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str


class UserCredentials(BaseModel):
    """Internal-only shape used exclusively by auth use cases. Never returned over HTTP."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    password_hash: str


class Month(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    # Set by hand for the first month or to correct the chain; otherwise the previous month's closing is used.
    carryover_override: Decimal | None = None


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    name: str
    limit_amount: Decimal
    position: int = 0


class Expense(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    amount: Decimal
    description: str | None = None
    expense_date: date
    created_by_user_id: int


class Income(BaseModel):
    """A person's expected income for a month. What actually arrived is the sum of their IncomeEntry rows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    user_id: int
    forecast_amount: Decimal


class IncomeEntry(BaseModel):
    """One actual receipt of money, e.g. "Аванс 40000"."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    user_id: int
    amount: Decimal
    description: str | None = None
    received_date: date
    created_by_user_id: int


class GreyZoneLimit(BaseModel):
    """How much a person may take out of the shared budget for themselves this month."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    user_id: int
    amount: Decimal


class GreyZoneEntry(BaseModel):
    """Money a person took for themselves. What they spent it on is deliberately not tracked."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    user_id: int
    amount: Decimal
    taken_date: date


class GreyZoneMonth(BaseModel):
    limits: list[GreyZoneLimit]
    entries: list[GreyZoneEntry]


SavingsPotKind = Literal["account", "deposit", "goal"]
# in: moved from the shared budget into the pot; out: back into the budget;
# interest: the pot grew on its own (bank interest), the budget is not touched.
SavingsTransferDirection = Literal["in", "out", "interest"]


class SavingsPot(BaseModel):
    """A savings account, a deposit or a goal ("new wardrobe"). Balance is the sum of its transfers."""

    id: int
    name: str
    kind: SavingsPotKind
    target_amount: Decimal | None = None
    target_date: date | None = None
    is_archived: bool = False
    balance: Decimal


class SavingsTransfer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pot_id: int
    direction: SavingsTransferDirection
    amount: Decimal
    transfer_date: date
    note: str | None = None
    created_by_user_id: int


class Reconciliation(BaseModel):
    """A check of how much money is really on hand against what the records say.

    `expected_balance` is None for the very first reconciliation, which only sets the
    starting point. `difference` = actual - expected: positive means more money than
    recorded, negative means something was spent and not written down.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    balance_date: date
    actual_balance: Decimal
    expected_balance: Decimal | None = None
    difference: Decimal
    note: str | None = None
    created_by_user_id: int
    created_at: datetime


class CashFlows(BaseModel):
    """Movements of the shared money over some period, all as positive amounts."""

    income: Decimal = Decimal(0)
    expenses: Decimal = Decimal(0)
    grey_zone: Decimal = Decimal(0)
    savings_in: Decimal = Decimal(0)
    savings_out: Decimal = Decimal(0)

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses - self.grey_zone - self.savings_in + self.savings_out


class BalanceStatus(BaseModel):
    """What the shared money should look like right now, according to the records."""

    last_reconciliation: Reconciliation | None
    expected_now: Decimal | None
    flows_since: CashFlows


class CategorySummary(BaseModel):
    id: int
    name: str
    limit_amount: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: float


class UserIncomeSummary(BaseModel):
    user_id: int
    display_name: str
    forecast: Decimal
    actual: Decimal


class GreyZoneUserSummary(BaseModel):
    user_id: int
    display_name: str
    limit: Decimal
    taken: Decimal
    remaining: Decimal


class GreyZoneSummary(BaseModel):
    per_user: list[GreyZoneUserSummary]
    total_limit: Decimal
    total_taken: Decimal


class MonthTotals(BaseModel):
    total_limit: Decimal
    total_spent: Decimal


class IncomeSummary(BaseModel):
    per_user: list[UserIncomeSummary]
    household_forecast: Decimal
    household_actual: Decimal


class BalanceSummary(BaseModel):
    """Where the month's money went: net = income - spent - grey zone - savings + adjustments.

    `adjustments` are reconciliation differences dated within the month.
    """

    income_actual: Decimal
    total_spent: Decimal
    grey_zone_taken: Decimal
    savings_net: Decimal
    adjustments: Decimal
    net: Decimal


class CarryoverSummary(BaseModel):
    """What was left over from the previous month and what this month passes on."""

    carried_over: Decimal
    is_manual: bool
    closing: Decimal


class MonthSummary(BaseModel):
    month: Month
    categories: list[CategorySummary]
    totals: MonthTotals
    income: IncomeSummary
    grey_zone: GreyZoneSummary
    balance: BalanceSummary
    carryover: CarryoverSummary
