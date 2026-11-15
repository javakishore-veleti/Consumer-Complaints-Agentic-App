"""seed app_workflows row for filter_cfpb_3_months (M02-0019 / D70)

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0019/filter_cfpb_3_months")
WORKFLOW_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"

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

CONFIG = {
    "dataset_code": "CFPB",
    "months": 3,
    "source_filename": "complaints.csv.zip",
    "output_filename": "complaints_3_months.csv.zip",
    "date_column": "Date received",
}


def upgrade() -> None:
    op.bulk_insert(
        workflows,
        [
            {
                "id": WORKFLOW_ID,
                "workflow_name": "filter_cfpb_3_months",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "filter_cfpb_3_months",
                "config": CONFIG,
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
