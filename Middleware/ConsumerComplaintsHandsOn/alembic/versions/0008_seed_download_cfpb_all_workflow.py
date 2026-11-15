"""seed app_workflows row for download_cfpb_all (M02-0018 / D63)

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0018/download_cfpb_all")
WORKFLOW_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"

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


def upgrade() -> None:
    op.bulk_insert(
        workflows,
        [
            {
                "id": WORKFLOW_ID,
                "workflow_name": "download_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "download_cfpb_all",
                "config": {"dataset_code": "CFPB"},
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
