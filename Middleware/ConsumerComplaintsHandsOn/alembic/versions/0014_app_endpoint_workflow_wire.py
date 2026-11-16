"""Wire download/ingest workflows to AppEndpoints + seed ingest endpoint (D87)

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-15
"""

import json
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
DOWNLOAD_WF_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
INGEST_WF_ID = "0064095f-9f8e-5f09-94cf-3b4fe28e2b33"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0015/ep-cfpb-ingest-local-mongo")
INGEST_EP_ID = "8ca22b0c-1c7c-5a25-be9d-d51c6063a3a5"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"

DOWNLOAD_CFG = {
    "dataset_code": "CFPB",
    "app_endpoint_name": "cfpb_source_http_to_local",
}
INGEST_CFG = {
    "dataset_code": "CFPB",
    "source_filename": "complaints.csv.zip",
    "batch_size": 500,
    "app_endpoint_name": "cfpb_ingest_local_to_mongo",
}
DOWNLOAD_CFG_DOWN = {"dataset_code": "CFPB"}
INGEST_CFG_DOWN = {
    "dataset_code": "CFPB",
    "source_filename": "complaints.csv.zip",
    "batch_size": 500,
}

_when = sa.DateTime(timezone=True)
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


def _set_workflow_config(conn, workflow_id: str, config: dict) -> None:
    payload = json.dumps(config)
    conn.execute(
        sa.text(
            f"UPDATE {SCHEMA}.app_workflows SET config = :cfg, updated_at = :ts WHERE id = :id"
        ),
        {"id": workflow_id, "cfg": payload, "ts": NOW},
    )


def upgrade() -> None:
    op.bulk_insert(
        endpoints,
        [
            {
                "id": INGEST_EP_ID,
                "name": "cfpb_ingest_local_to_mongo",
                "category": "ingest",
                "from_dataset_location_id": LOCAL_LOCATION_ID,
                "from_env_var_name": None,
                "to_dataset_location_id": None,
                "to_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                "credentials_ref": None,
                "description": "Local landing → complaint Mongo (D86/D87)",
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )
    conn = op.get_bind()
    _set_workflow_config(conn, DOWNLOAD_WF_ID, DOWNLOAD_CFG)
    _set_workflow_config(conn, INGEST_WF_ID, INGEST_CFG)


def downgrade() -> None:
    conn = op.get_bind()
    _set_workflow_config(conn, DOWNLOAD_WF_ID, DOWNLOAD_CFG_DOWN)
    _set_workflow_config(conn, INGEST_WF_ID, INGEST_CFG_DOWN)
    op.execute(sa.delete(endpoints).where(endpoints.c.id == INGEST_EP_ID))
