"""create app_workflows_exec_log in the admin schema (every execution of every workflow)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "app_workflows_exec_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),  # no foreign key on purpose (D56)
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("engine_type", sa.String(32), nullable=False),
        sa.Column("engine_workflow_id", sa.String(255), nullable=False),
        sa.Column("config_used", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("engine_run_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_app_wf_exec_log_workflow_status",
        "app_workflows_exec_log",
        ["workflow_id", "status"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_app_wf_exec_log_workflow_status", table_name="app_workflows_exec_log", schema=SCHEMA)
    op.drop_table("app_workflows_exec_log", schema=SCHEMA)
