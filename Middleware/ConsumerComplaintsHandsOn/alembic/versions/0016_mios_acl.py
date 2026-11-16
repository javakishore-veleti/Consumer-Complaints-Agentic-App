"""create mios_acl and seed internal for All + 3 months (D89)

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-16
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-all-internal")
ACL_ALL_ID = "814a15b9-246b-5f8f-baef-a3f75a946a72"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-3m-internal")
ACL_3M_ID = "c57c33d4-f3c6-50a9-b614-5f095d4d7134"

_when = sa.DateTime(timezone=True)
mios_acl = sa.table(
    "mios_acl",
    sa.column("id", sa.String),
    sa.column("mio_id", sa.String),
    sa.column("audience", sa.String),
    sa.column("created_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    op.create_table(
        "mios_acl",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),
        sa.Column("audience", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mio_id", "audience", name="uq_mios_acl_mio_audience"),
        sa.CheckConstraint(
            "audience IN ('internal', 'partner', 'user')",
            name="ck_mios_acl_audience",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_acl_mio_id", "mios_acl", ["mio_id"], schema=SCHEMA)
    op.bulk_insert(
        mios_acl,
        [
            {"id": ACL_ALL_ID, "mio_id": ALL_MIO_ID, "audience": "internal", "created_at": NOW},
            {"id": ACL_3M_ID, "mio_id": MIO_3_MONTHS_ID, "audience": "internal", "created_at": NOW},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_mios_acl_mio_id", table_name="mios_acl", schema=SCHEMA)
    op.drop_table("mios_acl", schema=SCHEMA)
