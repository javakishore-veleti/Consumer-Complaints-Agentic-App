"""seed index_cfpb_chroma + index_cfpb_redis workflows, binds, AppEndpoints (D94)

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-16
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
CHROMA_WF = "87100dc6-f634-5bde-8539-d7175ca194ac"
REDIS_WF = "474e4e9a-5743-54c2-99f6-5ec860aa8c38"
CHROMA_BIND = "2a43462f-e29d-506c-9422-1a39dfdc16eb"
REDIS_BIND = "cc9d2cc5-088a-5d57-8227-4c2d2ef1cbc9"
CHROMA_EP = "1046ad4a-b4fd-509b-9bc3-9e8501ef86c0"
REDIS_EP = "bc449f1d-4055-5514-8794-c2ca504ebd99"

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
endpoints = sa.table(
    "app_endpoints",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("category", sa.String),
    sa.column("from_dataset_location_id", sa.String),
    sa.column("from_env_var_name", sa.String),
    sa.column("to_dataset_location_id", sa.String),
    sa.column("to_env_var_name", sa.String),
    sa.column("credentials_ref", sa.String),
    sa.column("description", sa.String),
    sa.column("enabled", sa.Boolean),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    bind = op.get_bind()
    for wf_id, name, backend, ep_name in (
        (CHROMA_WF, "index_cfpb_chroma", "chroma", "cfpb_index_mongo_to_chroma"),
        (REDIS_WF, "index_cfpb_redis", "redis", "cfpb_index_mongo_to_redis"),
    ):
        bind.execute(
            sa.insert(workflows).values(
                id=wf_id,
                workflow_name=name,
                engine_type="apache_airflow",
                engine_workflow_id=name,
                config={
                    "dataset_code": "CFPB",
                    "batch_size": 500,
                    "vector_backend": backend,
                    "app_endpoint_name": ep_name,
                },
                enabled=True,
                created_at=NOW,
                updated_at=NOW,
            )
        )
    bind.execute(
        sa.insert(mios_workflows).values(id=CHROMA_BIND, mio_id=ALL_MIO_ID, workflow_id=CHROMA_WF, created_at=NOW)
    )
    bind.execute(
        sa.insert(mios_workflows).values(id=REDIS_BIND, mio_id=ALL_MIO_ID, workflow_id=REDIS_WF, created_at=NOW)
    )
    bind.execute(
        sa.insert(endpoints).values(
            id=CHROMA_EP,
            name="cfpb_index_mongo_to_chroma",
            category="index",
            from_dataset_location_id=None,
            from_env_var_name="CCA_MONGO_COMPLAINTS_URL",
            to_dataset_location_id=None,
            to_env_var_name="CCA_CHROMA_URL",
            credentials_ref=None,
            description="Complaint Mongo → local Chroma (D94)",
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    bind.execute(
        sa.insert(endpoints).values(
            id=REDIS_EP,
            name="cfpb_index_mongo_to_redis",
            category="index",
            from_dataset_location_id=None,
            from_env_var_name="CCA_MONGO_COMPLAINTS_URL",
            to_dataset_location_id=None,
            to_env_var_name="CCA_REDIS_URL",
            credentials_ref=None,
            description="Complaint Mongo → local Redis Stack vectors (D94)",
            enabled=True,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    for ep in (CHROMA_EP, REDIS_EP):
        bind.execute(sa.delete(endpoints).where(endpoints.c.id == ep))
    for bid in (CHROMA_BIND, REDIS_BIND):
        bind.execute(sa.delete(mios_workflows).where(mios_workflows.c.id == bid))
    for wid in (CHROMA_WF, REDIS_WF):
        bind.execute(sa.delete(workflows).where(workflows.c.id == wid))
