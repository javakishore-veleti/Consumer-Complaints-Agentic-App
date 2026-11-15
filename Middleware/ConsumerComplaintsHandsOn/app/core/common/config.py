"""Application settings. Read from environment variables each time, so tests can change them.

Schema names (DESIGN.md, section 3):

* consumer_comp_db            the consumer complaints area (no tables at head after D73; also the MongoDB database name)
* consumer_compl_intellect_db the Intellect app's own area
* consumer_comp_users_db      user management
* consumer_comp_admin_db      everything admin-related: the workflow registry and the catalog (D48)

SQLite has no real schemas, so each schema is a separate attached database file named after the schema.
On Postgres and similar databases they are real schemas.

Operational/admin store backends (D75): sqlite (default), postgres (CCA_DB_URL), mongodb (CCA_MONGO_OPERATIONAL_URL).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

SCHEMA_COMPLAINTS = "consumer_comp_db"
SCHEMA_INTELLECT = "consumer_compl_intellect_db"
SCHEMA_USERS = "consumer_comp_users_db"
SCHEMA_ADMIN = "consumer_comp_admin_db"
ALL_SCHEMAS = (SCHEMA_COMPLAINTS, SCHEMA_INTELLECT, SCHEMA_USERS, SCHEMA_ADMIN)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OperationalStore = Literal["sqlite", "postgres", "mongodb"]
_VALID_STORES = frozenset({"sqlite", "postgres", "mongodb"})


@dataclass(frozen=True)
class Settings:
    db_url: str
    data_dir: Path
    operational_store: OperationalStore = "sqlite"
    mongo_operational_url: str | None = None
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
    CCA_DB_URL: full SQLAlchemy URL; set it to use Postgres or another SQL database instead of SQLite.
    CCA_OPERATIONAL_STORE: optional sqlite | postgres | mongodb (D75).
    CCA_MONGO_OPERATIONAL_URL: required when the operational store is mongodb (D75; DAOs in #119).
    CCA_CALLBACK_SECRET: the shared secret Airflow sends with every callback (D59). Unset or blank means not
    configured, and then every protected endpoint answers 401.
    CCA_AIRFLOW_API_*: Airflow 3 REST base URL and basic credentials for Variables upsert (D42)."""
    data_dir = Path(os.environ.get("CCA_DATA_DIR", PROJECT_ROOT / ".data")).resolve()
    raw_db_url = os.environ.get("CCA_DB_URL", "").strip()
    explicit_store = os.environ.get("CCA_OPERATIONAL_STORE", "").strip() or None
    mongo_url = os.environ.get("CCA_MONGO_OPERATIONAL_URL", "").strip() or None

    # Resolve operational_store (D75). Logic stays inside get_settings so helpers do not take bare str (D37).
    if explicit_store:
        store_name = explicit_store.lower()
        if store_name not in _VALID_STORES:
            raise ValueError(
                f"CCA_OPERATIONAL_STORE must be one of sqlite, postgres, mongodb; got {explicit_store!r}"
            )
        store: OperationalStore = store_name  # type: ignore[assignment]
    elif not raw_db_url:
        store = "sqlite"
    else:
        scheme = urlparse(raw_db_url).scheme or ""
        dialect = scheme.split("+", 1)[0].lower()
        if dialect == "sqlite":
            store = "sqlite"
        elif dialect in ("postgresql", "postgres"):
            store = "postgres"
        elif dialect.startswith("mongodb"):
            store = "mongodb"
        else:
            raise ValueError(
                f"CCA_DB_URL dialect {dialect!r} is not a known operational store "
                "(expected sqlite, postgresql/postgres, or mongodb)"
            )

    if store == "mongodb":
        if not mongo_url:
            raise ValueError(
                "CCA_MONGO_OPERATIONAL_URL is required when CCA_OPERATIONAL_STORE=mongodb (D75)"
            )
        db_url = raw_db_url or f"sqlite:///{data_dir}/operational.sqlite"
    elif store == "postgres":
        if not raw_db_url:
            raise ValueError(
                "CCA_DB_URL is required when CCA_OPERATIONAL_STORE=postgres (D75)"
            )
        pg_scheme = urlparse(raw_db_url).scheme or ""
        pg_dialect = pg_scheme.split("+", 1)[0].lower()
        if pg_dialect not in ("postgresql", "postgres"):
            raise ValueError(
                "CCA_DB_URL must be a Postgres SQLAlchemy URL when the operational store is postgres"
            )
        db_url = raw_db_url
    else:
        db_url = raw_db_url or f"sqlite:///{data_dir}/operational.sqlite"

    callback_secret = os.environ.get("CCA_CALLBACK_SECRET", "").strip() or None
    base = os.environ.get("CCA_AIRFLOW_API_BASE_URL", "http://127.0.0.1:8080").strip().rstrip("/")
    user = os.environ.get("CCA_AIRFLOW_API_USERNAME", "airflow").strip() or "airflow"
    password = os.environ.get("CCA_AIRFLOW_API_PASSWORD", "airflow")  # keep as configured; default airflow
    upsert_path = PROJECT_ROOT.parents[1] / "CICD" / "Local" / "airflow" / "Airflow_Variables_Upsert.txt"
    return Settings(
        db_url=db_url,
        data_dir=data_dir,
        operational_store=store,
        mongo_operational_url=mongo_url if store == "mongodb" else None,
        callback_secret=callback_secret,
        airflow_api_base_url=base or "http://127.0.0.1:8080",
        airflow_api_username=user,
        airflow_api_password=password,
        airflow_variables_upsert_path=upsert_path,
    )
