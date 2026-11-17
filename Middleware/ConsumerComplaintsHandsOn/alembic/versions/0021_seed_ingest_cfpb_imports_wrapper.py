"""seed ingest_cfpb_imports_wrapper workflow + All MIO binding (M11)

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-17
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)
WORKFLOW_ID = "e64365bd-98f4-52a4-a3bc-e26455915c6b"
BINDING_ID = "3075d780-d9eb-5fe5-8b03-2cdcab384cc9"
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
                "workflow_name": "ingest_cfpb_imports_wrapper",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "ingest_cfpb_imports_wrapper",
                "config": {
                    "dataset_code": "CFPB",
                    "source_filename_glob": "complaints_part_*.csv.zip",
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
