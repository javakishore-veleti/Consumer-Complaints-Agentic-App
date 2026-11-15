# M02-0021 Airflow start DAG run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start an Airflow DAG run via REST (JWT), return immediately, and store Airflow's `dag_run_id` on `app_workflows_exec_log.engine_run_id` for later use by #42 / #83.

**Architecture:** `AirflowStartDagFacade` (D64 package `impl/af_start/`, one task) → `AirflowStartDagService` → `AppWfExecLogDao` + private `AirflowDagRunsClient` (same Settings/JWT pattern as #77 Variables client). No public HTTP endpoint.

**Tech Stack:** Python, httpx, FastAPI app layers (facades/services/dao), pytest + `httpx.MockTransport`.

## Global Constraints

- Ctx-only signatures (D37); singletons + package factories (D26); no `init()` yet.
- New facade tasks under `facades/impl/af_start/tasks/` (D64); do not move old facades.
- Reuse `CCA_AIRFLOW_API_*`; never log tokens/passwords.
- Do not change execution status on start (callbacks own started/completed/failed).
- No production code outside the tasks below; `/ccaa-commit-push 60` after each task.
- Spec: `docs/Superpowers/specs/M02-0021-airflow-start-dag-design.md`. No new DESIGN decision (D65 unused).

## File map

| Path | Role |
|---|---|
| `app/core/common/dtos/airflow_start_dag_dtos.py` | Service + client ctx/req/resp |
| `app/core/common/dtos/airflow_start_dag_facade_dtos.py` | Facade ctx |
| `app/core/services/impl/airflow_dag_runs_client.py` | JWT + POST dagRuns |
| `app/core/services/airflow_start_dag_service.py` | Interface |
| `app/core/services/impl/airflow_start_dag_service_impl.py` | get → trigger → update |
| `app/core/facades/airflow_start_dag_facade.py` / `_facade_task.py` | Interfaces |
| `app/core/facades/impl/af_start/airflow_start_dag_facade_impl.py` | Facade impl |
| `app/core/facades/impl/af_start/tasks/airflow_start_dag_call_service_task.py` | One task |
| `app/core/services/objects_factory.py` / `facades/objects_factory.py` | Factory methods |
| `tests/test_airflow_dag_runs_client.py` | Client tests |
| `tests/test_airflow_start_dag_service.py` | Service tests |
| `tests/test_airflow_start_dag_facade.py` | Facade + singleton wiring |

---

### Task 1: AirflowDagRunsClient (JWT + trigger)

**Files:**
- Create: `Middleware/ConsumerComplaintsHandsOn/app/core/common/dtos/airflow_start_dag_dtos.py`
- Create: `Middleware/ConsumerComplaintsHandsOn/app/core/services/impl/airflow_dag_runs_client.py`
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_airflow_dag_runs_client.py`

**Interfaces:**
- Produces: `AirflowDagRunsClient.trigger(ctx: AirflowDagRunTriggerCtx) -> int`; on SUCCESS sets `ctx.resp.dag_run_id`.

- [ ] **Step 1: Write the failing test**

```python
"""Airflow DAG runs client: JWT then POST /api/v2/dags/{dag_id}/dagRuns."""

import json

import httpx
import pytest

from app.core.common.dtos.airflow_start_dag_dtos import (
    AirflowDagRunTriggerCtx,
    AirflowDagRunTriggerReq,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/auth/token" and request.method == "POST":
        return httpx.Response(201, json={"access_token": "tok"})
    if path == "/api/v2/dags/download_cfpb_all/dagRuns" and request.method == "POST":
        body = json.loads(request.content.decode())
        assert body == {"logical_date": None, "conf": {"execution_id": "exec-1"}}
        assert request.headers.get("Authorization") == "Bearer tok"
        return httpx.Response(200, json={"dag_run_id": "manual__2026-11-14T00:00:00+00:00"})
    return httpx.Response(500, json={"detail": "unexpected"})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    return AirflowDagRunsClient(transport=httpx.MockTransport(_handler))


def test_trigger_returns_dag_run_id(client):
    ctx = AirflowDagRunTriggerCtx(
        req=AirflowDagRunTriggerReq(dag_id="download_cfpb_all", execution_id="exec-1")
    )
    assert client.trigger(ctx) == SUCCESS
    assert ctx.resp.dag_run_id == "manual__2026-11-14T00:00:00+00:00"


def test_token_failure_is_failure(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def bad_token(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    client = AirflowDagRunsClient(transport=httpx.MockTransport(bad_token))
    ctx = AirflowDagRunTriggerCtx(
        req=AirflowDagRunTriggerReq(dag_id="download_cfpb_all", execution_id="exec-1")
    )
    assert client.trigger(ctx) == FAILURE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_airflow_dag_runs_client.py -v`

Expected: FAIL with `ModuleNotFoundError` or import error for `airflow_dag_runs_client`.

- [ ] **Step 3: Minimal DTOs + client**

`airflow_start_dag_dtos.py`:

```python
from dataclasses import dataclass, field


@dataclass
class AirflowDagRunTriggerReq:
    dag_id: str
    execution_id: str


@dataclass
class AirflowDagRunTriggerResp:
    dag_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowDagRunTriggerCtx:
    req: AirflowDagRunTriggerReq
    resp: AirflowDagRunTriggerResp = field(default_factory=AirflowDagRunTriggerResp)


@dataclass
class AirflowStartDagReq:
    execution_id: str | None = None


@dataclass
class AirflowStartDagResp:
    engine_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowStartDagCtx:
    req: AirflowStartDagReq
    resp: AirflowStartDagResp = field(default_factory=AirflowStartDagResp)
```

`airflow_dag_runs_client.py` (mirror Variables client JWT; POST dagRuns; set `ctx.resp.dag_run_id` from JSON; FAILURE on bad status / missing id / HTTPError; never log secrets):

```python
"""HTTP client for Airflow 3 DAG runs API (JWT). Never logs tokens or passwords."""

from __future__ import annotations

import logging

import httpx

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_start_dag_dtos import AirflowDagRunTriggerCtx
from app.core.common.return_codes import FAILURE, SUCCESS

logger = logging.getLogger(__name__)


class AirflowDagRunsClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport

    def trigger(self, ctx: AirflowDagRunTriggerCtx) -> int:
        ctx.resp.dag_run_id = None
        settings = get_settings()
        if not settings.airflow_api_username or settings.airflow_api_password is None:
            ctx.resp.code = FAILURE
            return FAILURE
        timeout = httpx.Timeout(5.0, read=30.0)
        try:
            with httpx.Client(
                base_url=settings.airflow_api_base_url,
                timeout=timeout,
                transport=self._transport,
            ) as http:
                token_response = http.post(
                    "/auth/token",
                    json={
                        "username": settings.airflow_api_username,
                        "password": settings.airflow_api_password,
                    },
                )
                if token_response.status_code not in (200, 201):
                    logger.warning(
                        "airflow dag run trigger failed: token status %s",
                        token_response.status_code,
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                token = token_response.json().get("access_token")
                if not isinstance(token, str) or not token:
                    ctx.resp.code = FAILURE
                    return FAILURE
                headers = {"Authorization": f"Bearer {token}"}
                created = http.post(
                    f"/api/v2/dags/{ctx.req.dag_id}/dagRuns",
                    headers=headers,
                    json={
                        "logical_date": None,
                        "conf": {"execution_id": ctx.req.execution_id},
                    },
                )
                if created.status_code not in (200, 201):
                    logger.warning(
                        "airflow dag run trigger failed: create status %s",
                        created.status_code,
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                dag_run_id = created.json().get("dag_run_id")
                if not isinstance(dag_run_id, str) or not dag_run_id:
                    ctx.resp.code = FAILURE
                    return FAILURE
                ctx.resp.dag_run_id = dag_run_id
        except httpx.HTTPError:
            logger.warning("airflow dag run trigger failed: unreachable")
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `uv run pytest tests/test_airflow_dag_runs_client.py -v`

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 60` with summary `Airflow DAG runs client JWT trigger`.

---

### Task 2: AirflowStartDagService (get → trigger → store engine_run_id)

**Files:**
- Create: `app/core/services/airflow_start_dag_service.py`
- Create: `app/core/services/impl/airflow_start_dag_service_impl.py`
- Modify: `app/core/services/objects_factory.py`
- Test: `tests/test_airflow_start_dag_service.py`

**Interfaces:**
- Consumes: `AirflowDagRunsClient.trigger`, `AppWfExecLogDao.get/update` via `DaoObjectsFactory`
- Produces: `AirflowStartDagService.start(ctx: AirflowStartDagCtx) -> int`; SUCCESS sets `ctx.resp.engine_run_id`

- [ ] **Step 1: Write the failing test**

```python
"""AirflowStartDagService: load execution, trigger DAG, store engine_run_id; status stays requested."""

import json

import httpx
import pytest

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx, AirflowStartDagReq
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and request.url.path.endswith("/dagRuns"):
        body = json.loads(request.content.decode())
        assert body["logical_date"] is None
        assert "execution_id" in body["conf"]
        return httpx.Response(200, json={"dag_run_id": "run-abc"})
    return httpx.Response(500)


@pytest.fixture
def execution_id(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    wf = DaoObjectsFactory.get_app_wf_dao()
    wctx = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_start_dag",
            engine_type="apache_airflow",
            engine_workflow_id="download_cfpb_all",
        )
    )
    assert wf.create(wctx) == SUCCESS
    elog = DaoObjectsFactory.get_app_wf_exec_log_dao()
    ectx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=wctx.resp.records[0].id))
    assert elog.create(ectx) == SUCCESS
    return ectx.resp.records[0].id


def test_start_stores_engine_run_id_and_keeps_requested(execution_id, monkeypatch):
    service = AirflowStartDagServiceImpl()
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id=execution_id))
    assert service.start(ctx) == SUCCESS
    assert ctx.resp.engine_run_id == "run-abc"
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    row = got.resp.records[0]
    assert (row.engine_run_id, row.status) == ("run-abc", "requested")


def test_unknown_execution_is_not_found():
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id="missing"))
    assert AirflowStartDagServiceImpl().start(ctx) == NOT_FOUND


