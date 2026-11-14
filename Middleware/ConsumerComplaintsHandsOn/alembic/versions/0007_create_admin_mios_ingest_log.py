"""create mios_ingest_log in the admin schema and the optional ingest reference of app_workflows_exec_log

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"


def upgrade() -> None:
    op.create_table(
        "mios_ingest_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),  # no foreign key on purpose (D57, D58)
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_loaded", sa.BigInteger(), nullable=True),
        sa.Column("batch_count", sa.Integer(), nullable=True),
        sa.Column("increment_marker", sa.String(255), nullable=True),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_ingest_log_mio_status", "mios_ingest_log", ["mio_id", "status"], schema=SCHEMA)
    # Batch mode, so SQLite can drop the column again on downgrade (it rebuilds the table).
    with op.batch_alter_table("app_workflows_exec_log", schema=SCHEMA) as batch:
        batch.add_column(sa.Column("mios_ingest_log_id", sa.String(36), nullable=True))  # no foreign key (D58)
        batch.create_index("ix_app_wf_exec_log_mios_ingest_log_id", ["mios_ingest_log_id"])


def downgrade() -> None:
    with op.batch_alter_table("app_workflows_exec_log", schema=SCHEMA) as batch:
        batch.drop_index("ix_app_wf_exec_log_mios_ingest_log_id")
        batch.drop_column("mios_ingest_log_id")
    op.drop_index("ix_mios_ingest_log_mio_status", table_name="mios_ingest_log", schema=SCHEMA)
    op.drop_table("mios_ingest_log", schema=SCHEMA)
