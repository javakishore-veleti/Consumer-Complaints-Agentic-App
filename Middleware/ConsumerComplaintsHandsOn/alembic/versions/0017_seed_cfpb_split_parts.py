"""seed CFPB split-part download/ingest configs + stage AppEndpoint (D91)

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-16
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)
DOWNLOAD_WF_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
INGEST_WF_ID = "0064095f-9f8e-5f09-94cf-3b4fe28e2b33"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m06-0004/ep-cfpb-stage-split-local")
STAGE_EP_ID = "763c400e-09e1-59a5-92ed-ed910df667ac"

DOWNLOAD_SPLIT_CONFIG = {
    "dataset_code": "CFPB",
    "source_mode": "split",
    "source_filename_glob": "complaints_part_*.csv.zip",
    "stage_from_env": "CCA_CFPB_SPLIT_SOURCE_PATH",
    "app_endpoint_name": "cfpb_stage_split_to_local",
}
INGEST_SPLIT_CONFIG = {
    "dataset_code": "CFPB",
    "source_filename_glob": "complaints_part_*.csv.zip",
    "batch_size": 500,
    "app_endpoint_name": "cfpb_ingest_local_to_mongo",
}
DOWNLOAD_LEGACY = {
    "dataset_code": "CFPB",
    "app_endpoint_name": "cfpb_source_http_to_local",
}
INGEST_LEGACY = {
    "dataset_code": "CFPB",
    "source_filename": "complaints.csv.zip",
    "batch_size": 500,
    "app_endpoint_name": "cfpb_ingest_local_to_mongo",
}

_when = sa.DateTime(timezone=True)
workflows = sa.table(
    "app_workflows",
    sa.column("id", sa.String),
    sa.column("config", sa.JSON),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
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
    sa.column("description", sa.String),
    sa.column("enabled", sa.Boolean),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        workflows.update()
        .where(workflows.c.id == DOWNLOAD_WF_ID)
        .values(config=DOWNLOAD_SPLIT_CONFIG, updated_at=NOW)
    )
    bind.execute(
        workflows.update()
        .where(workflows.c.id == INGEST_WF_ID)
        .values(config=INGEST_SPLIT_CONFIG, updated_at=NOW)
    )
    bind.execute(
        sa.insert(endpoints).values(
            id=STAGE_EP_ID,
            name="cfpb_stage_split_to_local",
            category="source",
            from_dataset_location_id=None,
            from_env_var_name="CCA_CFPB_SPLIT_SOURCE_PATH",
            to_dataset_location_id=None,
            to_env_var_name="LOCAL_DATA_PATH_CFPB",
            credentials_ref=None,
            description="Stage CFPB split parts into local landing (D91)",
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.delete(endpoints).where(endpoints.c.id == STAGE_EP_ID))
    bind.execute(
        workflows.update()
        .where(workflows.c.id == DOWNLOAD_WF_ID)
        .values(config=DOWNLOAD_LEGACY, updated_at=NOW)
    )
    bind.execute(
        workflows.update()
        .where(workflows.c.id == INGEST_WF_ID)
        .values(config=INGEST_LEGACY, updated_at=NOW)
    )
