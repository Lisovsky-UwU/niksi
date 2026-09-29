from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Category
from app.infrastructure.db.orm_models import CategoryORM
from app.interfaces.repositories import CategoryRepository


class SqlAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, category_id: int) -> Category | None:
        orm = self._db.get(CategoryORM, category_id)
        return Category.model_validate(orm) if orm else None

    def list_by_month(self, month_id: int) -> list[Category]:
        orms = self._db.scalars(
            select(CategoryORM).where(CategoryORM.month_id == month_id).order_by(CategoryORM.position, CategoryORM.id)
        ).all()
        return [Category.model_validate(orm) for orm in orms]

    def create(self, month_id: int, name: str, limit_amount: Decimal, position: int) -> Category:
        orm = CategoryORM(month_id=month_id, name=name, limit_amount=limit_amount, position=position)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return Category.model_validate(orm)

    def update(
        self,
        category_id: int,
        name: str | None,
        limit_amount: Decimal | None,
        position: int | None,
    ) -> Category:
        orm = self._db.get(CategoryORM, category_id)
        assert orm is not None
        if name is not None:
            orm.name = name
        if limit_amount is not None:
            orm.limit_amount = limit_amount
        if position is not None:
            orm.position = position
        self._db.commit()
        self._db.refresh(orm)
        return Category.model_validate(orm)

    def delete(self, category_id: int) -> None:
        orm = self._db.get(CategoryORM, category_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()
