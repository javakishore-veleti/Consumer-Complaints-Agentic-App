# M02-0010 (#45) Read MIO status endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `GET /mios/status` returns every MIO with its latest ingest status and that ingest's executions, so the admin portal can fill its accordions in one call.

**Architecture:** `MioStatusApi` (a singleton router class, D29) builds a `MioStatusFacadeCtx` from its one request object and calls `MioStatusFacade`; the facade's one task calls `MioStatusService.read`, which lists MIOs (`MioDao`), takes the newest ingest per MIO (`MioIngestLogDao.list` with `limit=1`), and lists that ingest's executions (`AppWfExecLogDao.list` by `mios_ingest_log_id`). `ApiObjectsFactory` includes the router with **no** callback-secret dependency (D59, D61). No migration.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, pytest, `uv`, import-linter; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0010-read-mio-status-design.md`. Decisions: D5, D6, D26, D29, D32, D33, D37, D45, D54, D58, D59, D61 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there. All paths below are relative to it, except the plan and spec paths.
- Endpoint exactly: `GET /mios/status`, router prefix `/mios`, tag `mios`, response 200 with a JSON list of `MioStatusOut`.
- Names exactly: `MioStatusEntry`, `MioStatusIngest`, `MioStatusReq`, `MioStatusResp`, `MioStatusCtx` (`app/core/common/dtos/mio_status_dtos.py`); `MioStatusFacadeCtx` (`app/core/common/dtos/mio_status_facade_dtos.py`); `MioStatusService`, `MioStatusServiceImpl`; `MioStatusFacade`, `MioStatusFacadeTask`, `MioStatusCallServiceTask`, `MioStatusFacadeImpl`; `MioStatusApi`; models `MioStatusListReq`, `MioStatusIngestOut`, `MioStatusOut`; reuse `AppWfExecLogOut` from `app/api/models/wf_exec_callback_models.py`; factory methods `ServicesObjectsFactory.get_mio_status_service()`, `FacadesObjectsFactory.get_mio_status_facade()`, `ApiObjectsFactory.get_mio_status_api()`.
- Optional query `mio_id` only; blank/whitespace → INVALID_INPUT (422 `invalid request`); unknown → NOT_FOUND (404 `mio not found`); anything else non-SUCCESS → 500 `request failed`. No callback secret on this router.
- `latest_ingest` is the newest ingest for the MIO or `null`; its `executions` are every exec-log row of that ingest (newest first). `config_used` is never returned.
- Every class in `api`, `facades`, `services` is a singleton (`SingletonMeta` through its interface, D26) and handed out by its package's `objects_factory` in the task that adds it; no `init()` (D45 is after the MVP, D54).
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`, `list`... (D5, D37, enforced by `tests/test_ctx_only_signatures.py`). The endpoint takes one `MioStatusListReq`.
- The api package imports only `app.core.common` and facade interfaces and factories; facades import services through `ServicesObjectsFactory`; only `dao/impl` imports SQLAlchemy (`uv run lint-imports`: `Contracts: 7 kept, 0 broken.`).
- `openapi.json` is regenerated with `uv run python scripts/export_openapi.py` in the task that adds the route (D32; `tests/test_openapi_spec.py` compares it).
- The seed (migration `0006`) has four MIOs named `Customer complaints {3,6,9,12} months 2026` in every migrated test database; test workflows use the prefix `t_`.
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35). Never commit a `.env`.
- Commit with `/ccaa-commit-push 45` (it checks lint and tests, writes the `M02-0010 #45: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/dtos/mio_status_dtos.py` (create) | Req, Resp, Ctx, entry and ingest shapes of the service |
| `app/core/common/dtos/mio_status_facade_dtos.py` (create) | the facade ctx |
| `app/core/services/mio_status_service.py` (create) | the service interface |
| `app/core/services/impl/mio_status_service_impl.py` (create) | list MIOs, latest ingest, executions |
| `app/core/services/objects_factory.py` (modify) | `get_mio_status_service()` |
| `app/core/facades/mio_status_facade.py`, `app/core/facades/mio_status_facade_task.py` (create) | the facade and task interfaces |
| `app/core/facades/impl/mio_status_facade_impl.py`, `app/core/facades/impl/tasks/mio_status_call_service_task.py` (create) | the facade and its one task |
| `app/core/facades/objects_factory.py` (modify) | `get_mio_status_facade()` |
| `app/api/models/mio_status_models.py` (create) | query request and response models |
| `app/api/routers/mio_status_api.py` (create) | the router class and the HTTP mapping |
| `app/api/objects_factory.py` (modify) | `get_mio_status_api()`; includes the router without the secret |
| `openapi.json` (regenerate) | the new path and schemas |
| `tests/test_mio_status_service.py`, `tests/test_mio_status_api.py` (create) | service, facade and HTTP tests |
| `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | singletons; the flow on Postgres |
| `DESIGN.md`, `ARCHITECTURE.md` (modify) | marks the read-status endpoint as built |

---

### Task 1: the service, the facade and their factories

**Files:**
- Create: `app/core/common/dtos/mio_status_dtos.py`, `app/core/common/dtos/mio_status_facade_dtos.py`, `app/core/services/mio_status_service.py`, `app/core/services/impl/mio_status_service_impl.py`, `app/core/facades/mio_status_facade.py`, `app/core/facades/mio_status_facade_task.py`, `app/core/facades/impl/mio_status_facade_impl.py`, `app/core/facades/impl/tasks/mio_status_call_service_task.py`
- Modify: `app/core/services/objects_factory.py`, `app/core/facades/objects_factory.py`
- Test: `tests/test_mio_status_service.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Consumes: `MioDao.get/list`, `MioIngestLogDao.list` (`mio_id`, `limit=1`), `AppWfExecLogDao.list` (`mios_ingest_log_id`), all through `DaoObjectsFactory`.
- Produces: `MioStatusReq(mio_id)`, `MioStatusIngest` (ingest fields + `executions: list[AppWfExecLogRecord]`), `MioStatusEntry` (mio fields + `latest_ingest`), `MioStatusResp(entries, code)`, `MioStatusCtx`; `MioStatusFacadeCtx`; `FacadesObjectsFactory.get_mio_status_facade().read(ctx) -> int`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mio_status_service.py`:

```python
"""Every MIO with the status of its latest ingest and that ingest's executions (D61)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_NAMES = [
    "Customer complaints 12 months 2026",
    "Customer complaints 3 months 2026",
    "Customer complaints 6 months 2026",
    "Customer complaints 9 months 2026",
]
SEEDED_3M = "Customer complaints 3 months 2026"


def _read(req: MioStatusReq | None = None) -> MioStatusCtx:
    ctx = MioStatusCtx(req=req or MioStatusReq())
    ServicesObjectsFactory.get_mio_status_service().read(ctx)
    return ctx


@pytest.fixture
def workflow_id(data_dir):
    ctx = AppWfCtx(req=AppWfReq(workflow_name="t_status", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def seeded_3m_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_3M))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    return mio.resp.records[0].id


def test_every_seeded_mio_appears_ordered_by_name_with_no_ingest(data_dir):
    ctx = _read()
    assert ctx.resp.code == SUCCESS
    assert [e.name for e in ctx.resp.entries] == SEEDED_NAMES
    assert all(e.latest_ingest is None for e in ctx.resp.entries)


def test_latest_ingest_and_its_executions_are_nested(seeded_3m_id, workflow_id):
    older = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="old"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(older) == SUCCESS
    newer = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="new"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(newer) == SUCCESS
    newer_id = newer.resp.records[0].id
    first = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=newer_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(first) == SUCCESS
    second = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=newer_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(second) == SUCCESS

    ctx = _read()
    assert ctx.resp.code == SUCCESS
    entry = next(e for e in ctx.resp.entries if e.id == seeded_3m_id)
    assert entry.latest_ingest is not None
    assert (entry.latest_ingest.id, entry.latest_ingest.message) == (newer_id, "new")
    assert [x.id for x in entry.latest_ingest.executions] == [second.resp.records[0].id, first.resp.records[0].id]
    others = [e for e in ctx.resp.entries if e.id != seeded_3m_id]
    assert all(e.latest_ingest is None for e in others)


def test_an_ingest_without_executions_has_an_empty_list(seeded_3m_id):
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    ctx = _read(MioStatusReq(mio_id=seeded_3m_id))
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].latest_ingest.executions == []


def test_mio_id_returns_one_entry(seeded_3m_id):
    ctx = _read(MioStatusReq(mio_id=seeded_3m_id))
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].id == seeded_3m_id
    assert ctx.resp.entries[0].latest_ingest is None


def test_unknown_mio_id_is_not_found(data_dir):
    assert _read(MioStatusReq(mio_id="no-such-mio")).resp.code == NOT_FOUND


@pytest.mark.parametrize("mio_id", ["", "   "])
def test_blank_mio_id_is_invalid(data_dir, mio_id):
    assert _read(MioStatusReq(mio_id=mio_id)).resp.code == INVALID_INPUT


def test_the_facade_hands_the_read_on(seeded_3m_id):
    ctx = MioStatusFacadeCtx(req=MioStatusReq(mio_id=seeded_3m_id))
    assert FacadesObjectsFactory.get_mio_status_facade().read(ctx) == SUCCESS
    assert ctx.resp.code == SUCCESS
    assert len(ctx.resp.entries) == 1
    assert ctx.resp.entries[0].id == seeded_3m_id
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_mio_status_service.py -v`
Expected: FAIL with `ModuleNotFoundError` for `mio_status_dtos` (or the service factory method missing).

- [ ] **Step 3: Write the DTOs, service, facade and factories**

Create `app/core/common/dtos/mio_status_dtos.py`:

```python
"""Ctx, Req and Resp of the MIO status service: every MIO with its latest ingest and that ingest's executions
(DESIGN.md D61)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogRecord
from app.core.common.return_codes import SUCCESS


@dataclass
class MioStatusIngest:
    id: str
    mio_id: str
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    rows_loaded: int | None
    batch_count: int | None
    increment_marker: str | None
    executions: list[AppWfExecLogRecord] = field(default_factory=list)


@dataclass
class MioStatusEntry:
    id: str
    name: str
    description: str | None
    latest_ingest: MioStatusIngest | None = None


@dataclass
class MioStatusReq:
    """Optional mio_id: when given, only that MIO. None means every MIO."""

    mio_id: str | None = None


@dataclass
class MioStatusResp:
    entries: list[MioStatusEntry] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class MioStatusCtx:
    req: MioStatusReq = field(default_factory=MioStatusReq)
    resp: MioStatusResp = field(default_factory=MioStatusResp)
```

Create `app/core/common/dtos/mio_status_facade_dtos.py`:

```python
"""Ctx of the MIO status facade. Reuses the service's Req and Resp; carries the service ctx as status_ctx."""

from dataclasses import dataclass, field

from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq, MioStatusResp


@dataclass
class MioStatusFacadeCtx:
    req: MioStatusReq = field(default_factory=MioStatusReq)
    resp: MioStatusResp = field(default_factory=MioStatusResp)
    status_ctx: MioStatusCtx = field(default_factory=MioStatusCtx)
```

Create `app/core/services/mio_status_service.py`:

```python
"""Interface of the service that reads every MIO with its latest ingest status (DESIGN.md D61)."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_dtos import MioStatusCtx
from app.core.common.singleton import SingletonMeta


class MioStatusService(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioStatusCtx and returns an integer code
    (app.core.common.return_codes), also written to ctx.resp.code."""

    @abstractmethod
    def read(self, ctx: MioStatusCtx) -> int:
        """Optional req.mio_id. Returns every MIO (or that one) ordered by name, each with its newest ingest and
        that ingest's executions (newest first). latest_ingest is None when the MIO has never been ingested.
        INVALID_INPUT for a blank mio_id; NOT_FOUND for an unknown mio_id; SUCCESS with entries otherwise."""
```

Create `app/core/services/impl/mio_status_service_impl.py`:

```python
"""Builds one status entry per MIO from the catalog and the two logs (D61)."""

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq, MioRecord
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq, MioIngestLogRecord
from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusEntry, MioStatusIngest
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.mio_status_service import MioStatusService


class MioStatusServiceImpl(MioStatusService):
    def read(self, ctx: MioStatusCtx) -> int:
        mios, code = self._mios(ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        entries: list[MioStatusEntry] = []
        for mio in mios:
            ingest, code = self._latest_ingest(mio)
            if code != SUCCESS:
                ctx.resp.code = code
                return code
            entries.append(
                MioStatusEntry(id=mio.id, name=mio.name, description=mio.description, latest_ingest=ingest)
            )
        ctx.resp.entries = entries
        ctx.resp.code = SUCCESS
        return SUCCESS

    @staticmethod
    def _mios(ctx: MioStatusCtx) -> tuple[list[MioRecord], int]:
        mio_id = ctx.req.mio_id
        if mio_id is not None:
            if not str(mio_id).strip():
                return [], INVALID_INPUT
            dao_ctx = MioCtx(req=MioReq(id=str(mio_id).strip()))
            code = DaoObjectsFactory.get_mio_dao().get(dao_ctx)
            return (dao_ctx.resp.records, code) if code == SUCCESS else ([], code)
        dao_ctx = MioCtx()
        code = DaoObjectsFactory.get_mio_dao().list(dao_ctx)
        return (dao_ctx.resp.records, code) if code == SUCCESS else ([], code)

    @staticmethod
    def _latest_ingest(mio: MioRecord) -> tuple[MioStatusIngest | None, int]:
        ingest_ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.id, limit=1))
        code = DaoObjectsFactory.get_mio_ingest_log_dao().list(ingest_ctx)
        if code != SUCCESS:
            return None, FAILURE
        if not ingest_ctx.resp.records:
            return None, SUCCESS
        record = ingest_ctx.resp.records[0]
        executions, code = MioStatusServiceImpl._executions(record)
        if code != SUCCESS:
            return None, code
        return (
            MioStatusIngest(
                id=record.id,
                mio_id=record.mio_id,
                status=record.status,
                message=record.message,
                requested_at=record.requested_at,
                started_at=record.started_at,
                finished_at=record.finished_at,
                rows_loaded=record.rows_loaded,
                batch_count=record.batch_count,
                increment_marker=record.increment_marker,
                executions=executions,
            ),
            SUCCESS,
        )

    @staticmethod
    def _executions(ingest: MioIngestLogRecord) -> tuple[list, int]:
        exec_ctx = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=ingest.id))
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().list(exec_ctx)
        if code != SUCCESS:
            return [], FAILURE
        return exec_ctx.resp.records, SUCCESS
