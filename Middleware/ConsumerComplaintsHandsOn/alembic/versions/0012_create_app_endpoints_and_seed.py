"""create app_endpoints and seed CFPB source HTTP→local (D85 / M04 #155)

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0009/ep-cfpb-source-http-local")
ENDPOINT_ID = "ccbce57d-bd9f-56fe-a258-fa2deb9dd393"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"


def upgrade() -> None:
    op.create_table(
        "app_endpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("from_dataset_location_id", sa.String(36), nullable=True),
        sa.Column("from_env_var_name", sa.String(64), nullable=True),
        sa.Column("to_dataset_location_id", sa.String(36), nullable=True),
        sa.Column("to_env_var_name", sa.String(64), nullable=True),
        sa.Column("credentials_ref", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_app_endpoints_name"),
        sa.CheckConstraint(
            "(from_dataset_location_id IS NOT NULL AND from_env_var_name IS NULL) OR "
            "(from_dataset_location_id IS NULL AND from_env_var_name IS NOT NULL)",
            name="ck_app_endpoints_from_xor",
        ),
        sa.CheckConstraint(
            "(to_dataset_location_id IS NOT NULL AND to_env_var_name IS NULL) OR "
            "(to_dataset_location_id IS NULL AND to_env_var_name IS NOT NULL)",
            name="ck_app_endpoints_to_xor",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_app_endpoints_category", "app_endpoints", ["category"], schema=SCHEMA)

    endpoints = sa.table(
        "app_endpoints",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("from_dataset_location_id", sa.String),
        sa.column("from_env_var_name", sa.String),
        sa.column("to_dataset_location_id", sa.String),
        sa.column("to_env_var_name", sa.String),
        sa.column("credentials_ref", sa.String),
        sa.column("description", sa.Text),
        sa.column("enabled", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.bulk_insert(
        endpoints,
        [
            {
                "id": ENDPOINT_ID,
                "name": "cfpb_source_http_to_local",
                "category": "source",
                "from_dataset_location_id": HTTP_LOCATION_ID,
                "from_env_var_name": None,
                "to_dataset_location_id": LOCAL_LOCATION_ID,
                "to_env_var_name": None,
                "credentials_ref": None,
                "description": "CFPB download HTTP source to local landing (D63)",
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_app_endpoints_category", table_name="app_endpoints", schema=SCHEMA)
    op.drop_table("app_endpoints", schema=SCHEMA)
