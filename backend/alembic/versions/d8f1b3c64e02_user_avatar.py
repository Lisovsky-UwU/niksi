"""user avatar

Revision ID: d8f1b3c64e02
Revises: c3a9d5e27b41
Create Date: 2026-09-29 20:00:00

A small square picture per person, shown next to their expenses, income and grey zone.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8f1b3c64e02"
down_revision: Union[str, Sequence[str], None] = "c3a9d5e27b41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar", sa.LargeBinary(), nullable=True))
    op.add_column("users", sa.Column("avatar_content_type", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("avatar_version", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_version")
    op.drop_column("users", "avatar_content_type")
    op.drop_column("users", "avatar")
