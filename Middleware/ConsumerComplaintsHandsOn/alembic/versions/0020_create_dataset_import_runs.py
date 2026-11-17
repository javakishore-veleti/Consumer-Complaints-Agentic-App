"""create dataset_import_runs (M11 import registry)

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"


def upgrade() -> None:
    op.create_table(
        "dataset_import_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_folder_name", sa.String(32), nullable=False),
        sa.Column("location_kind", sa.String(32), nullable=False),
        sa.Column("location_ref", sa.Text(), nullable=False),
        sa.Column("source_snapshot_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_snapshot_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("workflow_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("workflow_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mio_id", sa.String(36), nullable=True),
        sa.Column("execution_id", sa.String(36), nullable=True),
        sa.Column("part_count", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_dataset_import_runs_status",
        "dataset_import_runs",
        ["status"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_dataset_import_runs_run_folder",
        "dataset_import_runs",
        ["run_folder_name"],
        schema=SCHEMA,
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_dataset_import_runs_run_folder", table_name="dataset_import_runs", schema=SCHEMA)
    op.drop_index("ix_dataset_import_runs_status", table_name="dataset_import_runs", schema=SCHEMA)
    op.drop_table("dataset_import_runs", schema=SCHEMA)
