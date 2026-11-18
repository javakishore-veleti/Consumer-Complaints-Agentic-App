"""Bind ingest wrapper + index workflows to 3-month MIO (M17-0001)

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-17
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)

MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
WRAPPER_WF = "e64365bd-98f4-52a4-a3bc-e26455915c6b"
PGVECTOR_WF = "68a0fa8a-825c-53f1-864f-5db167a339a0"
CHROMA_WF = "87100dc6-f634-5bde-8539-d7175ca194ac"
REDIS_WF = "474e4e9a-5743-54c2-99f6-5ec860aa8c38"

# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m17-0001/mios-workflows-3m-…")
MW_WRAPPER = "c706e8f2-44e1-5f26-95a7-25b4f82b5659"
MW_PGVECTOR = "a31ad1f2-0b5f-56e0-9467-7e3470b128dd"
MW_CHROMA = "451d226d-7563-5cbe-8f34-92c44ae752ee"
MW_REDIS = "ce69196c-d80e-5a31-b0ca-4839db66e620"

_when = sa.DateTime(timezone=True)
mios_workflows = sa.table(
    "mios_workflows",
    sa.column("id", sa.String),
    sa.column("mio_id", sa.String),
    sa.column("workflow_id", sa.String),
    sa.column("created_at", _when),
    schema=SCHEMA,
)

ROWS = [
    (MW_WRAPPER, WRAPPER_WF),
    (MW_PGVECTOR, PGVECTOR_WF),
    (MW_CHROMA, CHROMA_WF),
    (MW_REDIS, REDIS_WF),
]


def upgrade() -> None:
    op.bulk_insert(
        mios_workflows,
        [
            {
                "id": binding_id,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": workflow_id,
                "created_at": NOW,
            }
            for binding_id, workflow_id in ROWS
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.delete(mios_workflows).where(
            mios_workflows.c.id.in_([binding_id for binding_id, _ in ROWS])
        )
    )
