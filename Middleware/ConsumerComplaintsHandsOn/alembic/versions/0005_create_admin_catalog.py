"""create the catalog tables in the admin schema: datasets, datasets_location, mios and mios_datasets

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(15), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_datasets_name"),
        sa.UniqueConstraint("code", name="uq_datasets_code"),
        schema=SCHEMA,
    )
    op.create_table(
        "datasets_location",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),  # no foreign key on purpose (D57)
        sa.Column("location_type", sa.String(32), nullable=False),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("local_env_var_name", sa.String(64), nullable=True),
        sa.Column("credentials_ref", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "location_type", "path", name="uq_datasets_location_dataset_type_path"),
        sa.UniqueConstraint("dataset_id", "local_env_var_name", name="uq_datasets_location_dataset_env_var"),
        sa.CheckConstraint(
            "(path IS NOT NULL AND local_env_var_name IS NULL) OR (path IS NULL AND local_env_var_name IS NOT NULL)",
            name="ck_datasets_location_path_xor_env",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_datasets_location_dataset_id", "datasets_location", ["dataset_id"], schema=SCHEMA)
    op.create_table(
        "mios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_mios_name"),
        schema=SCHEMA,
    )
    op.create_table(
        "mios_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),  # no foreign keys on purpose (D57)
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("dataset_location_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mio_id", "dataset_id", name="uq_mios_datasets_mio_dataset"),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_datasets_mio_id", "mios_datasets", ["mio_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_mios_datasets_mio_id", table_name="mios_datasets", schema=SCHEMA)
    op.drop_table("mios_datasets", schema=SCHEMA)
    op.drop_table("mios", schema=SCHEMA)
    op.drop_index("ix_datasets_location_dataset_id", table_name="datasets_location", schema=SCHEMA)
    op.drop_table("datasets_location", schema=SCHEMA)
    op.drop_table("datasets", schema=SCHEMA)
