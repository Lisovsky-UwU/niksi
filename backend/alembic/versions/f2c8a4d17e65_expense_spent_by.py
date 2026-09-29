"""expense spent by

Revision ID: f2c8a4d17e65
Revises: e4b7c2a91d53
Create Date: 2026-09-30 14:00:00

Who spent the money is now separate from who wrote the expense down. For existing
expenses they are taken to be the same person.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2c8a4d17e65"
down_revision: Union[str, Sequence[str], None] = "e4b7c2a91d53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("expenses", sa.Column("spent_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.execute("UPDATE expenses SET spent_by_user_id = created_by_user_id")
    op.alter_column("expenses", "spent_by_user_id", nullable=False)


def downgrade() -> None:
    op.drop_column("expenses", "spent_by_user_id")
