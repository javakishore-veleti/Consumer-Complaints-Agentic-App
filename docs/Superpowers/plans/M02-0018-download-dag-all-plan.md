# M02-0018 (#57) Download DAG for the All dataset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Airflow DAG `download_cfpb_all` that reads `execution_id` from conf, loads CFPB http+local locations from the operational DB via `CCA_DB_URL`, downloads `complaints.csv.zip` into the resolved landing directory, and register the workflow in `app_workflows` (migration `0008`).

**Architecture:** Standalone helpers under `Middleware/Airflow-dags/ccaa/` (no `app.*` imports). DAG file imports those helpers. Catalog source/landing rules are D63. Status callbacks are no-op TODO hooks for #59.

**Tech Stack:** Apache Airflow 3.4.0, SQLAlchemy (`text`), stdlib `urllib.request`, Alembic, pytest, `uv`.

Spec: `docs/Superpowers/specs/M02-0018-download-dag-all-design.md`. Decisions: D11, D42, D43, D44, D51, D52, D54, D57, D62, D63 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- Paths are relative to the **repository root** unless a step says otherwise. App tests run from `Middleware/ConsumerComplaintsHandsOn` with `uv run pytest`.
- DAGs live only in `Middleware/Airflow-dags` (D44). Do **not** import `app.*` from any file under that folder.
- `engine_type` is `apache_airflow` (D52), never the shorthand `airflow`.
- DAG id and `engine_workflow_id` are exactly `download_cfpb_all`.
- Airflow may **read** the operational DB only (D11 / D51); never write status into tables from this story.
- Scratch / throwaway under `runtime_data/tmp/` (never commit).
- Commit with `/ccaa-commit-push 57` only (never a raw `git commit`).

## File Structure

| File | Responsibility |
|---|---|
| `Middleware/Airflow-dags/ccaa/__init__.py` | Package marker |
| `Middleware/Airflow-dags/ccaa/download.py` | Stream HTTP URL to a local path |
| `Middleware/Airflow-dags/ccaa/db_reader.py` | Read-only exec-log + dataset location queries |
| `Middleware/Airflow-dags/download_cfpb_all.py` | DAG definition |
| `Middleware/ConsumerComplaintsHandsOn/alembic/versions/0008_seed_download_cfpb_all_workflow.py` | Seed `app_workflows` |
| `Middleware/ConsumerComplaintsHandsOn/.env.example` | Document `LOCAL_DATA_PATH_CFPB` |
| `CICD/Local/airflow/Airflow_Variables_Upsert.txt` | Add `LOCAL_DATA_PATH_CFPB` |
| `CICD/Local/airflow/docker-compose.yaml` | Comment (+ optional volume) for landing path / Postgres note |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` / `ARCHITECTURE.md` | Point at D63 / DAG if not already |
| `tests/test_ccaa_download_helpers.py` | Unit tests for download + db_reader |
| `tests/test_download_cfpb_all_dag_file.py` | Path / dag_id presence |
| `tests/test_schema.py` | Extend for migration `0008` seed |

---

### Task 1: Download helper and DB reader (TDD)

**Files:**
- Create: `Middleware/Airflow-dags/ccaa/__init__.py`, `Middleware/Airflow-dags/ccaa/download.py`, `Middleware/Airflow-dags/ccaa/db_reader.py`
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_ccaa_download_helpers.py`

**Interfaces:**
- Produces:
  - `download_url_to_path(url: str, dest: Path) -> Path`
  - `resolve_env_or_variable(name: str, get_variable) -> str` (optional thin helper; `get_variable` is a callable `str -> str` so tests avoid Airflow)
  - `load_execution_config(conn, execution_id: str) -> dict`
  - `load_dataset_locations(conn, dataset_code: str) -> dict` with keys `"http"` / `"local"`
  - `make_engine(db_url: str)` for SQLAlchemy engine (Postgres as-is; SQLite attaches admin schema file when URL is `sqlite:///.../operational.sqlite`)

