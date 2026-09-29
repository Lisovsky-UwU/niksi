"""income entries, grey zone, savings, reconciliation, carry-over

Revision ID: b7e2c91f4a10
Revises: dac45a62a1e3
Create Date: 2026-09-29 12:00:00

Actual income moves from a single `incomes.actual_amount` number to individual
`income_entries` rows. Existing non-zero amounts become one entry each, dated the first
day of their month, so no history is lost.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e2c91f4a10"
down_revision: Union[str, Sequence[str], None] = "dac45a62a1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
    )


def upgrade() -> None:
    op.add_column("months", sa.Column("carryover_override", sa.Numeric(12, 2), nullable=True))

    op.create_table(
        "income_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month_id", sa.Integer(), sa.ForeignKey("months.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        _created_at(),
    )
    op.create_index("ix_income_entries_month_id", "income_entries", ["month_id"])

    op.execute(
        """
        INSERT INTO income_entries (month_id, user_id, amount, description, received_date, created_by_user_id)
        SELECT i.month_id, i.user_id, i.actual_amount, 'Доход', make_date(m.year, m.month, 1), i.user_id
        FROM incomes i JOIN months m ON m.id = i.month_id
        WHERE i.actual_amount > 0
        """
    )
    op.drop_column("incomes", "actual_amount")

    op.create_table(
        "grey_zone_limits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month_id", sa.Integer(), sa.ForeignKey("months.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("month_id", "user_id", name="uq_grey_zone_limits_month_user"),
    )

    op.create_table(
        "grey_zone_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month_id", sa.Integer(), sa.ForeignKey("months.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("taken_date", sa.Date(), nullable=False),
        _created_at(),
    )
    op.create_index("ix_grey_zone_entries_month_id", "grey_zone_entries", ["month_id"])

    op.create_table(
        "savings_pots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created_at(),
    )

    op.create_table(
        "savings_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pot_id", sa.Integer(), sa.ForeignKey("savings_pots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        _created_at(),
    )
    op.create_index("ix_savings_transfers_pot_id", "savings_transfers", ["pot_id"])

    op.create_table(
        "reconciliations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("balance_date", sa.Date(), nullable=False),
        sa.Column("actual_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("expected_balance", sa.Numeric(12, 2), nullable=True),
        sa.Column("difference", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        _created_at(),
    )


def downgrade() -> None:
    op.drop_table("reconciliations")
    op.drop_index("ix_savings_transfers_pot_id", table_name="savings_transfers")
    op.drop_table("savings_transfers")
    op.drop_table("savings_pots")
    op.drop_index("ix_grey_zone_entries_month_id", table_name="grey_zone_entries")
    op.drop_table("grey_zone_entries")
    op.drop_table("grey_zone_limits")

    op.add_column(
        "incomes", sa.Column("actual_amount", sa.Numeric(12, 2), nullable=False, server_default="0")
    )
    op.execute(
        """
        UPDATE incomes i SET actual_amount = COALESCE(
            (SELECT SUM(e.amount) FROM income_entries e WHERE e.month_id = i.month_id AND e.user_id = i.user_id), 0
        )
        """
    )
    op.drop_index("ix_income_entries_month_id", table_name="income_entries")
    op.drop_table("income_entries")

    op.drop_column("months", "carryover_override")
