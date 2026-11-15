"""Application settings. Read from environment variables each time, so tests can change them.

Schema names (DESIGN.md, section 3):

* consumer_comp_db            the consumer complaints area (no tables at head after D73; also the MongoDB database name)
* consumer_compl_intellect_db the Intellect app's own area
* consumer_comp_users_db      user management
* consumer_comp_admin_db      everything admin-related: the workflow registry and the catalog (D48)

SQLite has no real schemas, so each schema is a separate attached database file named after the schema.
On Postgres and similar databases they are real schemas.
"""

import os
from dataclasses import dataclass, field
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
    callback_secret: str | None = field(default=None, repr=False)
    airflow_api_base_url: str = "http://127.0.0.1:8080"
    airflow_api_username: str = "airflow"
    airflow_api_password: str = field(default="airflow", repr=False)
    airflow_variables_upsert_path: Path = field(
        default_factory=lambda: PROJECT_ROOT.parents[1]
        / "CICD"
        / "Local"
        / "airflow"
        / "Airflow_Variables_Upsert.txt"
    )


def get_settings() -> Settings:
    """CCA_DATA_DIR: folder for the SQLite files (default: .data in the project).
    CCA_DB_URL: full SQLAlchemy URL; set it to use Postgres or another database instead of SQLite.
    CCA_CALLBACK_SECRET: the shared secret Airflow sends with every callback (D59). Unset or blank means not
    configured, and then every protected endpoint answers 401.
    CCA_AIRFLOW_API_*: Airflow 3 REST base URL and basic credentials for Variables upsert (D42)."""
    data_dir = Path(os.environ.get("CCA_DATA_DIR", PROJECT_ROOT / ".data")).resolve()
    db_url = os.environ.get("CCA_DB_URL", f"sqlite:///{data_dir}/operational.sqlite")
    callback_secret = os.environ.get("CCA_CALLBACK_SECRET", "").strip() or None
    base = os.environ.get("CCA_AIRFLOW_API_BASE_URL", "http://127.0.0.1:8080").strip().rstrip("/")
    user = os.environ.get("CCA_AIRFLOW_API_USERNAME", "airflow").strip() or "airflow"
    password = os.environ.get("CCA_AIRFLOW_API_PASSWORD", "airflow")  # keep as configured; default airflow
    upsert_path = PROJECT_ROOT.parents[1] / "CICD" / "Local" / "airflow" / "Airflow_Variables_Upsert.txt"
    return Settings(
        db_url=db_url,
        data_dir=data_dir,
        callback_secret=callback_secret,
        airflow_api_base_url=base or "http://127.0.0.1:8080",
        airflow_api_username=user,
        airflow_api_password=password,
        airflow_variables_upsert_path=upsert_path,
    )
