from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Expense
from app.infrastructure.db.orm_models import CategoryORM, ExpenseORM
from app.interfaces.repositories import ExpenseRepository


class SqlAlchemyExpenseRepository(ExpenseRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, expense_id: int) -> Expense | None:
        orm = self._db.get(ExpenseORM, expense_id)
        return Expense.model_validate(orm) if orm else None

    def list_filtered(self, month_id: int | None, category_id: int | None) -> list[Expense]:
        stmt = select(ExpenseORM)
        if month_id is not None:
            stmt = stmt.join(CategoryORM, ExpenseORM.category_id == CategoryORM.id).where(
                CategoryORM.month_id == month_id
            )
        if category_id is not None:
            stmt = stmt.where(ExpenseORM.category_id == category_id)
        stmt = stmt.order_by(ExpenseORM.expense_date.desc(), ExpenseORM.id.desc())
        orms = self._db.scalars(stmt).all()
        return [Expense.model_validate(orm) for orm in orms]

    def sum_by_category_for_month(self, month_id: int) -> dict[int, Decimal]:
        stmt = (
            select(ExpenseORM.category_id, func.coalesce(func.sum(ExpenseORM.amount), 0))
            .join(CategoryORM, ExpenseORM.category_id == CategoryORM.id)
            .where(CategoryORM.month_id == month_id)
            .group_by(ExpenseORM.category_id)
        )
        return {category_id: Decimal(total) for category_id, total in self._db.execute(stmt).all()}

    def create(
        self,
        category_id: int,
        amount: Decimal,
        description: str | None,
        expense_date: date,
        created_by_user_id: int,
        spent_by_user_id: int,
    ) -> Expense:
        orm = ExpenseORM(
            category_id=category_id,
            amount=amount,
            description=description,
            expense_date=expense_date,
            created_by_user_id=created_by_user_id,
            spent_by_user_id=spent_by_user_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return Expense.model_validate(orm)

    def update(
        self,
        expense_id: int,
        amount: Decimal | None,
        description: str | None,
        expense_date: date | None,
        category_id: int | None = None,
        set_description: bool = False,
        spent_by_user_id: int | None = None,
    ) -> Expense:
        orm = self._db.get(ExpenseORM, expense_id)
        assert orm is not None
        if amount is not None:
            orm.amount = amount
        if set_description or description is not None:
            orm.description = description
        if category_id is not None:
            orm.category_id = category_id
        if expense_date is not None:
            orm.expense_date = expense_date
        if spent_by_user_id is not None:
            orm.spent_by_user_id = spent_by_user_id
        self._db.commit()
        self._db.refresh(orm)
        return Expense.model_validate(orm)

    def delete(self, expense_id: int) -> None:
        orm = self._db.get(ExpenseORM, expense_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()
