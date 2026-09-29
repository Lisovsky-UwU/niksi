"""SQLAlchemy persistence models. These never leave the infrastructure layer —
repositories map them to/from the Pydantic domain models in `app.domain.models`.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonthORM(Base):
    __tablename__ = "months"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_months_year_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["CategoryORM"] = relationship(back_populates="expenses")


class IncomeORM(Base):
    __tablename__ = "incomes"
    __table_args__ = (UniqueConstraint("month_id", "user_id", name="uq_incomes_month_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    forecast_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    month: Mapped["MonthORM"] = relationship(back_populates="incomes")
