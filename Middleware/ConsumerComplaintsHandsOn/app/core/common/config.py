"""Application settings. Read from environment variables each time, so tests can change them.

Schema names (DESIGN.md, section 3):

* consumer_comp_db            the consumer complaints area: dataset status and the data ingest log
* consumer_compl_intellect_db the Intellect app's own area
* consumer_comp_users_db      user management
* consumer_comp_admin_db      everything admin-related: the workflow registry and the catalog (D48)

SQLite has no real schemas, so each schema is a separate attached database file named after the schema.
On Postgres and similar databases they are real schemas.
"""

import os
from dataclasses import dataclass
from pathlib import Path

SCHEMA_COMPLAINTS = "consumer_comp_db"
SCHEMA_INTELLECT = "consumer_compl_intellect_db"
SCHEMA_USERS = "consumer_comp_users_db"
SCHEMA_ADMIN = "consumer_comp_admin_db"
ALL_SCHEMAS = (SCHEMA_COMPLAINTS, SCHEMA_INTELLECT, SCHEMA_USERS, SCHEMA_ADMIN)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    db_url: str
    data_dir: Path


def get_settings() -> Settings:
    """CCA_DATA_DIR: folder for the SQLite files (default: .data in the project).
    CCA_DB_URL: full SQLAlchemy URL; set it to use Postgres or another database instead of SQLite."""
    data_dir = Path(os.environ.get("CCA_DATA_DIR", PROJECT_ROOT / ".data")).resolve()
    db_url = os.environ.get("CCA_DB_URL", f"sqlite:///{data_dir}/operational.sqlite")
    return Settings(db_url=db_url, data_dir=data_dir)
