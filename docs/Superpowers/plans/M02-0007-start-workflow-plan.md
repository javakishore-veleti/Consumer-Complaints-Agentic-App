# M02-0007 (#42) Start-workflow endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `POST /workflows/{workflow_id}/start` creates the execution (and optional MIO ingest), triggers Airflow via #60 `AirflowStartDagFacade`, and returns 202 with `execution_id` without waiting.

**Architecture:** `StartWfApi` → `StartWfFacade` (two tasks under `impl/start_wf/tasks/`, D64): (1) `StartWfService` creates optional ingest + exec log; (2) `AirflowStartDagFacade.start` (#60). No callback secret (D59). Factories register via `init()` (D45).

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, httpx MockTransport, pytest, `uv`, import-linter; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0007-start-workflow-design.md`. Decisions: D5, D6, D12, D26, D29, D32, D33, D37, D43, D45, D46, D51, D54, D55, D56, D58, D59, D60, D64, **D68**.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there. Plan/spec paths are relative to the repo root.
- Endpoint exactly: `POST /workflows/{workflow_id}/start`, tag `workflows`, success **202** with `{"execution_id": "..."}`.
- Names exactly: `StartWf*`; package `start_wf`; factory methods `get_start_wf_service()`, `get_start_wf_facade()`, `get_start_wf_api()`.
- Facade files under `app/core/facades/impl/start_wf/` and `impl/start_wf/tasks/` (D64). Second task calls `FacadesObjectsFactory.get_airflow_start_dag_facade()`.
- No callback secret on this router. Unknown/disabled/non-airflow workflow → 422 `invalid request`. Airflow FAILURE → 502 `engine start failed`.
- Every class is a singleton (`SingletonMeta`, D26) registered in package `init()` (D45).
- Every function takes nothing or exactly one object (D5, D37).
- `uv run lint-imports`: `Contracts: 7 kept, 0 broken.`
- Regenerate `openapi.json` with `uv run python scripts/export_openapi.py` (D32).
- Test workflow names use prefix `t_`. Scratch in `runtime_data/tmp/` only. Never commit `.env`.
- Commit after each task: `M02-0007 #42: <imperative summary>` (strip AI trailers; author `javakishore-veleti`).

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/dtos/start_wf_dtos.py` | service Req/Resp/Ctx |
| `app/core/common/dtos/start_wf_facade_dtos.py` | facade ctx |
| `app/core/services/start_wf_service.py` | service interface |
| `app/core/services/impl/start_wf_service_impl.py` | prepare ingest + exec |
| `app/core/services/objects_factory.py` | register + `get_start_wf_service` |
| `app/core/facades/start_wf_facade.py`, `start_wf_facade_task.py` | interfaces |
| `app/core/facades/impl/start_wf/` + `tasks/` | impl + two tasks (D64) |
| `app/core/facades/objects_factory.py` | register + `get_start_wf_facade` |
| `app/api/models/start_wf_models.py` | body + out |
| `app/api/routers/start_wf_api.py` | HTTP mapping |
| `app/api/objects_factory.py` | register + include without secret |
| `openapi.json` | regenerate |
| `tests/test_start_wf_service.py`, `tests/test_start_wf_api.py` | service/facade/HTTP |
| `tests/test_singletons.py`, `tests/test_postgres.py` | singletons; Postgres |
| `DESIGN.md`, `ARCHITECTURE.md`, `Milestone_02.md` | D68 + docs |

---

### Task 1: StartWf service, facade (D64) and factories

**Files:**
- Create: DTOs, service, facade interfaces/impl/tasks, empty `__init__.py`s
- Modify: `services/objects_factory.py`, `facades/objects_factory.py`
- Test: `tests/test_start_wf_service.py`, `tests/test_singletons.py`

**Interfaces:**
- Consumes: `AppWfDao`, `MioIngestLogDao`, `DatasetLocationDao`, `AppWfExecLogDao`; `AirflowStartDagFacade`
- Produces: `StartWfService.start(ctx) -> int` with `resp.execution_id`; `StartWfFacade.start(ctx) -> int`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_start_wf_service.py`:

```python
"""StartWfService prepares ingest+exec; facade triggers Airflow (#60) (D68)."""

import json

import httpx
import pytest

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagReq
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.start_wf_dtos import StartWfCtx, StartWfReq
from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        body = json.loads(request.content.decode())
        assert body["logical_date"] is None
        assert body["conf"]["execution_id"]
        return httpx.Response(200, json={"dag_run_id": "run-start-1"})
    return httpx.Response(500)


@pytest.fixture(autouse=True)
def _airflow_env(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)
    yield
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)


def _workflow(name="t_start", enabled=True, engine_type="apache_airflow") -> str:
    ctx = AppWfCtx(
        req=AppWfReq(
            workflow_name=name,
            engine_type=engine_type,
            engine_workflow_id="download_cfpb_all",
            enabled=enabled,
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _mio() -> str:
    ctx = MioCtx(req=MioReq(name="t_mio_start", description="d"))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def test_creates_exec_without_mio(data_dir):
    wf_id = _workflow()
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == SUCCESS
    assert ctx.resp.execution_id
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    row = got.resp.records[0]
    assert row.workflow_id == wf_id and row.mios_ingest_log_id is None and row.status == "requested"


def test_creates_ingest_and_links_exec(data_dir):
    wf_id, mio_id = _workflow("t_start_mio"), _mio()
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id=mio_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == SUCCESS
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    ingest_id = got.resp.records[0].mios_ingest_log_id
    assert ingest_id
    ing = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ing) == SUCCESS
    assert ing.resp.records[0].mio_id == mio_id and ing.resp.records[0].status == "requested"


def test_unknown_workflow_is_invalid(data_dir):
    ctx = StartWfCtx(req=StartWfReq(workflow_id="missing"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_disabled_workflow_is_invalid(data_dir):
    wf_id = _workflow("t_disabled", enabled=False)
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_non_airflow_engine_is_invalid(data_dir):
    wf_id = _workflow("t_step", engine_type="aws_step_functions")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_blank_mio_id_is_invalid(data_dir):
    wf_id = _workflow("t_blank_mio")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id="  "))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_unknown_mio_is_invalid(data_dir):
    wf_id = _workflow("t_bad_mio")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id="no-such-mio"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_unknown_dataset_location_is_invalid(data_dir):
    wf_id = _workflow("t_bad_loc")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, dataset_location_id="no-loc"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_facade_triggers_airflow_and_stores_run_id(data_dir):
    from app.core.common.bean_registry import bean_registry
    from app.core.services.airflow_start_dag_service import AirflowStartDagService

    ServicesObjectsFactory.init()
    bean_registry.register(
        AirflowStartDagService,
        AirflowStartDagServiceImpl(client=AirflowDagRunsClient(transport=httpx.MockTransport(_handler))),
    )
    wf_id = _workflow("t_facade_af")
    ctx = StartWfFacadeCtx(req=StartWfReq(workflow_id=wf_id))
    assert FacadesObjectsFactory.get_start_wf_facade().start(ctx) == SUCCESS
    assert ctx.resp.execution_id
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].engine_run_id == "run-start-1"
```

In `tests/test_singletons.py`, add StartWf factory/class singleton asserts (same pattern as WfList).

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_start_wf_service.py -v
```

Expected: FAIL — missing modules / factory methods.

- [ ] **Step 3: Implement DTOs, service, facade, factories**

`start_wf_dtos.py`:

```python
from dataclasses import dataclass, field

@dataclass
class StartWfReq:
    workflow_id: str | None = None
    mio_id: str | None = None
    dataset_location_id: str | None = None

@dataclass
class StartWfResp:
    execution_id: str | None = None
    code: int = 0

@dataclass
class StartWfCtx:
    req: StartWfReq = field(default_factory=StartWfReq)
    resp: StartWfResp = field(default_factory=StartWfResp)
```

`start_wf_facade_dtos.py`: facade ctx with `req`, `resp`, `start_ctx: StartWfCtx | None = None`.

`StartWfServiceImpl.start`: follow the design prepare steps; map workflow/mio/location NOT_FOUND to INVALID_INPUT.

`StartWfCallServiceTask`: build service ctx from `ctx.req`, call service, copy `execution_id` and code onto facade resp.

`StartWfTriggerEngineTask`: build `AirflowStartDagFacadeCtx(req=AirflowStartDagReq(execution_id=ctx.resp.execution_id))`, call `get_airflow_start_dag_facade().start`, set facade `resp.code` to the result.

`StartWfFacadeImpl`: tasks = [CallService, TriggerEngine]; stop on non-SUCCESS (D24).

Register in both factories' `init()` and add getters.

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_start_wf_service.py tests/test_singletons.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
# stage named files only; message: M02-0007 #42: add start-wf service and facade
```

---

### Task 2: HTTP API, OpenAPI, docs

**Files:**
- Create: `app/api/models/start_wf_models.py`, `app/api/routers/start_wf_api.py`, `tests/test_start_wf_api.py`
- Modify: `app/api/objects_factory.py`, `openapi.json`, `tests/test_postgres.py`, `DESIGN.md`, `ARCHITECTURE.md`, `docs/Project_Management/Issues/Milestone_02.md`

**Interfaces:**
- Consumes: `StartWfFacade` via `FacadesObjectsFactory`
- Produces: `POST /workflows/{workflow_id}/start` → 202 / 422 / 502 / 500

- [ ] **Step 1: Write the failing API tests**

```python
"""POST /workflows/{id}/start through HTTP (D68)."""

import json

import httpx
import pytest

from app.core.common.bean_registry import bean_registry
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.airflow_start_dag_service import AirflowStartDagService
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED = "download_cfpb_all"


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        return httpx.Response(200, json={"dag_run_id": "run-api-1"})
    return httpx.Response(500)


def _fail(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    return httpx.Response(503, json={"detail": "down"})


@pytest.fixture
def seeded_wf_id(data_dir):
    ctx = AppWfCtx(req=AppWfReq(workflow_name=SEEDED))
    # get by name from seeded migration
    listed = AppWfCtx()
    DaoObjectsFactory.get_app_wf_dao().list(listed)
    return next(r.id for r in listed.resp.records if r.workflow_name == SEEDED)


@pytest.fixture
def mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)
    ServicesObjectsFactory.init()
    bean_registry.register(
        AirflowStartDagService,
        AirflowStartDagServiceImpl(client=AirflowDagRunsClient(transport=httpx.MockTransport(_handler))),
    )
    yield
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)


def test_start_returns_202_with_execution_id(client, seeded_wf_id, mock_airflow):
    response = client.post(f"/workflows/{seeded_wf_id}/start", json={})
    assert response.status_code == 202
    body = response.json()
    assert body["execution_id"]
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=body["execution_id"]))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].engine_run_id == "run-api-1"


def test_unknown_workflow_is_422(client, mock_airflow):
    assert client.post("/workflows/no-such/start", json={}).status_code == 422
    assert client.post("/workflows/no-such/start", json={}).json()["detail"] == "invalid request"


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, seeded_wf_id, mock_airflow, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.post(f"/workflows/{seeded_wf_id}/start", json={}).status_code == 202


def test_airflow_failure_is_502(client, seeded_wf_id, monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)
    ServicesObjectsFactory.init()
    bean_registry.register(
        AirflowStartDagService,
        AirflowStartDagServiceImpl(client=AirflowDagRunsClient(transport=httpx.MockTransport(_fail))),
    )
    response = client.post(f"/workflows/{seeded_wf_id}/start", json={})
    assert response.status_code == 502
    assert response.json()["detail"] == "engine start failed"
    # orphan exec row exists
    listed = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=seeded_wf_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().list(listed) == SUCCESS
    assert listed.resp.records


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/workflows/{workflow_id}/start" in spec["paths"]
    assert "post" in spec["paths"]["/workflows/{workflow_id}/start"]
```

- [ ] **Step 2: Run API tests — expect fail**

```bash
uv run pytest tests/test_start_wf_api.py -v
```

- [ ] **Step 3: Implement API + factory + OpenAPI + docs**

`StartWfApi`: route `/{workflow_id}/start` POST; build req; call facade; map SUCCESS→202, INVALID_INPUT→422, FAILURE→502, else→500.

Include router in `ApiObjectsFactory` next to `wf_list_api` without secret.

Add D68 to DESIGN.md; update section 4.2 Start row; ARCHITECTURE §5.3 mention `POST /workflows/{id}/start`; Milestone next-decision note stays D69 after this.

Postgres: add `test_start_wf_service_works_on_postgres` mirroring the facade happy path with MockTransport.

Regenerate openapi:

```bash
uv run python scripts/export_openapi.py
```

- [ ] **Step 4: Lint and full test**

```bash
cd ../.. && npm run local:api:lint && npm run local:api:test
```

(from repo root / worktree root)

- [ ] **Step 5: Commit**

```bash
# M02-0007 #42: add start-workflow HTTP endpoint
```

---

## Self-review

1. Spec coverage: prepare steps, ingest link, #60 facade, 202/422/502, no secret, D64 package, factories, OpenAPI, singletons, Postgres — all tasked.
2. No placeholders.
3. Types: `StartWfReq.workflow_id`, `resp.execution_id`, path `workflow_id` consistent.
