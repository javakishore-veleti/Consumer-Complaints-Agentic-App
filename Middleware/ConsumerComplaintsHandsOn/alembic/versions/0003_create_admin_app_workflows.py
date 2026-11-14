"""create app_workflows in the admin schema (the registry of workflows)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "app_workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("engine_type", sa.String(32), nullable=False),
        sa.Column("engine_workflow_id", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workflow_name", name="uq_app_workflows_workflow_name"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("app_workflows", schema=SCHEMA)
