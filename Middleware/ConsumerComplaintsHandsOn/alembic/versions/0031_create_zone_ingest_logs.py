"""create zone ingest_log_* tables (M55-0011 / #391)

Revision ID: 0031
Revises: 0030
Create Date: 2026-11-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: Union[str, None] = "0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
ZONES = ("raw", "refined", "curated", "taxonomy", "chroma")


def _create_zone_table(zone: str) -> None:
    table = f"ingest_log_{zone}"
    op.create_table(
        table,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("partition_key", sa.String(128), nullable=False),
        sa.Column("data_tech", sa.String(32), nullable=False),
        sa.Column("source_end_point_id", sa.String(36), nullable=False),
        sa.Column("dest_end_point_id", sa.String(36), nullable=False),
        sa.Column("workflow_execution_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("status_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("configs_json", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "partition_key",
            "source_end_point_id",
            "dest_end_point_id",
            name=f"uq_ingest_log_{zone}_partition_endpoints",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        f"ix_ingest_log_{zone}_status_updated",
        table,
        ["status", "status_updated_on"],
        schema=SCHEMA,
    )
    op.create_index(
        f"ix_ingest_log_{zone}_workflow_execution_id",
        table,
        ["workflow_execution_id"],
        schema=SCHEMA,
    )
    op.create_index(
        f"ix_ingest_log_{zone}_status_updated_on",
        table,
        ["status_updated_on"],
        schema=SCHEMA,
    )


def upgrade() -> None:
    for zone in ZONES:
        _create_zone_table(zone)


def downgrade() -> None:
    for zone in reversed(ZONES):
        table = f"ingest_log_{zone}"
        op.drop_index(f"ix_ingest_log_{zone}_status_updated_on", table_name=table, schema=SCHEMA)
        op.drop_index(f"ix_ingest_log_{zone}_workflow_execution_id", table_name=table, schema=SCHEMA)
        op.drop_index(f"ix_ingest_log_{zone}_status_updated", table_name=table, schema=SCHEMA)
        op.drop_table(table, schema=SCHEMA)