```

Create `app/core/facades/mio_status_facade.py`:

```python
"""Interface of the MIO status facade (the portal's read-status call, D61). The API depends on this, never on
facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class MioStatusFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioStatusFacadeCtx and returns an integer
    code (app.core.common.return_codes), also written to ctx.resp.code. The facade only runs its tasks in order and
    stops at the first task that does not return SUCCESS."""

    @abstractmethod
    def read(self, ctx: MioStatusFacadeCtx) -> int:
        """Read every MIO (or one) with its latest ingest and executions (ctx.req). Codes and entries are those of
        MioStatusService.read."""
```

Create `app/core/facades/mio_status_facade_task.py`:

```python
"""The task interface dedicated to the MIO status facade. Every task of this facade implements it."""

from abc import abstractmethod

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class MioStatusFacadeTask(metaclass=SingletonMeta):
    """A singleton (every task is), so a task keeps no state of its own: what it needs is in the ctx."""

    @abstractmethod
    def execute(self, ctx: MioStatusFacadeCtx) -> int:
        """Do one step. Return SUCCESS to let the next task run, any other code to stop the facade."""
```

Create `app/core/facades/impl/tasks/mio_status_call_service_task.py`:

```python
"""Hands the read to the service and puts the service's response on the facade ctx."""

