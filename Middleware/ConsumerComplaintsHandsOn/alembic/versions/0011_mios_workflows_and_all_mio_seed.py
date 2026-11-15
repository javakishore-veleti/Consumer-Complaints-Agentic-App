"""create mios_workflows and seed All MIO + bindings (M03-0018 / D84)

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-15
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)

# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m03-0018/mio-all-2026")
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m03-0018/mios-datasets-all-2026")
ALL_MIOS_DATASETS_ID = "038915b0-1a19-50e9-9333-e49f3816a0f8"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m03-0018/mios-workflows-all-download")
MW_ALL_DOWNLOAD_ID = "c23808b9-4e57-5a5b-b301-78dec5ac839e"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m03-0018/mios-workflows-3m-filter")
MW_3M_FILTER_ID = "edd79fde-5736-5655-9d00-c52bfe172c1f"

DATASET_ID = "5187ad0c-d8ed-56ac-829d-e49313c16dbf"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
DOWNLOAD_CFPB_ALL_WORKFLOW_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
FILTER_CFPB_3_MONTHS_WORKFLOW_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"

_when = sa.DateTime(timezone=True)
mios = sa.table(
    "mios",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
mios_datasets = sa.table(
    "mios_datasets",
    sa.column("id", sa.String),
    sa.column("mio_id", sa.String),
    sa.column("dataset_id", sa.String),
    sa.column("dataset_location_id", sa.String),
    sa.column("created_at", _when),
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
    op.create_table(
        "mios_workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mio_id", "workflow_id", name="uq_mios_workflows_mio_workflow"),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_workflows_mio_id", "mios_workflows", ["mio_id"], schema=SCHEMA)
    op.create_index("ix_mios_workflows_workflow_id", "mios_workflows", ["workflow_id"], schema=SCHEMA)

    op.bulk_insert(
        mios,
        [
            {
                "id": ALL_MIO_ID,
                "name": "Customer complaints all 2026",
                "description": "A label only. The data is what mios_datasets links.",
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        mios_datasets,
        [
            {
                "id": ALL_MIOS_DATASETS_ID,
                "mio_id": ALL_MIO_ID,
                "dataset_id": DATASET_ID,
                "dataset_location_id": HTTP_LOCATION_ID,
                "created_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        mios_workflows,
        [
            {
                "id": MW_ALL_DOWNLOAD_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": DOWNLOAD_CFPB_ALL_WORKFLOW_ID,
                "created_at": NOW,
            },
            {
                "id": MW_3M_FILTER_ID,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": FILTER_CFPB_3_MONTHS_WORKFLOW_ID,
                "created_at": NOW,
            },
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(mios_workflows).where(mios_workflows.c.id.in_([MW_ALL_DOWNLOAD_ID, MW_3M_FILTER_ID])))
    op.execute(sa.delete(mios_datasets).where(mios_datasets.c.id == ALL_MIOS_DATASETS_ID))
    op.execute(sa.delete(mios).where(mios.c.id == ALL_MIO_ID))
    op.drop_index("ix_mios_workflows_workflow_id", table_name="mios_workflows", schema=SCHEMA)
    op.drop_index("ix_mios_workflows_mio_id", table_name="mios_workflows", schema=SCHEMA)
    op.drop_table("mios_workflows", schema=SCHEMA)
