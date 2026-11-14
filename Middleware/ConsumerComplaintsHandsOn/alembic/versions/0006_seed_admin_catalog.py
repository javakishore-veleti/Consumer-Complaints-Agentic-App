"""seed the admin catalog: the CFPB dataset, its two locations and four labelled MIOs

Only data that is the same in every environment is seeded. The local location holds only the NAME of the
environment variable that each environment sets; no machine path is stored (D57).

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)
HTTP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"

# Fixed ids so a downgrade removes exactly these rows. The dataset, the two locations and the four MIO ids are
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0036/<name>") with <name> dataset_cfpb, loc_http, loc_local and
# mio_3, mio_6, mio_9, mio_12. The four mios_datasets ids are arbitrary fixed UUIDs, not derived from a name.
DATASET_ID = "5187ad0c-d8ed-56ac-829d-e49313c16dbf"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"
MIOS = (  # (mio id, mios_datasets id, months)
    ("a10fbfe0-ac03-5f3f-8d20-5132d470b03a", "f4baf6a8-1b8c-5145-b016-9a870bdecd6f", 3),
    ("b0f8bb64-be6b-5773-9f4c-3552ca36dc37", "012a8fd8-3f34-5843-b0ca-f4cf42f070a4", 6),
    ("f34fa9f1-e361-5fc0-98e0-f557bb561176", "47081de5-5db8-5c50-8b9a-6597d5624a84", 9),
    ("eb33e86c-5972-5d25-95aa-87625bec004d", "47fa4276-bc79-5e7b-a961-c33016e56199", 12),
)

_when = sa.DateTime(timezone=True)
datasets = sa.table(
    "datasets",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("code", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
locations = sa.table(
    "datasets_location",
    sa.column("id", sa.String),
    sa.column("dataset_id", sa.String),
    sa.column("location_type", sa.String),
    sa.column("path", sa.String),
    sa.column("local_env_var_name", sa.String),
    sa.column("credentials_ref", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
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


def upgrade() -> None:
    op.bulk_insert(
        datasets,
        [
            {
                "id": DATASET_ID,
                "name": "cfpb_consumer_complaints",
                "code": "CFPB",
                "description": "The full CFPB Consumer Complaint Database file",
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        locations,
        [
            {
                "id": HTTP_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "http",
                "path": HTTP_URL,
                "local_env_var_name": None,
                "credentials_ref": None,
                "description": "The public download of the CFPB file",
                "created_at": NOW,
                "updated_at": NOW,
            },
            {
                "id": LOCAL_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "local",
                "path": None,
                "local_env_var_name": "LOCAL_DATA_PATH_CFPB",
                "credentials_ref": None,
                "description": "Where the file is kept; each environment sets the variable",
                "created_at": NOW,
                "updated_at": NOW,
            },
        ],
    )
    op.bulk_insert(
        mios,
        [
            {
                "id": mio_id,
                "name": f"Customer complaints {months} months 2026",
                "description": "A label only. The data is what mios_datasets links.",
                "created_at": NOW,
                "updated_at": NOW,
            }
            for mio_id, _link_id, months in MIOS
        ],
    )
    op.bulk_insert(
        mios_datasets,
        [
            {
                "id": link_id,
                "mio_id": mio_id,
                "dataset_id": DATASET_ID,
                "dataset_location_id": HTTP_LOCATION_ID,
                "created_at": NOW,
            }
            for mio_id, link_id, _months in MIOS
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(mios_datasets).where(mios_datasets.c.id.in_([link_id for _m, link_id, _n in MIOS])))
    op.execute(sa.delete(mios).where(mios.c.id.in_([mio_id for mio_id, _l, _n in MIOS])))
    op.execute(sa.delete(locations).where(locations.c.id.in_([HTTP_LOCATION_ID, LOCAL_LOCATION_ID])))
    op.execute(sa.delete(datasets).where(datasets.c.id == DATASET_ID))
