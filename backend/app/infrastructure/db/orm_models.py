"""SQLAlchemy persistence models. These never leave the infrastructure layer —
repositories map them to/from the Pydantic domain models in `app.domain.models`.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    # Small square image resized in the browser; deferred so it is only loaded when served.
    avatar: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    avatar_content_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    avatar_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonthORM(Base):
    __tablename__ = "months"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_months_year_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    # Manually set carry-over from the previous month. None means "take the previous month's closing balance".
    carryover_override: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categories: Mapped[list["CategoryORM"]] = relationship(back_populates="month", cascade="all, delete-orphan")
    incomes: Mapped[list["IncomeORM"]] = relationship(back_populates="month", cascade="all, delete-orphan")


class CategoryORM(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    position: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    month: Mapped["MonthORM"] = relationship(back_populates="categories")
    expenses: Mapped[list["ExpenseORM"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class ExpenseORM(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    spent_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["CategoryORM"] = relationship(back_populates="expenses")


class IncomeORM(Base):
    __tablename__ = "incomes"
    __table_args__ = (UniqueConstraint("month_id", "user_id", name="uq_incomes_month_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    forecast_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    month: Mapped["MonthORM"] = relationship(back_populates="incomes")


class IncomeEntryORM(Base):
    __tablename__ = "income_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    received_date: Mapped[date] = mapped_column(Date)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GreyZoneLimitORM(Base):
    __tablename__ = "grey_zone_limits"
    __table_args__ = (UniqueConstraint("month_id", "user_id", name="uq_grey_zone_limits_month_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)


class GreyZoneEntryORM(Base):
    __tablename__ = "grey_zone_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    taken_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SavingsPotORM(Base):
    __tablename__ = "savings_pots"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))
    target_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transfers: Mapped[list["SavingsTransferORM"]] = relationship(back_populates="pot", cascade="all, delete-orphan")


class SavingsTransferORM(Base):
    __tablename__ = "savings_transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    pot_id: Mapped[int] = mapped_column(ForeignKey("savings_pots.id", ondelete="CASCADE"), index=True)
    direction: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    transfer_date: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pot: Mapped["SavingsPotORM"] = relationship(back_populates="transfers")


class ReconciliationORM(Base):
    __tablename__ = "reconciliations"

    id: Mapped[int] = mapped_column(primary_key=True)
    balance_date: Mapped[date] = mapped_column(Date)
    actual_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    expected_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    difference: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
