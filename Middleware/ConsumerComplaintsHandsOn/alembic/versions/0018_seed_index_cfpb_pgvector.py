"""seed index_cfpb_pgvector workflow + All MIO bind + pgvector AppEndpoint (D92)

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-16
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0007/index_cfpb_pgvector")
WORKFLOW_ID = "68a0fa8a-825c-53f1-864f-5db167a339a0"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/mios-workflows-all-index-pgvector")
BINDING_ID = "494ff42b-a7e7-5e90-8430-74b81a52dff1"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/ep-cfpb-index-mongo-pgvector")
EP_ID = "2e6bd178-2900-5ea2-80ed-507f486a2133"

CONFIG = {
    "dataset_code": "CFPB",
    "batch_size": 500,
    "vector_backend": "pgvector",
    "app_endpoint_name": "cfpb_index_mongo_to_pgvector",
}

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
    bind = op.get_bind()
    bind.execute(
        sa.insert(workflows).values(
            id=WORKFLOW_ID,
            workflow_name="index_cfpb_pgvector",
            engine_type="apache_airflow",
            engine_workflow_id="index_cfpb_pgvector",
            config=CONFIG,
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    bind.execute(
        sa.insert(mios_workflows).values(
            id=BINDING_ID,
            mio_id=ALL_MIO_ID,
            workflow_id=WORKFLOW_ID,
            created_at=NOW,
        )
    )
    bind.execute(
        sa.insert(endpoints).values(
            id=EP_ID,
            name="cfpb_index_mongo_to_pgvector",
            category="index",
            from_dataset_location_id=None,
            from_env_var_name="CCA_MONGO_COMPLAINTS_URL",
            to_dataset_location_id=None,
            to_env_var_name="CCA_PGVECTOR_URL",
            credentials_ref=None,
            description="Complaint Mongo → local pgvector (D92)",
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.delete(endpoints).where(endpoints.c.id == EP_ID))
    bind.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == BINDING_ID))
    bind.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
