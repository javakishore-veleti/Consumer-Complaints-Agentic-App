"""dataset_import_run tags + optional comment (M17-0004 / #247)

Revision ID: 0025
Revises: 0024
Create Date: 2026-11-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"


def upgrade() -> None:
    op.add_column(
        "dataset_import_runs",
        sa.Column("comment", sa.Text(), nullable=True),
        schema=SCHEMA,
    )
    op.create_table(
        "dataset_import_run_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("import_run_id", sa.String(36), nullable=False),
        sa.Column("tag", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_dataset_import_run_tags_import_run_id",
        "dataset_import_run_tags",
        ["import_run_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_dataset_import_run_tags_tag",
        "dataset_import_run_tags",
        ["tag"],
        schema=SCHEMA,
    )
    op.create_index(
        "uq_dataset_import_run_tags_run_tag",
        "dataset_import_run_tags",
        ["import_run_id", "tag"],
        unique=True,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_dataset_import_run_tags_run_tag",
        table_name="dataset_import_run_tags",
        schema=SCHEMA,
    )
    op.drop_index(
        "ix_dataset_import_run_tags_tag",
        table_name="dataset_import_run_tags",
        schema=SCHEMA,
    )
    op.drop_index(
        "ix_dataset_import_run_tags_import_run_id",
        table_name="dataset_import_run_tags",
        schema=SCHEMA,
    )
    op.drop_table("dataset_import_run_tags", schema=SCHEMA)
    op.drop_column("dataset_import_runs", "comment", schema=SCHEMA)
