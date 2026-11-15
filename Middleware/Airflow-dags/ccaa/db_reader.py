"""Read-only operational DB access for Airflow DAGs. Must not import app.*."""

from __future__ import annotations

import json
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

SCHEMA = "consumer_comp_admin_db"


def make_engine(db_url: str) -> Engine:
    engine = sa.create_engine(db_url)
    if db_url.startswith("sqlite:///"):
        # Prefer Postgres when Airflow runs in Docker (D63). SQLite fallback: ATTACH admin file.
        db_path = Path(db_url.removeprefix("sqlite:///"))
        admin = db_path.parent / f"{SCHEMA}.sqlite"

        @sa.event.listens_for(engine, "connect")
        def _attach(dbapi_conn, _):  # noqa: ANN001
            if admin.exists():
                dbapi_conn.execute(f"ATTACH DATABASE '{admin}' AS {SCHEMA}")

    return engine


def load_execution_config(conn: Connection, execution_id: str) -> dict:
    row = conn.execute(
        text(
            f"SELECT config_used FROM {SCHEMA}.app_workflows_exec_log WHERE id = :id"
        ),
        {"id": execution_id},
    ).one_or_none()
    if row is None:
        raise LookupError(f"execution not found: {execution_id}")
    raw = row[0]
    if raw is None:
        raise ValueError("execution has no config_used")
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def load_dataset_locations(conn: Connection, dataset_code: str) -> dict:
    ds = conn.execute(
        text(f"SELECT id FROM {SCHEMA}.datasets WHERE code = :code"),
        {"code": dataset_code},
    ).one_or_none()
    if ds is None:
        raise LookupError(f"dataset not found: {dataset_code}")
    rows = conn.execute(
        text(
            f"SELECT location_type, path, local_env_var_name FROM {SCHEMA}.datasets_location "
            "WHERE dataset_id = :dataset_id"
        ),
        {"dataset_id": ds[0]},
    ).all()
    out: dict = {}
    for location_type, path, local_env_var_name in rows:
        out[location_type] = {"path": path, "local_env_var_name": local_env_var_name}
    if "http" not in out or not out["http"].get("path"):
        raise ValueError("dataset missing http source location")
    if "local" not in out or not out["local"].get("local_env_var_name"):
        raise ValueError("dataset missing local landing location")
    return out


def resolve_landing_dir(local_env_var_name: str, getenv, get_variable) -> Path:
    value = (getenv(local_env_var_name) or "").strip() or (get_variable(local_env_var_name) or "").strip()
    if not value:
        raise RuntimeError(f"{local_env_var_name} is not set in the environment or as an Airflow Variable")
    return Path(value)
