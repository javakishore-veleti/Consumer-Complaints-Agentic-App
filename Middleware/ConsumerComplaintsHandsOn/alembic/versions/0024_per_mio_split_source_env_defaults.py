"""Per-MIO split source env vars (3m filter + all stage) — M17-0005 / #248

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-17
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)
FILTER_WF_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"
DOWNLOAD_WF_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
STAGE_EP_ID = "763c400e-09e1-59a5-92ed-ed910df667ac"

FILTER_NEW = {
    "dataset_code": "CFPB",
    "months": 3,
    "source_path_env": "CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS",
    "source_filename": "complaints.csv.zip",
    "output_filename": "complaints_3_months.csv.zip",
    "date_column": "Date received",
}
FILTER_OLD = {
    "dataset_code": "CFPB",
    "months": 3,
    "source_path_env": "CCA_CFPB_SPLIT_SOURCE_PATH",
    "source_filename": "complaints.csv.zip",
    "output_filename": "complaints_3_months.csv.zip",
    "date_column": "Date received",
}
DOWNLOAD_NEW = {
    "dataset_code": "CFPB",
    "source_mode": "split",
    "source_filename_glob": "complaints_part_*.csv.zip",
    "stage_from_env": "CCA_CFPB_SPLIT_SOURCE_PATH_ALL",
    "app_endpoint_name": "cfpb_stage_split_to_local",
}
DOWNLOAD_OLD = {
    "dataset_code": "CFPB",
    "source_mode": "split",
    "source_filename_glob": "complaints_part_*.csv.zip",
    "stage_from_env": "CCA_CFPB_SPLIT_SOURCE_PATH",
    "app_endpoint_name": "cfpb_stage_split_to_local",
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
    sa.column("from_env_var_name", sa.String),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        workflows.update()
        .where(workflows.c.id == FILTER_WF_ID)
        .values(config=FILTER_NEW, updated_at=NOW)
    )
    bind.execute(
        workflows.update()
        .where(workflows.c.id == DOWNLOAD_WF_ID)
        .values(config=DOWNLOAD_NEW, updated_at=NOW)
    )
    bind.execute(
        endpoints.update()
        .where(endpoints.c.id == STAGE_EP_ID)
        .values(from_env_var_name="CCA_CFPB_SPLIT_SOURCE_PATH_ALL", updated_at=NOW)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        workflows.update()
        .where(workflows.c.id == FILTER_WF_ID)
        .values(config=FILTER_OLD, updated_at=NOW)
    )
    bind.execute(
        workflows.update()
        .where(workflows.c.id == DOWNLOAD_WF_ID)
        .values(config=DOWNLOAD_OLD, updated_at=NOW)
    )
    bind.execute(
        endpoints.update()
        .where(endpoints.c.id == STAGE_EP_ID)
        .values(from_env_var_name="CCA_CFPB_SPLIT_SOURCE_PATH", updated_at=NOW)
    )