from app.core.common.dtos.mio_status_dtos import MioStatusCtx
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.facades.mio_status_facade_task import MioStatusFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class MioStatusCallServiceTask(MioStatusFacadeTask):
    def execute(self, ctx: MioStatusFacadeCtx) -> int:
        ctx.status_ctx = MioStatusCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_mio_status_service().read(ctx.status_ctx)
        ctx.resp = ctx.status_ctx.resp
        return code
```

Create `app/core/facades/impl/mio_status_facade_impl.py`:

```python
"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.tasks.mio_status_call_service_task import MioStatusCallServiceTask
from app.core.facades.mio_status_facade import MioStatusFacade


class MioStatusFacadeImpl(MioStatusFacade):
    def __init__(self):
        self._tasks = [MioStatusCallServiceTask()]

    def read(self, ctx: MioStatusFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
```

In `app/core/services/objects_factory.py`, add the import of `MioStatusService` next to the other service imports, and add:

```python
    @staticmethod
    def get_mio_status_service() -> MioStatusService:
        from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl

        return MioStatusServiceImpl()
```

In `app/core/facades/objects_factory.py`, add the import of `MioStatusFacade` next to the other facade imports, and add:

```python
    @staticmethod
    def get_mio_status_facade() -> MioStatusFacade:
        from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl

        return MioStatusFacadeImpl()
```

In `tests/test_singletons.py`:

- Add imports: `MioStatusApi` is not yet created — only add service/facade ones now:
  - `from app.core.facades.impl.tasks.mio_status_call_service_task import MioStatusCallServiceTask`
  - `from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl`
  - `from app.core.facades.mio_status_facade import MioStatusFacade`
  - `from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl`
  - `from app.core.services.mio_status_service import MioStatusService`
- In the `for getter, interface in (` tuple, add:
  - `(ServicesObjectsFactory.get_mio_status_service, MioStatusService),`
  - `(FacadesObjectsFactory.get_mio_status_facade, MioStatusFacade),`
- In `test_the_classes_themselves_are_singletons`, add:
  - `assert MioStatusServiceImpl() is MioStatusServiceImpl()`
  - `assert MioStatusFacadeImpl() is MioStatusFacadeImpl()`
  - add `MioStatusCallServiceTask` to the `for task in (` tuple.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_mio_status_service.py tests/test_singletons.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 45` with summary `mio status service and facade` and files `app/core/common/dtos/mio_status_dtos.py app/core/common/dtos/mio_status_facade_dtos.py app/core/services/mio_status_service.py app/core/services/impl/mio_status_service_impl.py app/core/services/objects_factory.py app/core/facades/mio_status_facade.py app/core/facades/mio_status_facade_task.py app/core/facades/impl/mio_status_facade_impl.py app/core/facades/impl/tasks/mio_status_call_service_task.py app/core/facades/objects_factory.py tests/test_mio_status_service.py tests/test_singletons.py docs/Superpowers/specs/M02-0010-read-mio-status-design.md docs/Superpowers/plans/M02-0010-read-mio-status-plan.md Middleware/ConsumerComplaintsHandsOn/DESIGN.md docs/Project_Management/Issues/Milestone_02.md`.

---

### Task 2: the API, models, wiring, OpenAPI and HTTP tests

**Files:**
- Create: `app/api/models/mio_status_models.py`, `app/api/routers/mio_status_api.py`, `tests/test_mio_status_api.py`
- Modify: `app/api/objects_factory.py`, `tests/test_singletons.py`, `openapi.json` (regenerate)

**Interfaces:**
- Consumes: `FacadesObjectsFactory.get_mio_status_facade().read`, `MioStatusFacadeCtx`, `MioStatusReq`, `AppWfExecLogOut`.
- Produces: `GET /mios/status` returning `list[MioStatusOut]`; `ApiObjectsFactory.get_mio_status_api()`.

- [ ] **Step 1: Write the failing HTTP tests**

Create `tests/test_mio_status_api.py`:

```python
"""GET /mios/status through HTTP (D61): the portal's read of every MIO with its latest ingest and executions."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SEEDED_NAMES = [
    "Customer complaints 12 months 2026",
    "Customer complaints 3 months 2026",
    "Customer complaints 6 months 2026",
    "Customer complaints 9 months 2026",
]
SEEDED_3M = "Customer complaints 3 months 2026"
URL = "/mios/status"


@pytest.fixture
def seeded_3m_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_3M))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    return mio.resp.records[0].id


def test_lists_every_seeded_mio_with_null_ingest(client):
    response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert [row["name"] for row in body] == SEEDED_NAMES
    assert all(row["latest_ingest"] is None for row in body)


def test_nests_latest_ingest_and_executions(client, seeded_3m_id):
    older = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="old"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(older) == SUCCESS
    newer = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="new", rows_loaded=10))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(newer) == SUCCESS
    newer_id = newer.resp.records[0].id
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_api_status", engine_type="apache_airflow", engine_workflow_id="d"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS
    execution = AppWfExecLogCtx(
        req=AppWfExecLogReq(workflow_id=workflow.resp.records[0].id, mios_ingest_log_id=newer_id)
    )
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS

    body = client.get(URL).json()
    entry = next(row for row in body if row["id"] == seeded_3m_id)
    ingest = entry["latest_ingest"]
    assert (ingest["id"], ingest["message"], ingest["rows_loaded"]) == (newer_id, "new", 10)
    assert len(ingest["executions"]) == 1
    assert ingest["executions"][0]["id"] == execution.resp.records[0].id
    assert "config_used" not in ingest["executions"][0]


def test_mio_id_filter_returns_one(client, seeded_3m_id):
    response = client.get(URL, params={"mio_id": seeded_3m_id})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == seeded_3m_id


def test_unknown_mio_id_is_404(client):
    response = client.get(URL, params={"mio_id": "no-such-mio"})
    assert response.status_code == 404
    assert response.json() == {"detail": "mio not found"}


def test_blank_mio_id_is_422(client):
    response = client.get(URL, params={"mio_id": "   "})
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid request"}


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.get(URL).status_code == 200


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/mios/status" in spec["paths"]
    assert "get" in spec["paths"]["/mios/status"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_mio_status_api.py -v`
Expected: FAIL (404 on `/mios/status` or import error for the models/router).

- [ ] **Step 3: Write the models, router and factory wiring**

Create `app/api/models/mio_status_models.py`:

```python
"""Request and response models of GET /mios/status (D61; these produce the OpenAPI schema).

The endpoint takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.models.wf_exec_callback_models import AppWfExecLogOut


class MioStatusListReq(BaseModel):
    """Optional query: mio_id selects one MIO."""

    mio_id: str | None = None


class MioStatusIngestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mio_id: str
    status: str
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    executions: list[AppWfExecLogOut] = []


class MioStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    latest_ingest: MioStatusIngestOut | None = None
```

Create `app/api/routers/mio_status_api.py`:

```python
"""The portal's read of every MIO with its latest ingest status, as a class (D29, D61). It is a singleton.

No callback secret: the portal calls this from a browser (D59). Methods are plain `def` so FastAPI runs the blocking
database calls in a worker thread.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.models.mio_status_models import MioStatusIngestOut, MioStatusListReq, MioStatusOut
from app.api.models.wf_exec_callback_models import AppWfExecLogOut
from app.core.common.dtos.mio_status_dtos import MioStatusEntry, MioStatusReq
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class MioStatusApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/mios", tags=["mios"])
        self.router.add_api_route(
            "/status",
            self.list_status,
            methods=["GET"],
            response_model=list[MioStatusOut],
        )

    def list_status(self, req: Annotated[MioStatusListReq, Query()]) -> list[MioStatusOut]:
        ctx = MioStatusFacadeCtx(req=MioStatusReq(mio_id=req.mio_id))
        FacadesObjectsFactory.get_mio_status_facade().read(ctx)
        self._check(ctx)
        return [self._entry(e) for e in ctx.resp.entries]

    @staticmethod
    def _entry(entry: MioStatusEntry) -> MioStatusOut:
        ingest = entry.latest_ingest
        return MioStatusOut(
            id=entry.id,
            name=entry.name,
            description=entry.description,
            latest_ingest=(
                None
                if ingest is None
                else MioStatusIngestOut(
                    id=ingest.id,
                    mio_id=ingest.mio_id,
                    status=ingest.status,
                    message=ingest.message,
                    rows_loaded=ingest.rows_loaded,
                    batch_count=ingest.batch_count,
                    increment_marker=ingest.increment_marker,
                    requested_at=ingest.requested_at,
                    started_at=ingest.started_at,
                    finished_at=ingest.finished_at,
                    executions=[AppWfExecLogOut.model_validate(x) for x in ingest.executions],
                )
            ),
        )

    @staticmethod
    def _check(ctx: MioStatusFacadeCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "mio not found")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
```

In `app/api/objects_factory.py`:

- Update the module docstring to mention the MIO status API (D61) alongside the callback.
- Add: `from app.api.routers.mio_status_api import MioStatusApi`
- Add:

```python
    @staticmethod
    def get_mio_status_api() -> MioStatusApi:
        return MioStatusApi()
```

- In `_build_app`, after including `DataIngestApi().router` and **before** the protected callback router, add:

```python
        # Portal endpoints stay open (no callback secret): the browser cannot keep a shared secret (D59, D61).
        app.include_router(ApiObjectsFactory.get_mio_status_api().router)
```

In `tests/test_singletons.py`:

- Add `from app.api.routers.mio_status_api import MioStatusApi`
- In `test_factories_return_the_same_object_typed_as_the_interface`, after the wf_exec_callback_api asserts, add:

```python
    assert ApiObjectsFactory.get_mio_status_api() is ApiObjectsFactory.get_mio_status_api()
    assert isinstance(ApiObjectsFactory.get_mio_status_api(), MioStatusApi)
```

- In `test_the_classes_themselves_are_singletons`, add `assert MioStatusApi() is MioStatusApi()`.

- [ ] **Step 4: Regenerate OpenAPI and run the tests**

Run:

```bash
uv run python scripts/export_openapi.py
uv run pytest tests/test_mio_status_api.py tests/test_singletons.py tests/test_openapi_spec.py tests/test_callback_secret_api.py tests/test_ctx_only_signatures.py tests/test_import_contracts.py -v
uv run lint-imports
```

Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 45` with summary `GET /mios/status for the portal` and files `app/api/models/mio_status_models.py app/api/routers/mio_status_api.py app/api/objects_factory.py openapi.json tests/test_mio_status_api.py tests/test_singletons.py`.

---

### Task 3: Postgres, design notes and full suite

**Files:**
- Modify: `tests/test_postgres.py`, `DESIGN.md`, `ARCHITECTURE.md`

**Interfaces:**
- Consumes: `ServicesObjectsFactory.get_mio_status_service().read(ctx)` and the DTOs from Task 1.

- [ ] **Step 1: Write the Postgres test**

In `tests/test_postgres.py`, add directly below the existing `wf_exec_status` imports:

```python
from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq
```

Then append at the end of the file:

```python


def test_mio_status_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    mio = MioCtx(req=MioReq(name="t_read_status_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    mio_id = mio.resp.records[0].id
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, message="live"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    made = AppWfCtx(req=AppWfReq(workflow_name="w_read", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    execution = AppWfExecLogCtx(
        req=AppWfExecLogReq(workflow_id=made.resp.records[0].id, mios_ingest_log_id=ingest.resp.records[0].id)
    )
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS

    ctx = MioStatusCtx(req=MioStatusReq(mio_id=mio_id))
    assert ServicesObjectsFactory.get_mio_status_service().read(ctx) == SUCCESS
    assert len(ctx.resp.entries) == 1
    entry = ctx.resp.entries[0]
    assert entry.id == mio_id
    assert entry.latest_ingest is not None
    assert entry.latest_ingest.message == "live"
    assert [x.id for x in entry.latest_ingest.executions] == [execution.resp.records[0].id]
    missing = MioStatusCtx(req=MioStatusReq(mio_id="missing"))
    assert ServicesObjectsFactory.get_mio_status_service().read(missing) == NOT_FOUND
```

Ensure `NOT_FOUND` is already imported from `return_codes` in that file (it is). Ensure `ServicesObjectsFactory` is imported (it is, for the wf_exec_status test).

- [ ] **Step 2: Run it without Postgres**

Run: `uv run pytest tests/test_postgres.py::test_mio_status_service_works_on_postgres -v`
Expected: SKIPPED (`CCA_TEST_POSTGRES_URL is not set`).

- [ ] **Step 3: Mark the endpoint as built in the design**

In `DESIGN.md`, section `### 4.2 Endpoints`, in the Read status table row (already updated by D61), ensure it still says designed/built consistently. Replace any remaining "Designed in story #45" in the D61 decision **Why** column is fine; in the D61 decision text itself, change `Designed in story #45.` to:

```
Built in story #45 (`MioStatusApi`, `MioStatusFacade`, `MioStatusService`; spec `docs/Superpowers/specs/M02-0010-read-mio-status-design.md`).
```

In `ARCHITECTURE.md`, section that mentions the portal reading status (near "the portal reads the status through the API"), add after that sentence if not already present:

```
`GET /mios/status` returns every MIO with its latest ingest and that ingest's executions (D61); it needs no callback secret.
```

- [ ] **Step 4: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; `380 passed, 10 skipped`. Include `tests/test_portability.py` (it scans the `.md` files).

Optional Postgres container check (same pattern as M02-0008):

```bash
docker run -d --name cca-pg-0010 -e POSTGRES_PASSWORD=postgres -p 55439:5432 postgres:16
sleep 7
CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55439/postgres uv run pytest -q
docker rm -f cca-pg-0010
```

Expected: every test PASS (nothing skipped). Always run `docker rm -f cca-pg-0010`, also after a failure.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 45` with summary `mio status on Postgres and design notes` and files `tests/test_postgres.py DESIGN.md ARCHITECTURE.md`.

---

## Self-Review (done)

1. **Spec coverage:** naming (Global Constraints, all tasks); `GET /mios/status`, list response, nested `latest_ingest` + `executions`, null ingest, empty catalog via seed-with-no-ingests (Tasks 1–2); optional `mio_id`, 404/422/500 (Tasks 1–2); no callback secret (Task 2); layering API → facade → service → DAOs (Tasks 1–2); singletons and factories (Tasks 1–2, D26); OpenAPI (Task 2); Postgres (Task 3); DESIGN/ARCHITECTURE (Task 3). D61, Milestone next-number D62, and the section 3 / 4.2 edits were written with the spec. Out of scope and not built: path-by-id, pagination, historical ingests, read transaction, portal UI (#64).
2. **Placeholders:** none; every code step shows the full file or names the exact insertion point.
3. **Types and names:** `MioStatusReq/Resp/Ctx/Entry/Ingest`, `MioStatusFacadeCtx.status_ctx`, `MioStatusService.read`, `MioStatusFacade.read`, `MioStatusCallServiceTask`, `MioStatusApi.list_status`, `MioStatusListReq`, `MioStatusOut`, `MioStatusIngestOut`, `AppWfExecLogOut`, the three factory methods, and the details `mio not found` / `invalid request` / `request failed` are spelled the same in every task and in the spec.
4. **Pre-check:** the code of Tasks 1 to 3 was run in a scratch copy of the app root under `runtime_data/tmp/` (deleted afterwards): `lint-imports` 7 kept, 0 broken; SQLite suite `380 passed, 10 skipped` (364 before, plus 8 service/facade tests, 8 HTTP tests, and one more Postgres test skipped). `_entry` must annotate `entry: MioStatusEntry` or `tests/test_ctx_only_signatures.py` fails.
5. **Accepted gaps (from the spec):** no shared read transaction across the three DAOs; no `config_used`; no historical ingest list; no path-param single-MIO route.
