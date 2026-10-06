"""loans

Revision ID: b5d2e8f3a714
Revises: a9d3e5f7b812
Create Date: 2026-10-06 20:00:00

Bank loans and their payments. A payment stores its own split into interest and principal,
so the history does not change when the rate is edited later.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b5d2e8f3a714"
down_revision: Union[str, Sequence[str], None] = "a9d3e5f7b812"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("principal", sa.Numeric(12, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("rate_percent", sa.Numeric(6, 3), nullable=False),
        sa.Column("monthly_payment", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_day", sa.Integer(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_reminded_due", sa.Date(), nullable=True),
        _created_at(),
    )

    op.create_table(
        "loan_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loan_id", sa.Integer(), sa.ForeignKey("loans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("interest_part", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("principal_part", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        _created_at(),
    )
    op.create_index("ix_loan_payments_loan_id", "loan_payments", ["loan_id"])


def downgrade() -> None:
    op.drop_index("ix_loan_payments_loan_id", table_name="loan_payments")
    op.drop_table("loan_payments")
    op.drop_table("loans")
