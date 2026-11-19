"""seed hydrate_curated_iceberg_3m workflow + 3m MIO bind (M51 / #344)

Revision ID: 0029
Revises: 0028
Create Date: 2026-11-19
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029"
down_revision: Union[str, None] = "0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 19, tzinfo=timezone.utc)
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
WF_ID = "24e5f80c-68cc-5f99-8f33-2fd3ea48d4b0"
BIND_ID = "e1043a76-3059-57de-945f-a376c6ad3a78"

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
    bind = op.get_bind()
    bind.execute(
        sa.insert(workflows).values(
            id=WF_ID,
            workflow_name="hydrate_curated_iceberg_3m",
            engine_type="apache_airflow",
            engine_workflow_id="hydrate_curated_iceberg_3m",
            config={"dataset_code": "CFPB", "dataset_slice": "3m", "lakehouse_zone": "curated"},
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    bind.execute(
        sa.insert(mios_workflows).values(
            id=BIND_ID, mio_id=MIO_3_MONTHS_ID, workflow_id=WF_ID, created_at=NOW
        )
    )


def downgrade() -> None:
    op.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == BIND_ID))
    op.execute(sa.delete(workflows).where(workflows.c.id == WF_ID))
