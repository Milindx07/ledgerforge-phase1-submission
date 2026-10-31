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
    # The initial schema already contains phone_number in some distributed Phase 1
    # databases. Keep both fresh installs and those snapshots migratable.
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("employees")}
    if "phone_number" not in columns:
        op.add_column("employees", sa.Column("phone_number", sa.String(length=30), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("employees")}
    if "phone_number" in columns:
        op.drop_column("employees", "phone_number")
