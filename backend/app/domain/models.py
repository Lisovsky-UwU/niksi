"""Domain entities and aggregates, shared by every entry point (web API today, Telegram bot later).

These are plain Pydantic v2 models with no dependency on SQLAlchemy, FastAPI, or any
other framework. `infrastructure/repositories` are responsible for converting to/from
ORM rows; `api/routes` may return these directly as HTTP response bodies since Pydantic
models already know how to serialize themselves.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.loans import forecast, months_after, nth_payment_date


class User(BaseModel):
    """Public-safe user identity. Never carries the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    # Bumped on every new avatar so its URL changes and browsers can cache it forever.
    # None when the person has no avatar.
    avatar_version: int | None = None
    # Whether this person can use the Telegram bot; the Telegram id itself is never exposed.
    telegram_linked: bool = False


class Avatar(BaseModel):
    content_type: str
    data: bytes


class TelegramLinkCode(BaseModel):
    """One-time code shown in the web settings and sent to the bot as /link CODE."""

    code: str
    expires_at: datetime
    # Lets the web page offer a t.me link that sends the code by itself; None if not configured.
    bot_username: str | None = None


class TelegramChat(BaseModel):
    """The couple's shared Telegram chat where the bot answers and posts."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    bound_by_user_id: int
    notify_enabled: bool = True
    daily_summary_enabled: bool = True
    last_summary_date: date | None = None


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
    # The budget period: from the day of the first full salary until the day before the
    # next month starts (see app.domain.periods). end_date is None while no next month exists.
    start_date: date
    end_date: date | None = None
    # Set by hand for the first month or to correct the chain; otherwise the previous month's closing is used.
    carryover_override: Decimal | None = None


# Coloured pencils a category can be marked with. None means "pick automatically by position".
CategoryColor = Literal["orange", "teal", "violet", "green", "sky", "lilac", "ochre", "brown"]


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    name: str
    limit_amount: Decimal
    position: int = 0
    color: CategoryColor | None = None


class Expense(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    amount: Decimal
    description: str | None = None
    expense_date: date
    created_by_user_id: int
    # Who actually spent the money; may differ from who wrote it down.
    spent_by_user_id: int


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


# regular: the monthly payment, split into interest and principal; early: an early
# repayment, all of it goes to the principal; correction: the balance set to the bank's
# figure, no money moves. Only regular and early payments leave the shared budget.
LoanPaymentKind = Literal["regular", "early", "correction"]


class Loan(BaseModel):
    """A bank loan. `principal` is the debt when the loan was added to the app; the balance
    is what is left after the principal parts of its payments."""

    id: int
    name: str
    principal: Decimal
    start_date: date
    rate_percent: Decimal
    monthly_payment: Decimal
    payment_day: int
    is_closed: bool = False
    balance: Decimal
    regular_payments: int = 0
    # Which payment date the bot has already reminded about; internal only.
    last_reminded_due: date | None = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def next_payment_date(self) -> date | None:
        if self.is_closed or self.balance <= 0:
            return None
        return nth_payment_date(self.start_date, self.payment_day, self.regular_payments + 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def payments_left(self) -> int | None:
        """None when the monthly payment does not cover the interest."""
        result = forecast(self.balance, self.rate_percent, self.monthly_payment)
        return result.payments_left if result else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def interest_left(self) -> Decimal | None:
        result = forecast(self.balance, self.rate_percent, self.monthly_payment)
        return result.interest_left if result else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def payoff_date(self) -> date | None:
        next_date, left = self.next_payment_date, self.payments_left
        if next_date is None or not left:
            return None
        return months_after(next_date, self.payment_day, left - 1)


class LoanPayment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    loan_id: int
    kind: LoanPaymentKind
    amount: Decimal
    interest_part: Decimal
    principal_part: Decimal
    payment_date: date
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
    loan_payments: Decimal = Decimal(0)

    @property
    def net(self) -> Decimal:
        return (
            self.income - self.expenses - self.grey_zone - self.savings_in + self.savings_out - self.loan_payments
        )


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
    """Where the month's money went: net = income - spent - grey zone - savings - loan payments + adjustments.

    `adjustments` are reconciliation differences dated within the month.
    """

    income_actual: Decimal
    total_spent: Decimal
    grey_zone_taken: Decimal
    savings_net: Decimal
    loan_payments: Decimal
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