- [ ] **Step 1: Write the failing tests**

Create `Middleware/ConsumerComplaintsHandsOn/tests/test_ccaa_download_helpers.py`:

```python
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


def test_db_reader_loads_config_and_locations():
    engine = sa.create_engine("sqlite://")
    _seed_min_admin(engine)
    with engine.connect() as conn:
        cfg = db_reader.load_execution_config(conn, "exec-1")
        locs = db_reader.load_dataset_locations(conn, cfg["dataset_code"])
    assert cfg == {"dataset_code": "CFPB"}
    assert locs["http"]["path"].endswith("complaints.csv.zip")
    assert locs["local"]["local_env_var_name"] == "LOCAL_DATA_PATH_CFPB"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_download_helpers.py -v
```

Expected: FAIL (import / module not found).

- [ ] **Step 3: Implement minimal helpers**

`Middleware/Airflow-dags/ccaa/__init__.py` — empty.

`Middleware/Airflow-dags/ccaa/download.py`:

```python
"""HTTP download helper for Airflow DAGs (stdlib only)."""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path


def download_url_to_path(url: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp:
        with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    tmp_path.replace(dest)
    return dest
```

`Middleware/Airflow-dags/ccaa/db_reader.py`:

```python
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
```

Adjust the download mock if `urlopen` context-manager behavior differs — keep the test green with the smallest change.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_download_helpers.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
/ccaa-commit-push 57
```

---

### Task 2: DAG file and path test (TDD)

**Files:**
- Create: `Middleware/Airflow-dags/download_cfpb_all.py`
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_download_cfpb_all_dag_file.py`
- Modify: `CICD/Local/airflow/docker-compose.yaml` (header comments only unless adding a documented data volume)

**Interfaces:**
- Consumes: `ccaa.download.download_url_to_path`, `ccaa.db_reader.*`
- Produces: Airflow DAG with `dag_id="download_cfpb_all"`; task callable that needs conf `execution_id`

- [ ] **Step 1: Write the failing path test**

```python
"""D44 / D63: download_cfpb_all DAG file is present under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "download_cfpb_all.py"


def test_download_cfpb_all_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="download_cfpb_all"' in text or "dag_id='download_cfpb_all'" in text
    assert "TODO story #59" in text
    assert "from app." not in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_download_cfpb_all_dag_file.py -v
```

Expected: FAIL (file missing).

- [ ] **Step 3: Implement the DAG**

`Middleware/Airflow-dags/download_cfpb_all.py`:

```python
"""Download the full CFPB complaints zip (All dataset). D51 / D63. Status callbacks: story #59."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

from ccaa.db_reader import (
    load_dataset_locations,
    load_execution_config,
    make_engine,
    resolve_landing_dir,
)
from ccaa.download import download_url_to_path


def _notify_started(execution_id: str) -> None:
    # TODO story #59: POST /callbacks/workflow-executions/{execution_id}/status status=started
    return None


def _notify_finished(execution_id: str, ok: bool) -> None:
    # TODO story #59: POST ... status=completed|failed
    return None


def resolve_and_download(**context) -> str:
    conf = context.get("dag_run").conf or {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")

    _notify_started(execution_id)
    try:
        db_url = Variable.get("CCA_DB_URL")
        engine = make_engine(db_url)
        with engine.connect() as conn:
            cfg = load_execution_config(conn, execution_id)
            code = cfg.get("dataset_code")
            if not code:
                raise ValueError("config_used.dataset_code is required")
            locs = load_dataset_locations(conn, code)

        url = locs["http"]["path"]
        landing = resolve_landing_dir(
            locs["local"]["local_env_var_name"],
            getenv=os.getenv,
            get_variable=Variable.get,
        )
        name = Path(urlparse(url).path).name or "complaints.csv.zip"
        dest = landing / name
        download_url_to_path(url, dest)
        _notify_finished(execution_id, True)
        return str(dest)
    except Exception:
        _notify_finished(execution_id, False)
        raise


with DAG(
    dag_id="download_cfpb_all",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "download"],
) as dag:
    PythonOperator(
        task_id="resolve_and_download",
        python_callable=resolve_and_download,
    )
```

