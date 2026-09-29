"""month start date

Revision ID: e4b7c2a91d53
Revises: d8f1b3c64e02
Create Date: 2026-09-30 10:00:00

A budget month now starts on the day of the first full salary. Existing months keep
starting on the 1st, so nothing changes until someone moves a start date.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4b7c2a91d53"
down_revision: Union[str, Sequence[str], None] = "d8f1b3c64e02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("months", sa.Column("start_date", sa.Date(), nullable=True))
    op.execute("UPDATE months SET start_date = make_date(year, month, 1)")
    op.alter_column("months", "start_date", nullable=False)


def downgrade() -> None:
    op.drop_column("months", "start_date")
