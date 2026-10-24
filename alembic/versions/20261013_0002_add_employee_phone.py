"""add employee phone number

Revision ID: 20261013_0002
Revises: 20261013_0001
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261013_0002"
down_revision: str | None = "20261013_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("phone_number", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "phone_number")
