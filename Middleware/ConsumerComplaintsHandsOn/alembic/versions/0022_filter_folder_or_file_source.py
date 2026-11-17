"""filter_cfpb_3_months: prefer folder or file via CCA_CFPB_SPLIT_SOURCE_PATH (M10-0023)

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-17
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)
FILTER_WF_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"

NEW_CONFIG = {
    "dataset_code": "CFPB",
    "months": 3,
    "source_path_env": "CCA_CFPB_SPLIT_SOURCE_PATH",
    "source_filename": "complaints.csv.zip",
    "output_filename": "complaints_3_months.csv.zip",
    "date_column": "Date received",
}
OLD_CONFIG = {
    "dataset_code": "CFPB",
    "months": 3,
    "source_filename": "complaints.csv.zip",
    "output_filename": "complaints_3_months.csv.zip",
    "date_column": "Date received",
}

_when = sa.DateTime(timezone=True)
workflows = sa.table(
    "app_workflows",
    sa.column("id", sa.String),
    sa.column("config", sa.JSON),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        workflows.update()
        .where(workflows.c.id == FILTER_WF_ID)
        .values(config=NEW_CONFIG, updated_at=NOW)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        workflows.update()
        .where(workflows.c.id == FILTER_WF_ID)
        .values(config=OLD_CONFIG, updated_at=NOW)
    )
