# M03-0012 (#122) E2E happy path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the Admin UI → API → Airflow → callback → UI happy path and add a CI-friendly smoke that asserts non-invented status from the active DB (SQLite first).

**Architecture:** Docs runbook for the full live path; a pytest smoke with mocked Airflow (start → callback → `GET /mios/status`) always runnable in `local:api:test`; optional live HTTP script + npm script for a running Middleware. No new facades (D64).

**Tech Stack:** FastAPI TestClient, pytest, httpx (live script), Markdown docs, root npm scripts.

## Global Constraints

- Never invent MIO/ingest status in UI or smoke assertions — only exact D30 strings from API/DB.
- D64: no new facades or public simulate endpoints.
- D75: SQLite-first in docs; smoke uses default test SQLite (`data_dir`).
- Rebase on `main` before PR if #117/#120 landed.

---

## File map

| File | Responsibility |
|---|---|
| `docs/local-admin-e2e-happy-path.md` | Human runbook (UI + Airflow + SQLite) |
| `docs/Superpowers/specs/M03-0012-e2e-happy-path-design.md` | Spec (already drafted) |
| `Middleware/.../tests/test_e2e_happy_path_smoke.py` | Automated happy-path smoke (TDD) |
| `CICD/Local/e2e_happy_path_smoke.py` | Optional live HTTP probe against `:8000` (outside Middleware scripts / D37) |
| `package.json` | `local:e2e:happy-path:smoke` |
| Portal + root README | One-line pointers |

---

### Task 1: Failing pytest smoke (TDD)

**Files:**
- Create: `Middleware/ConsumerComplaintsHandsOn/tests/test_e2e_happy_path_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
"""E2E happy-path smoke (M03-0012): start → callbacks → GET /mios/status (no invented status)."""

import httpx
import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_WF = "download_cfpb_all"
SEEDED_MIO = "Customer complaints 3 months 2026"
SECRET = "e2e-smoke-secret"
HEADERS = {"X-Callback-Secret": SECRET}


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        return httpx.Response(200, json={"dag_run_id": "e2e-run-1"})
    return httpx.Response(500)


@pytest.fixture
def mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))


def test_happy_path_start_callback_mios_status(client, data_dir, mock_airflow):
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == SEEDED_WF)
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    start = client.post(f"/workflows/{wf_id}/start", json={"mio_id": mio_id})
    assert start.status_code == 202
    execution_id = start.json()["execution_id"]
    assert execution_id

    before = client.get("/mios/status").json()
    entry = next(e for e in before if e["id"] == mio_id)
    assert entry["latest_ingest"]["status"] == "requested"
    assert entry["latest_ingest"]["executions"][0]["status"] == "requested"

    cb = f"/callbacks/workflow-executions/{execution_id}/status"
    assert client.post(cb, json={"status": "started", "engine_run_id": "e2e-run-1"}, headers=HEADERS).status_code == 200
    mid = next(e for e in client.get("/mios/status").json() if e["id"] == mio_id)
    assert mid["latest_ingest"]["status"] == "started"
    assert mid["latest_ingest"]["executions"][0]["status"] == "started"

    assert client.post(cb, json={"status": "completed", "message": "ok"}, headers=HEADERS).status_code == 200
    done = next(e for e in client.get("/mios/status").json() if e["id"] == mio_id)
    assert done["latest_ingest"]["status"] == "completed"
    assert done["latest_ingest"]["executions"][0]["status"] == "completed"
    # Never invent: only these literals
    assert done["latest_ingest"]["status"] in ("requested", "started", "completed", "failed")
```

- [ ] **Step 2: Run test — expect FAIL** if wiring wrong, or PASS if stack already supports it (then still keep test as the smoke gate).

```bash
cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_e2e_happy_path_smoke.py -q
```

- [ ] **Step 3: Commit** `M03-0012 #122: add e2e happy-path smoke test`

---

### Task 2: Live script + npm + docs

**Files:**
- Create: `CICD/Local/e2e_happy_path_smoke.py`
- Create: `docs/local-admin-e2e-happy-path.md`
- Modify: `package.json`, `README.md`, `Portals/consumer-complaints-admin/README.md`

- [ ] **Step 1: Live script** — `GET /health`, list workflows, if `CCA_E2E_MODE=full` start+poll; else print that pytest smoke is the default gate and exit 0 only when `/health` + `/workflows` + `/mios/status` succeed (read-only probe). Prefer documenting that full callback simulation without Airflow is covered by pytest; live script validates API up + catalog for local ops.

Better live script behavior matching design:

1. Require `CCA_CALLBACK_SECRET` and API base (`CCA_E2E_API_BASE` default `http://127.0.0.1:8000`).
2. Mode `probe` (default): health + workflows contains `download_cfpb_all` + mios/status JSON list (no invent).
3. Mode `full`: POST start with first MIO, poll until started/completed (needs Airflow).
4. Mode `callback`: after start (202) or fail with clear message if 502 — for 202, POST started/completed and assert mios/status.

- [ ] **Step 2: npm** `"local:e2e:happy-path:smoke": "cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_e2e_happy_path_smoke.py -q"`

- [ ] **Step 3: Write runbook** `docs/local-admin-e2e-happy-path.md` (SQLite first, containers, with-api, Imports UI, expected statuses, smoke command, full Airflow notes).

- [ ] **Step 4: README pointers** (one line each).

- [ ] **Step 5: Commit** `M03-0012 #122: document e2e happy path and smoke script`

---

### Task 3: Verify + PR

- [ ] Rebase on `origin/main`
- [ ] `npm run local:e2e:happy-path:smoke` and `npm run local:api:test` (or at least the new file + lint if Python unchanged beyond tests/scripts)
- [ ] Final `ccaa-commit-push 122`, open PR, merge when green
- [ ] `ccaa-story-complete 122` then `ccaa-feature-complete 114` if both stories done
