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


def load_app_endpoint_by_name(conn: Connection, name: str) -> dict:
    """Load one enabled app_endpoints row by name (D85 / D87)."""
    row = conn.execute(
        text(
            f"SELECT id, name, category, from_dataset_location_id, from_env_var_name, "
            f"to_dataset_location_id, to_env_var_name, credentials_ref, enabled "
            f"FROM {SCHEMA}.app_endpoints WHERE name = :name"
        ),
        {"name": name},
    ).one_or_none()
    if row is None:
        raise LookupError(f"app_endpoint not found: {name}")
    keys = (
        "id",
        "name",
        "category",
        "from_dataset_location_id",
        "from_env_var_name",
        "to_dataset_location_id",
        "to_env_var_name",
        "credentials_ref",
        "enabled",
    )
    ep = dict(zip(keys, row, strict=True))
    if not ep["enabled"]:
        raise ValueError(f"app_endpoint is disabled: {name}")
    return ep


def load_location_by_id(conn: Connection, location_id: str) -> dict:
    row = conn.execute(
        text(
            f"SELECT id, location_type, path, local_env_var_name FROM {SCHEMA}.datasets_location "
            "WHERE id = :id"
        ),
        {"id": location_id},
    ).one_or_none()
    if row is None:
        raise LookupError(f"datasets_location not found: {location_id}")
    return {
        "id": row[0],
        "location_type": row[1],
        "path": row[2],
        "local_env_var_name": row[3],
    }


def resolve_side(
    conn: Connection,
    *,
    location_id: str | None,
    env_var_name: str | None,
    getenv,
    get_variable,
) -> dict:
    """Resolve one AppEndpoint side to {kind, path|env_var_name, value?}."""
    if location_id and env_var_name:
        raise ValueError("side cannot set both location_id and env_var_name")
    if location_id:
        loc = load_location_by_id(conn, location_id)
        if loc.get("path"):
            return {"kind": "path", "path": loc["path"], "location_type": loc["location_type"]}
        if loc.get("local_env_var_name"):
            name = loc["local_env_var_name"]
            return {
                "kind": "env",
                "env_var_name": name,
                "value": str(resolve_landing_dir(name, getenv, get_variable)),
                "location_type": loc["location_type"],
            }
        raise ValueError(f"location {location_id} has neither path nor local_env_var_name")
    if env_var_name:
        value = (getenv(env_var_name) or "").strip() or (get_variable(env_var_name) or "").strip()
        if not value:
            raise RuntimeError(f"{env_var_name} is not set in the environment or as an Airflow Variable")
        return {"kind": "env", "env_var_name": env_var_name, "value": value}
    raise ValueError("side requires location_id or env_var_name")


def resolve_app_endpoint(
    conn: Connection,
    name: str,
    *,
    getenv,
    get_variable,
) -> dict:
    """Resolve AppEndpoint name to from/to sides (D87)."""
    ep = load_app_endpoint_by_name(conn, name)
    frm = resolve_side(
        conn,
        location_id=ep["from_dataset_location_id"],
        env_var_name=ep["from_env_var_name"],
        getenv=getenv,
        get_variable=get_variable,
    )
    to = resolve_side(
        conn,
        location_id=ep["to_dataset_location_id"],
        env_var_name=ep["to_env_var_name"],
        getenv=getenv,
        get_variable=get_variable,
    )
    return {"endpoint": ep, "from": frm, "to": to}
