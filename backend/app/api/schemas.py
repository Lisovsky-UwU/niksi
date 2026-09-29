"""Thin HTTP-only input DTOs. Response bodies reuse the domain models directly
(app.domain.models) since those are already Pydantic v2 and safe to serialize.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.domain.models import CategoryColor, SavingsPotKind, SavingsTransferDirection


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MonthCreateRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    copy_categories_from_previous: bool = False
    # The day the month's budget starts (first full salary); the 1st when omitted.
    start_date: date | None = None


class MonthStartRequest(BaseModel):
    start_date: date


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    limit_amount: Decimal = Field(ge=0)
    color: CategoryColor | None = None


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    limit_amount: Decimal | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)
    # Omitted: unchanged. "auto": back to the automatic colour.
    color: CategoryColor | Literal["auto"] | None = None


class ExpenseCreateRequest(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)
    expense_date: date
    # Who spent the money; defaults to whoever records it.
    spent_by_user_id: int | None = None


class ExpenseUpdateRequest(BaseModel):
    """Only fields present in the request change; sending "description": null erases the comment."""

    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)
    expense_date: date | None = None
    category_id: int | None = None
    spent_by_user_id: int | None = None


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=200)


class IncomeSetRequest(BaseModel):
    forecast_amount: Decimal = Field(ge=0)


class IncomeEntryCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=200)
    received_date: date
    # Whose money it is; defaults to whoever records it.
    user_id: int | None = None


class GreyZoneLimitRequest(BaseModel):
    amount: Decimal = Field(ge=0)


class GreyZoneTakeRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    taken_date: date


class CarryoverRequest(BaseModel):
    # None switches back to the automatic carry-over from the previous month.
    amount: Decimal | None = None


class SavingsPotCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: SavingsPotKind
    target_amount: Decimal | None = Field(default=None, gt=0)
    target_date: date | None = None


class SavingsPotUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: Decimal | None = Field(default=None, gt=0)
    target_date: date | None = None
    is_archived: bool = False


class SavingsTransferCreateRequest(BaseModel):
    direction: SavingsTransferDirection
    amount: Decimal = Field(gt=0)
    transfer_date: date
    note: str | None = Field(default=None, max_length=200)


class ReconciliationCreateRequest(BaseModel):
    actual_balance: Decimal
    balance_date: date
    note: str | None = Field(default=None, max_length=200)
