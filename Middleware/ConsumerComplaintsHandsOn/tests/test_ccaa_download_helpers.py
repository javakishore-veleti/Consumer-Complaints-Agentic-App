"""Unit tests for Middleware/Airflow-dags/ccaa helpers (D63)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy import text

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import download as download_mod  # noqa: E402
from ccaa import db_reader  # noqa: E402


def test_download_url_to_path_writes_bytes(tmp_path: Path):
    dest = tmp_path / "complaints.csv.zip"
    fake = MagicMock()
    fake.read.side_effect = [b"abc", b""]
    fake.__enter__ = lambda s: s
    fake.__exit__ = MagicMock(return_value=False)
    with patch.object(download_mod.urllib.request, "urlopen", return_value=fake) as opener:
        out = download_mod.download_url_to_path("https://example.com/complaints.csv.zip", dest)
    opener.assert_called_once()
    assert out == dest
    assert dest.read_bytes() == b"abc"


def test_download_url_to_path_rejects_http_error(tmp_path: Path):
    import urllib.error

    dest = tmp_path / "x.zip"
    with patch.object(
        download_mod.urllib.request,
        "urlopen",
        side_effect=urllib.error.HTTPError("https://x", 404, "no", hdrs=None, fp=None),
    ):
        with pytest.raises(urllib.error.HTTPError):
            download_mod.download_url_to_path("https://x", dest)


def _seed_min_admin(engine: sa.Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("ATTACH DATABASE ':memory:' AS consumer_comp_admin_db"))
        conn.execute(
            text(
                """
                CREATE TABLE consumer_comp_admin_db.app_workflows_exec_log (
                    id TEXT PRIMARY KEY,
                    config_used TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE consumer_comp_admin_db.datasets (
                    id TEXT PRIMARY KEY,
                    code TEXT UNIQUE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE consumer_comp_admin_db.datasets_location (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    location_type TEXT,
                    path TEXT,
                    local_env_var_name TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO consumer_comp_admin_db.app_workflows_exec_log (id, config_used) "
                "VALUES ('exec-1', '{\"dataset_code\": \"CFPB\"}')"
            )
        )
        conn.execute(text("INSERT INTO consumer_comp_admin_db.datasets (id, code) VALUES ('ds-1', 'CFPB')"))
        conn.execute(
            text(
                "INSERT INTO consumer_comp_admin_db.datasets_location "
                "(id, dataset_id, location_type, path, local_env_var_name) VALUES "
                "('loc-h', 'ds-1', 'http', 'https://files.consumerfinance.gov/ccdb/complaints.csv.zip', NULL), "
                "('loc-l', 'ds-1', 'local', NULL, 'LOCAL_DATA_PATH_CFPB')"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE consumer_comp_admin_db.app_endpoints (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE,
                    category TEXT,
                    from_dataset_location_id TEXT,
                    from_env_var_name TEXT,
                    to_dataset_location_id TEXT,
                    to_env_var_name TEXT,
                    credentials_ref TEXT,
                    enabled INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO consumer_comp_admin_db.app_endpoints "
                "(id, name, category, from_dataset_location_id, from_env_var_name, "
                "to_dataset_location_id, to_env_var_name, credentials_ref, enabled) VALUES "
                "('ep-1', 'cfpb_source_http_to_local', 'source', 'loc-h', NULL, 'loc-l', NULL, NULL, 1)"
            )
        )


def test_db_reader_loads_config_and_locations():
    engine = sa.create_engine("sqlite://")
    _seed_min_admin(engine)
    with engine.connect() as conn:
        cfg = db_reader.load_execution_config(conn, "exec-1")
        locs = db_reader.load_dataset_locations(conn, cfg["dataset_code"])
    assert cfg == {"dataset_code": "CFPB"}
    assert locs["http"]["path"].endswith("complaints.csv.zip")
    assert locs["local"]["local_env_var_name"] == "LOCAL_DATA_PATH_CFPB"


def test_db_reader_resolves_app_endpoint(tmp_path: Path):
    engine = sa.create_engine("sqlite://")
    _seed_min_admin(engine)
    landing = tmp_path / "land"
    landing.mkdir()
    with engine.connect() as conn:
        resolved = db_reader.resolve_app_endpoint(
            conn,
            "cfpb_source_http_to_local",
            getenv=lambda k, default=None: str(landing) if k == "LOCAL_DATA_PATH_CFPB" else default,
            get_variable=lambda k: "",
        )
    assert resolved["from"]["kind"] == "path"
    assert "complaints.csv.zip" in resolved["from"]["path"]
    assert resolved["to"]["kind"] == "env"
    assert resolved["to"]["value"] == str(landing)
