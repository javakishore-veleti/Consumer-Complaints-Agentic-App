"""seed ingest_cfpb_all workflow + All MIO binding (M04-0013 / D86)

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0013/ingest_cfpb_all")
WORKFLOW_ID = "0064095f-9f8e-5f09-94cf-3b4fe28e2b33"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0013/mios-workflows-all-ingest")
BINDING_ID = "251b44d2-9aea-5d9d-b1a0-0816e8db3f80"
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"

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


def upgrade() -> None:
    op.bulk_insert(
        workflows,
        [
            {
                "id": WORKFLOW_ID,
                "workflow_name": "ingest_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "ingest_cfpb_all",
                "config": {
                    "dataset_code": "CFPB",
                    "source_filename": "complaints.csv.zip",
                    "batch_size": 500,
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


def downgrade() -> None:
    op.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == BINDING_ID))
    op.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
