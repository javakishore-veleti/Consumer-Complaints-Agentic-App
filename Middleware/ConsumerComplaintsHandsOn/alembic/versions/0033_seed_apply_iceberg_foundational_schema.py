"""seed apply_iceberg_foundational_schema workflow + 3m MIO bind (M58-0001 / #400)

Revision ID: 0033
Revises: 0032
Create Date: 2026-11-20
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: Union[str, None] = "0032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)

MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m58-0001/apply_iceberg_foundational_schema")
WF_ID = "6b4c8d84-b407-55c6-841b-114d986db58e"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m58-0001/mios-workflows-3m-apply-iceberg-foundational")
BIND_ID = "570402c8-47f9-5636-a910-4c5c129fd989"

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
            workflow_name="apply_iceberg_foundational_schema",
            engine_type="apache_airflow",
            engine_workflow_id="apply_iceberg_foundational_schema",
            config={
                "dataset_code": "CFPB",
                "dataset_slice": "3m",
                "schema_kind": "foundational",
                "store": "iceberg",
                "zones": ["raw", "refined", "taxonomy", "curated"],
            },
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    bind.execute(
        sa.insert(mios_workflows).values(
            id=BIND_ID,
            mio_id=MIO_3_MONTHS_ID,
            workflow_id=WF_ID,
            created_at=NOW,
        )
    )


def downgrade() -> None:
    op.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == BIND_ID))
    op.execute(sa.delete(workflows).where(workflows.c.id == WF_ID))