def test_blank_execution_id_is_invalid():
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id="  "))
    assert AirflowStartDagServiceImpl().start(ctx) == INVALID_INPUT
```

If the service impl does not expose `_client`, inject via constructor default `AirflowDagRunsClient()` and in the test subclass or patch: prefer a constructor arg `client: AirflowDagRunsClient | None = None` stored as `self._client = client or AirflowDagRunsClient()` (still a singleton class with no per-request state beyond the optional transport used only in tests).

- [ ] **Step 2: Run — expect FAIL** (service missing)

Run: `uv run pytest tests/test_airflow_start_dag_service.py -v`

- [ ] **Step 3: Interface + impl + factory**

Interface:

```python
from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx
from app.core.common.singleton import SingletonMeta


class AirflowStartDagService(metaclass=SingletonMeta):
    def start(self, ctx: AirflowStartDagCtx) -> int:
        raise NotImplementedError
```

Impl sketch:

```python
class AirflowStartDagServiceImpl(AirflowStartDagService):
    def __init__(self, client: AirflowDagRunsClient | None = None):
        self._client = client or AirflowDagRunsClient()

    def start(self, ctx: AirflowStartDagCtx) -> int:
        ctx.resp.engine_run_id = None
        execution_id = (ctx.req.execution_id or "").strip()
        if not execution_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        elog = DaoObjectsFactory.get_app_wf_exec_log_dao()
        get_ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
        code = elog.get(get_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        row = get_ctx.resp.records[0]
        dag_id = (row.engine_workflow_id or "").strip()
        if not dag_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        trigger = AirflowDagRunTriggerCtx(
            req=AirflowDagRunTriggerReq(dag_id=dag_id, execution_id=execution_id)
        )
        code = self._client.trigger(trigger)
        if code != SUCCESS or not trigger.resp.dag_run_id:
            ctx.resp.code = FAILURE
            return FAILURE
        upd = AppWfExecLogCtx(
            req=AppWfExecLogReq(id=execution_id, engine_run_id=trigger.resp.dag_run_id)
        )
        code = elog.update(upd)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.engine_run_id = trigger.resp.dag_run_id
        ctx.resp.code = SUCCESS
        return SUCCESS
```

Add `ServicesObjectsFactory.get_airflow_start_dag_service() -> AirflowStartDagService`.

Note: `SingletonMeta` + `__init__` with optional client — tests that need a mock transport must call `AirflowStartDagServiceImpl(client=...)` **before** any other construction, or clear the singleton between tests if the metaclass caches the first instance. Prefer: in tests, patch `AirflowStartDagServiceImpl._client` on the instance returned by the factory after forcing a fresh instance, **or** pass transport by monkeypatching `AirflowDagRunsClient.__init__`. Simplest stable approach used in this plan: instantiate `AirflowStartDagServiceImpl(client=AirflowDagRunsClient(transport=...))` in the happy-path test only; if SingletonMeta returns a prior empty instance, clear via the project's existing singleton reset pattern if any, else set `AirflowStartDagServiceImpl._instances = {}` before constructing (only in that test module). Mirror whatever `test_airflow_upsert_secrets_*` does if present; otherwise reset `_instances` in an autouse fixture for this module.

- [ ] **Step 4: Run — expect PASS**

Run: `uv run pytest tests/test_airflow_start_dag_service.py tests/test_airflow_dag_runs_client.py -v`

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 60` with summary `AirflowStartDagService stores engine_run_id`.

---

### Task 3: Facade (D64 `af_start`) + factories

**Files:**
- Create: `app/core/common/dtos/airflow_start_dag_facade_dtos.py`
- Create: `app/core/facades/airflow_start_dag_facade.py`
- Create: `app/core/facades/airflow_start_dag_facade_task.py`
- Create: `app/core/facades/impl/af_start/__init__.py` (empty)
- Create: `app/core/facades/impl/af_start/tasks/__init__.py` (empty)
- Create: `app/core/facades/impl/af_start/airflow_start_dag_facade_impl.py`
- Create: `app/core/facades/impl/af_start/tasks/airflow_start_dag_call_service_task.py`
- Modify: `app/core/facades/objects_factory.py`
- Modify: `tests/test_singletons.py` (add facade + service assertions)
- Test: `tests/test_airflow_start_dag_facade.py`

**Interfaces:**
- Consumes: `ServicesObjectsFactory.get_airflow_start_dag_service().start`
- Produces: `FacadesObjectsFactory.get_airflow_start_dag_facade().start(ctx) -> int`

- [ ] **Step 1: Failing facade test**

```python
"""AirflowStartDagFacade: one task calls the service (D64 af_start)."""

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagReq
from app.core.common.dtos.airflow_start_dag_facade_dtos import (
    AirflowStartDagFacadeCtx,
    AirflowStartDagFacadeResp,
)
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.facades.objects_factory import FacadesObjectsFactory


def test_blank_execution_id_stops_at_invalid():
    ctx = AirflowStartDagFacadeCtx(
        req=AirflowStartDagReq(execution_id=""),
        resp=AirflowStartDagFacadeResp(),
    )
    assert FacadesObjectsFactory.get_airflow_start_dag_facade().start(ctx) == INVALID_INPUT
    assert ctx.resp.code == INVALID_INPUT
```

Facade DTOs hold `req: AirflowStartDagReq`, `resp: AirflowStartDagFacadeResp` with `engine_run_id` and `code`, plus optional nested `start_ctx: AirflowStartDagCtx | None` if other facades nest that way — follow `airflow_upsert_secrets_facade_dtos` / `wf_exec_status` pattern: one facade ctx wrapping the service ctx built inside the task.

Minimal pattern (match upsert-secrets):

```python
@dataclass
class AirflowStartDagFacadeResp:
    engine_run_id: str | None = None
    code: int = 0


@dataclass
class AirflowStartDagFacadeCtx:
    req: AirflowStartDagReq
    resp: AirflowStartDagFacadeResp = field(default_factory=AirflowStartDagFacadeResp)
```

Task builds `AirflowStartDagCtx(req=ctx.req)`, calls service, copies `engine_run_id` and `code` onto `ctx.resp`.

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement facade + task + factory + singleton test lines**

Facade impl loops one task list (D6/D24). Factory lazy-imports `AirflowStartDagFacadeImpl` from `app.core.facades.impl.af_start.airflow_start_dag_facade_impl`.

- [ ] **Step 4: Run full related suite**

Run: `uv run pytest tests/test_airflow_dag_runs_client.py tests/test_airflow_start_dag_service.py tests/test_airflow_start_dag_facade.py tests/test_singletons.py tests/test_import_contracts.py -v`

Also: `npm run local:api:lint` and `npm run local:api:test` from repo root before the final push of this task.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 60` with summary `AirflowStartDagFacade under af_start package`.

---

## Spec coverage self-review

| Spec requirement | Task |
|---|---|
| JWT + POST dagRuns, returns immediately | 1 |
| Store `dag_run_id` as `engine_run_id` | 2 |
| Status stays `requested` | 2 |
| Facade D64 `af_start` | 3 |
| No public endpoint / no D65 | all (omitted) |
| Settings reuse CCA_AIRFLOW_API_* | 1–2 |

No placeholders left. Types consistent: `execution_id` → `dag_run_id` → `engine_run_id`.
