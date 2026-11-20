"""add wf_engine_data_json + wf_exec_data_json on app_workflows_exec_log (M57-0001 / #398)

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: Union[str, None] = "0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
TABLE = "app_workflows_exec_log"


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column("wf_engine_data_json", sa.JSON(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        TABLE,
        sa.Column("wf_exec_data_json", sa.JSON(), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column(TABLE, "wf_exec_data_json", schema=SCHEMA)
    op.drop_column(TABLE, "wf_engine_data_json", schema=SCHEMA)
