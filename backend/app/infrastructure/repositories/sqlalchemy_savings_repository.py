from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.models import SavingsPot, SavingsPotKind, SavingsTransfer, SavingsTransferDirection
from app.infrastructure.db.orm_models import SavingsPotORM, SavingsTransferORM
from app.interfaces.repositories import SavingsRepository

# Money going out of a pot is negative, everything else (deposits, interest) adds to it.
_signed_amount = case(
    (SavingsTransferORM.direction == "out", -SavingsTransferORM.amount),
    else_=SavingsTransferORM.amount,
)


class SqlAlchemySavingsRepository(SavingsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def _balances(self, pot_ids: list[int]) -> dict[int, Decimal]:
        if not pot_ids:
            return {}
        stmt = (
            select(SavingsTransferORM.pot_id, func.coalesce(func.sum(_signed_amount), 0))
            .where(SavingsTransferORM.pot_id.in_(pot_ids))
            .group_by(SavingsTransferORM.pot_id)
        )
        return {pot_id: Decimal(total) for pot_id, total in self._db.execute(stmt).all()}

    @staticmethod
    def _to_domain(orm: SavingsPotORM, balance: Decimal) -> SavingsPot:
        return SavingsPot(
            id=orm.id,
            name=orm.name,
            kind=orm.kind,  # type: ignore[arg-type]
            target_amount=orm.target_amount,
            target_date=orm.target_date,
            is_archived=orm.is_archived,
            balance=balance,
        )

    def list_pots(self, include_archived: bool) -> list[SavingsPot]:
        stmt = select(SavingsPotORM).order_by(SavingsPotORM.id)
        if not include_archived:
            stmt = stmt.where(SavingsPotORM.is_archived.is_(False))
        orms = self._db.scalars(stmt).all()
        balances = self._balances([orm.id for orm in orms])
        return [self._to_domain(orm, balances.get(orm.id, Decimal(0))) for orm in orms]

    def get_pot(self, pot_id: int) -> SavingsPot | None:
        orm = self._db.get(SavingsPotORM, pot_id)
        if orm is None:
            return None
        return self._to_domain(orm, self._balances([pot_id]).get(pot_id, Decimal(0)))

    def create_pot(
        self,
        name: str,
        kind: SavingsPotKind,
        target_amount: Decimal | None,
        target_date: date | None,
    ) -> SavingsPot:
        orm = SavingsPotORM(name=name, kind=kind, target_amount=target_amount, target_date=target_date, is_archived=False)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm, Decimal(0))

    def update_pot(
        self,
        pot_id: int,
        name: str,
        target_amount: Decimal | None,
        target_date: date | None,
        is_archived: bool,
    ) -> SavingsPot:
        orm = self._db.get(SavingsPotORM, pot_id)
        assert orm is not None
        orm.name = name
        orm.target_amount = target_amount
        orm.target_date = target_date
        orm.is_archived = is_archived
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm, self._balances([pot_id]).get(pot_id, Decimal(0)))

    def delete_pot(self, pot_id: int) -> None:
        orm = self._db.get(SavingsPotORM, pot_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def has_transfers(self, pot_id: int) -> bool:
        return self._db.scalar(select(SavingsTransferORM.id).where(SavingsTransferORM.pot_id == pot_id).limit(1)) is not None

    def list_transfers(self, pot_id: int) -> list[SavingsTransfer]:
        orms = self._db.scalars(
            select(SavingsTransferORM)
            .where(SavingsTransferORM.pot_id == pot_id)
            .order_by(SavingsTransferORM.transfer_date.desc(), SavingsTransferORM.id.desc())
        ).all()
        return [SavingsTransfer.model_validate(orm) for orm in orms]

    def get_transfer(self, transfer_id: int) -> SavingsTransfer | None:
        orm = self._db.get(SavingsTransferORM, transfer_id)
        return SavingsTransfer.model_validate(orm) if orm else None

    def create_transfer(
        self,
        pot_id: int,
        direction: SavingsTransferDirection,
        amount: Decimal,
        transfer_date: date,
        note: str | None,
        created_by_user_id: int,
    ) -> SavingsTransfer:
        orm = SavingsTransferORM(
            pot_id=pot_id,
            direction=direction,
            amount=amount,
            transfer_date=transfer_date,
            note=note,
            created_by_user_id=created_by_user_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return SavingsTransfer.model_validate(orm)

    def delete_transfer(self, transfer_id: int) -> None:
        orm = self._db.get(SavingsTransferORM, transfer_id)
        if orm is not None:
            self._db.delete(orm)
            self._db.commit()

    def sum_budget_flows_between(self, start: date, end: date) -> tuple[Decimal, Decimal]:
        stmt = (
            select(SavingsTransferORM.direction, func.coalesce(func.sum(SavingsTransferORM.amount), 0))
            .where(
                SavingsTransferORM.transfer_date >= start,
                SavingsTransferORM.transfer_date <= end,
                SavingsTransferORM.direction.in_(("in", "out")),
            )
            .group_by(SavingsTransferORM.direction)
        )
        totals = {direction: Decimal(total) for direction, total in self._db.execute(stmt).all()}
        return totals.get("in", Decimal(0)), totals.get("out", Decimal(0))
