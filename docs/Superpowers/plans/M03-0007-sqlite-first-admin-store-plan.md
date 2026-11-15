# M03-0007 (#117) SQLite-first admin store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove and harden the M02 admin schema on default SQLite (migrations, DAOs, start-workflow + callback persistence) with no Postgres container.

**Architecture:** Keep SQLAlchemy DAOs + Alembic (D23/D75). Add **D76** reliability contract. Harden `data_dir` env isolation. Add one file-level SQLite persistence test for start → callback.

**Tech Stack:** Python 3.11+, pytest, Alembic, sqlite3, FastAPI TestClient, uv.

Spec: `docs/Superpowers/specs/M03-0007-sqlite-first-admin-store-design.md`. Decision: **D76**.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run pytest / lint from there unless a step says otherwise.
- Do **not** implement Postgres DoD (#118) or Mongo DAOs (#119).
- Do **not** add new facade packages (D64).
- Avoid colliding with #120 on package.json/docker profiles unless necessary; prefer not editing portal (`Portals/`).
- Scratch under `runtime_data/tmp/` (D36); never commit it.
- Commit with `/ccaa-commit-push 117` only. Author `javakishore-veleti`; strip AI Co-authored-by trailers.
- Next free decision after this story is **D77+**.

## File Structure

| File | Responsibility |
|---|---|
| `docs/Superpowers/specs/M03-0007-sqlite-first-admin-store-design.md` | Spec |
| `docs/Superpowers/plans/M03-0007-sqlite-first-admin-store-plan.md` | This plan |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | Add D76 |
| `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` | Note SQLite-first verified for admin schema |
| `docs/Project_Management/Issues/Milestone_03.md` | Workflow + next decision D77+ |
| `tests/conftest.py` | Clear operational-store env in `data_dir` |
| `tests/test_sqlite_admin_store.py` | Head admin tables + start/callback file persistence |

---

### Task 1: Decision + docs

**Files:** DESIGN.md, ARCHITECTURE.md, Milestone_03.md notes, spec/plan

- [ ] **Step 1: Add D76** to DESIGN.md after D75 (full contract from the spec).
- [ ] **Step 2: ARCHITECTURE §6** — one sentence that the default SQLite path is verified for the M02 admin schema (migrations + start/callback), story #117 / D76.
- [ ] **Step 3: Milestone note** — next free decision **D77+**.
- [ ] **Step 4: Commit** — `M03-0007 #117: document SQLite-first admin store (D76)`

### Task 2: Test isolation + failing persistence test (TDD)

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/test_sqlite_admin_store.py`

- [ ] **Step 1: Harden `data_dir`** — after clearing `CCA_DB_URL`, also `monkeypatch.delenv("CCA_OPERATIONAL_STORE", raising=False)` and `monkeypatch.delenv("CCA_MONGO_OPERATIONAL_URL", raising=False)`.

- [ ] **Step 2: Write failing/new tests** in `test_sqlite_admin_store.py`:

```python
"""SQLite-first admin store (D76): migrate, start-workflow, callback → rows in .sqlite files."""

import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory
from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

ADMIN_TABLES = {
    "app_workflows",
    "app_workflows_exec_log",
    "datasets",
    "datasets_location",
    "mios",
    "mios_datasets",
    "mios_ingest_log",
}
SECRET = "sqlite-first-callback-secret"
SEEDED_WF = "download_cfpb_all"
SEEDED_MIO = "Customer complaints 3 months 2026"


def _admin(data_dir):
    return sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite")


def test_alembic_head_creates_admin_tables_in_sqlite_file(data_dir):
    with _admin(data_dir) as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    assert ADMIN_TABLES <= tables
    assert "system_datasets" not in tables and "data_ingest_log" not in tables


def _mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/token":
            return httpx.Response(201, json={"access_token": "tok"})
        if request.method == "POST" and "/dagRuns" in request.url.path:
            return httpx.Response(200, json={"dag_run_id": "sqlite-run-1"})
        return httpx.Response(500)

    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(handler))


def test_start_workflow_and_callback_persist_to_sqlite_file(data_dir, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    _mock_airflow(monkeypatch)
    client = TestClient(ApiObjectsFactory.get_app())

    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == SEEDED_WF)

    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    started = client.post(f"/workflows/{wf_id}/start", json={"mio_id": mio_id})
    assert started.status_code == 202
    execution_id = started.json()["execution_id"]

    with _admin(data_dir) as db:
        exec_row = db.execute(
            "select status, engine_run_id, mios_ingest_log_id from app_workflows_exec_log where id = ?",
            (execution_id,),
        ).fetchone()
        assert exec_row is not None
        assert exec_row[0] == "requested"
        assert exec_row[1] == "sqlite-run-1"
        ingest_id = exec_row[2]
        assert ingest_id
        assert db.execute("select status from mios_ingest_log where id = ?", (ingest_id,)).fetchone()[0] == "requested"

    cb = client.post(
        f"/callbacks/workflow-executions/{execution_id}/status",
        json={"status": "started", "engine_run_id": "sqlite-run-1"},
        headers={"X-Callback-Secret": SECRET},
    )
    assert cb.status_code == 200

    with _admin(data_dir) as db:
        assert db.execute("select status from app_workflows_exec_log where id = ?", (execution_id,)).fetchone()[0] == "started"
        assert db.execute("select status from mios_ingest_log where id = ?", (ingest_id,)).fetchone()[0] == "started"
```

- [ ] **Step 3: Run** `uv run pytest tests/test_sqlite_admin_store.py -v` — expect PASS if stack already correct; if FAIL, fix the minimal SQLite gap (batch mode / attach / DAO) then re-run.
- [ ] **Step 4: Commit** — `M03-0007 #117: prove start+callback persist on SQLite`

### Task 3: Verify and finish

- [ ] **Step 1:** From repo root (worktree): `npm run local:api:lint` and `npm run local:api:test`.
- [ ] **Step 2:** Confirm `npm run local:api:migrate` with unset `CCA_DB_URL` against a temp `CCA_DATA_DIR`.
- [ ] **Step 3:** Final `/ccaa-commit-push 117`, PR → main, green CI, merge, `/ccaa-story-complete 117`.
