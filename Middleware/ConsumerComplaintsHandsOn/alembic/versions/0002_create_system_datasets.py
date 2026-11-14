"""create system_datasets (one row per dataset and stage) and seed the four rows

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_db"
DATASETS = ("3_months", "all")
STAGES = ("download", "db_ingest")


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_table("system_datasets", schema=SCHEMA)
