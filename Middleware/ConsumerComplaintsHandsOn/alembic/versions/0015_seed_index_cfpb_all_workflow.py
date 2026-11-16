"""seed index_cfpb_all workflow + All MIO bind + index AppEndpoint (D88)

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0017/index_cfpb_all")
WORKFLOW_ID = "120e90d3-f61d-5fd4-a8c4-2a1aba9e9ba6"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0018/mios-workflows-all-index")
BINDING_ID = "ee28b7aa-b4cf-5611-bf07-080fb3b53864"
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0017/ep-cfpb-index-mongo-vectors")
INDEX_EP_ID = "af151640-ce3a-5995-a390-fa1ec5212aaf"

_when = sa.DateTime(timezone=True)
workflows = sa.table(
    "app_workflows",
    sa.column("id", sa.String),
    sa.column("workflow_name", sa.String),
    sa.column("engine_type", sa.String),
    sa.column("engine_workflow_id", sa.String),
    sa.column("config", sa.JSON),
    sa.column("enabled", sa.Boolean),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
mios_workflows = sa.table(
    "mios_workflows",
    sa.column("id", sa.String),
    sa.column("mio_id", sa.String),
    sa.column("workflow_id", sa.String),
    sa.column("created_at", _when),
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
    op.bulk_insert(
        workflows,
        [
            {
                "id": WORKFLOW_ID,
                "workflow_name": "index_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "index_cfpb_all",
                "config": {
                    "dataset_code": "CFPB",
                    "batch_size": 500,
                    "app_endpoint_name": "cfpb_index_mongo_to_vectors",
                },
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        mios_workflows,
        [
            {
                "id": BINDING_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": WORKFLOW_ID,
                "created_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        endpoints,
        [
            {
                "id": INDEX_EP_ID,
                "name": "cfpb_index_mongo_to_vectors",
                "category": "index",
                "from_dataset_location_id": None,
                "from_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                "to_dataset_location_id": None,
                "to_env_var_name": "CCA_VECTOR_STORE_PATH",
                "credentials_ref": None,
                "description": "Complaint Mongo → local vector store (D88)",
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(endpoints).where(endpoints.c.id == INDEX_EP_ID))
    op.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == BINDING_ID))
    op.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
