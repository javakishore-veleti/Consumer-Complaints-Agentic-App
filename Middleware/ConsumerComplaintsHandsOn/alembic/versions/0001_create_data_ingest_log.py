"""create data_ingest_log

Revision ID: 0001
Revises:
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_db"


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("ix_data_ingest_log_purpose_status", table_name="data_ingest_log", schema=SCHEMA)
    op.drop_table("data_ingest_log", schema=SCHEMA)
