"""Domain entities and aggregates, shared by every entry point (web API today, Telegram bot later).

These are plain Pydantic v2 models with no dependency on SQLAlchemy, FastAPI, or any
other framework. `infrastructure/repositories` are responsible for converting to/from
ORM rows; `api/routes` may return these directly as HTTP response bodies since Pydantic
models already know how to serialize themselves.
"""

from datetime import date
from decimal import Decimal

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    month_id: int
    user_id: int
    forecast_amount: Decimal
    actual_amount: Decimal


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


class MonthTotals(BaseModel):
    total_limit: Decimal
    total_spent: Decimal


class IncomeSummary(BaseModel):
    per_user: list[UserIncomeSummary]
    household_forecast: Decimal
    household_actual: Decimal


class BalanceSummary(BaseModel):
    income_actual: Decimal
    total_spent: Decimal
    net: Decimal


class MonthSummary(BaseModel):
    month: Month
    categories: list[CategorySummary]
    totals: MonthTotals
    income: IncomeSummary
    balance: BalanceSummary
