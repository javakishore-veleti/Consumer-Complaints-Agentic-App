"""drop retired system_datasets and data_ingest_log (D47 / D74)

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_db"
DATASETS = ("3_months", "all")
STAGES = ("download", "db_ingest")


def upgrade() -> None:
    op.drop_index("ix_data_ingest_log_purpose_status", table_name="data_ingest_log", schema=SCHEMA)
    op.drop_table("data_ingest_log", schema=SCHEMA)
    op.drop_table("system_datasets", schema=SCHEMA)


def downgrade() -> None:
    op.create_table(
        "data_ingest_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purpose", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("run_id", sa.String(128)),
        sa.Column("message", sa.Text()),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_data_ingest_log_purpose_status",
        "data_ingest_log",
        ["purpose", "status"],
        schema=SCHEMA,
    )
    table = op.create_table(
        "system_datasets",
        sa.Column("dataset", sa.String(32), primary_key=True),
        sa.Column("stage", sa.String(32), primary_key=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("last_log_id", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        table,
        [
            {"dataset": d, "stage": s, "status": "not_started", "last_log_id": None, "updated_at": now}
            for d in DATASETS
            for s in STAGES
        ],
    )