Add a short compose header note that for Docker Airflow, set `CCA_DB_URL` to Postgres the containers can reach (D63), and set `LOCAL_DATA_PATH_CFPB` to a path mounted writable into the worker.

- [ ] **Step 4: Run tests**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_download_cfpb_all_dag_file.py tests/test_ccaa_download_helpers.py -v
```

Expected: PASS. (Do not import the DAG module under pytest without Airflow installed unless the env has it; the path test is enough for CI.)

- [ ] **Step 5: Commit**

```bash
/ccaa-commit-push 57
```

---

### Task 3: Seed `app_workflows` + env docs (TDD)

**Files:**
- Create: `Middleware/ConsumerComplaintsHandsOn/alembic/versions/0008_seed_download_cfpb_all_workflow.py`
- Modify: `Middleware/ConsumerComplaintsHandsOn/tests/test_schema.py`, `.env.example`, `CICD/Local/airflow/Airflow_Variables_Upsert.txt`, `ARCHITECTURE.md` (brief present-tense note if needed)

**Interfaces:**
- Consumes: admin schema `app_workflows` from migration `0003`
- Produces: seed row id `b4b8014f-d756-5bc8-a041-96899ac037ac` (`uuid5` of `ccaa/m02-0018/download_cfpb_all`)

- [ ] **Step 1: Extend schema tests (failing)**

In `tests/test_schema.py`, add assertions that after `upgrade` to head:

- a row exists in `consumer_comp_admin_db.app_workflows` with `workflow_name='download_cfpb_all'`, `engine_type='apache_airflow'`, `engine_workflow_id='download_cfpb_all'`
- `config` / JSON contains `dataset_code` = `CFPB`
- after downgrade to `0007`, that row is gone

Follow the existing seed assertions for `0006` as the pattern.

- [ ] **Step 2: Run the focused schema test and confirm failure**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_schema.py -k download_cfpb -v
```

Expected: FAIL (no migration / no row).

- [ ] **Step 3: Add migration `0008`**

```python
"""seed app_workflows row for download_cfpb_all (M02-0018 / D63)

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0018/download_cfpb_all")
WORKFLOW_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"

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


def upgrade() -> None:
    op.bulk_insert(
        workflows,
        [
            {
                "id": WORKFLOW_ID,
                "workflow_name": "download_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "download_cfpb_all",
                "config": {"dataset_code": "CFPB"},
                "enabled": True,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(workflows).where(workflows.c.id == WORKFLOW_ID))
```

Update `.env.example`:

```bash
# Directory where the CFPB zip lands inside the Airflow worker (D57 / D63). Name only in catalog; value per env.
LOCAL_DATA_PATH_CFPB=
```

Append to `CICD/Local/airflow/Airflow_Variables_Upsert.txt`:

```text
LOCAL_DATA_PATH_CFPB
```

- [ ] **Step 4: Run schema + helper + dag-file tests**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_schema.py tests/test_ccaa_download_helpers.py tests/test_download_cfpb_all_dag_file.py -v
```

Expected: PASS.

Manual (optional, when Airflow is up): wait ≥10s, confirm `download_cfpb_all` in `airflow dags list`; trigger with a real execution id after migrations + upsert-secrets.

- [ ] **Step 5: Commit**

```bash
/ccaa-commit-push 57
```

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| Source http / landing local (D63) | 1–2 |
| Standalone reader, no `app.*` | 1–2 |
| DAG id `download_cfpb_all` in Airflow-dags | 2 |
| Seed `app_workflows` | 3 |
| File lands as `complaints.csv.zip` under env path | 1–2 |
| TODO hooks for #59 only | 2 |
| Postgres preferred for Docker CCA_DB_URL | 2 comment + DESIGN/D63 |
| Unit + path tests; live Airflow manual | 1–3 |
