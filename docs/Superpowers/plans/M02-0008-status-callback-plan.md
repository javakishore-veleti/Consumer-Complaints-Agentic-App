# M02-0008 (#43) Airflow status callback endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `POST /callbacks/workflow-executions/{execution_id}/status`, protected by the callback secret, changes the execution log row and its MIO ingest row in one transaction, so duplicate, out-of-order and late Airflow calls are harmless.

**Architecture:** `WfExecCallbackApi` (a singleton router class, D29) builds a `WfExecStatusFacadeCtx` from its one request object and calls `WfExecStatusFacade`; the facade's one task calls `WfExecStatusService`, which opens a transaction through the `TransactionDao` (D39), updates the execution with `AppWfExecLogDao.update` (D30 rules, story #82), works out where the ingest row follows (D60) and updates it with `MioIngestLogDao.update` (story #87), then commits or rolls back. `ApiObjectsFactory` includes the router with the `CallbackSecretAuth` dependency (D59). No migration.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, pytest, `uv`, import-linter; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0008-status-callback-design.md`. Decisions: D5, D6, D26, D29, D30, D32, D33, D37, D39, D45, D54, D58, D59, D60 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there. All paths below are relative to it, except the plan and spec paths.
- Endpoint exactly: `POST /callbacks/workflow-executions/{execution_id}/status`, router prefix `/callbacks`, tag `callbacks`, response 200 with `{"execution": {...}, "ingest": {...} | null}`.
- Names exactly: `WfExecStatusReq`, `WfExecStatusResp`, `WfExecStatusCtx` (`app/core/common/dtos/wf_exec_status_dtos.py`); `WfExecStatusFacadeCtx` (`app/core/common/dtos/wf_exec_status_facade_dtos.py`); `WfExecStatusService`, `WfExecStatusServiceImpl`; `WfExecStatusFacade`, `WfExecStatusFacadeTask`, `WfExecStatusCallServiceTask`, `WfExecStatusFacadeImpl`; `WfExecCallbackApi`; models `WfExecStatusReport`, `WfExecStatusReportReq`, `AppWfExecLogOut`, `MioIngestLogOut`, `WfExecStatusOut`; factory methods `ServicesObjectsFactory.get_wf_exec_status_service()`, `FacadesObjectsFactory.get_wf_exec_status_facade()`, `ApiObjectsFactory.get_wf_exec_callback_api()`.
- Reported statuses are `started`, `completed`, `failed` only; `requested` is INVALID_INPUT (422).
- Error mapping: NOT_FOUND 404 `workflow execution not found`; CONFLICT 409 `status change not allowed in the current state`; INVALID_INPUT 422 `invalid request`; anything else 500 `request failed`; 401 comes from `CallbackSecretAuth`. 404 and 409 always describe the execution: a non-SUCCESS from the ingest side other than INVALID_INPUT becomes FAILURE.
- The ingest rule (D60): target = the execution's status after its update; for `completed` only when every execution of the ingest is `completed`; the target is used only when it is in `ExecStatus(ingest.status).next_statuses`, else the ingest's status is left alone. The callback's `message` goes to the ingest only with a target; `rows_loaded`, `batch_count`, `increment_marker` go to the ingest on every call; none of it is written for an execution without an ingest.
- Execution and ingest change in ONE transaction: `TransactionDao.begin`, the `TransactionCtx` on every DAO ctx, `commit` only when every step returned SUCCESS, else `rollback`.
- Every class in `api`, `facades`, `services` is a singleton (`SingletonMeta` through its interface, D26) and handed out by its package's `objects_factory` in the task that adds it; no `init()` (D45 is after the MVP, D54).
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`, `list`... (D5, D37, enforced by `tests/test_ctx_only_signatures.py`, which scans `app`, `alembic`, `scripts` and `main.py`). The endpoint takes one `WfExecStatusReportReq`.
- The api package imports only `app.core.common` and facade interfaces and factories; facades import services through `ServicesObjectsFactory`; only `dao/impl` imports SQLAlchemy (`uv run lint-imports`: `Contracts: 7 kept, 0 broken.`).
- `openapi.json` is regenerated with `uv run python scripts/export_openapi.py` in the task that adds the route (D32; `tests/test_openapi_spec.py` compares it).
- The seed (migration `0006`) has the MIO `Customer complaints 3 months 2026` in every migrated test database; test workflows use the prefix `t_`.
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35). Never commit a `.env`.
- Commit with `/ccaa-commit-push 43` (it checks lint and tests, writes the `M02-0008 #43: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/dtos/wf_exec_status_dtos.py` (create) | Req, Resp, Ctx of the service |
| `app/core/common/dtos/wf_exec_status_facade_dtos.py` (create) | the facade ctx |
| `app/core/services/wf_exec_status_service.py` (create) | the service interface and its contract |
| `app/core/services/impl/wf_exec_status_service_impl.py` (create) | the transaction and the ingest rule |
| `app/core/services/objects_factory.py` (modify) | `get_wf_exec_status_service()` |
| `app/core/facades/wf_exec_status_facade.py`, `app/core/facades/wf_exec_status_facade_task.py` (create) | the facade and task interfaces |
| `app/core/facades/impl/wf_exec_status_facade_impl.py`, `app/core/facades/impl/tasks/wf_exec_status_call_service_task.py` (create) | the facade and its one task |
| `app/core/facades/objects_factory.py` (modify) | `get_wf_exec_status_facade()` |
| `app/api/models/wf_exec_callback_models.py` (create) | body, request, response models |
| `app/api/routers/wf_exec_callback_api.py` (create) | the router class and the HTTP mapping |
| `app/api/objects_factory.py` (modify) | `get_wf_exec_callback_api()`; includes the router with the secret check |
| `openapi.json` (regenerate) | the new path and schemas |
| `tests/test_wf_exec_status_service.py`, `tests/test_wf_exec_callback_api.py` (create) | service, facade and HTTP tests |
| `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | singletons; the flow on Postgres |
| `DESIGN.md`, `ARCHITECTURE.md` (modify) | marks the callback as built |

---

### Task 1: the service, the facade and their factories

**Files:**
- Create: `app/core/common/dtos/wf_exec_status_dtos.py`, `app/core/common/dtos/wf_exec_status_facade_dtos.py`, `app/core/services/wf_exec_status_service.py`, `app/core/services/impl/wf_exec_status_service_impl.py`, `app/core/facades/wf_exec_status_facade.py`, `app/core/facades/wf_exec_status_facade_task.py`, `app/core/facades/impl/wf_exec_status_facade_impl.py`, `app/core/facades/impl/tasks/wf_exec_status_call_service_task.py`
- Modify: `app/core/services/objects_factory.py`, `app/core/facades/objects_factory.py`
- Test: `tests/test_wf_exec_status_service.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Consumes: `AppWfExecLogDao.update/list` and `MioIngestLogDao.get/update` (their D30 rules and codes), `TransactionDao.begin/commit/rollback`, all through `DaoObjectsFactory`; `ExecStatus` and `ExecStatus.next_statuses` from `app/core/common/app_types_constants.py`.
- Produces: `WfExecStatusReq(execution_id, status, engine_run_id, message, rows_loaded, batch_count, increment_marker)`, `WfExecStatusResp(execution: AppWfExecLogRecord | None, ingest: MioIngestLogRecord | None, code: int)`, `WfExecStatusCtx(TransactionalCtx)` with `req` and `resp`; `WfExecStatusFacadeCtx(req: WfExecStatusReq, resp: WfExecStatusResp, status_ctx: WfExecStatusCtx)`; `FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx: WfExecStatusFacadeCtx) -> int` (code also in `ctx.resp.code`; rows in `ctx.resp.execution` and `ctx.resp.ingest`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wf_exec_status_service.py`:

```python
"""The status an engine reports for one execution (D60): the execution log and its MIO ingest row change together, and
duplicate, out-of-order and late reports are harmless (D30)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import SqlAlchemyMioIngestLogDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_MIO = "Customer complaints 3 months 2026"


def _report(req: WfExecStatusReq) -> WfExecStatusCtx:
    ctx = WfExecStatusCtx(req=req)
    ServicesObjectsFactory.get_wf_exec_status_service().record(ctx)
    return ctx


def _execution(execution_id):
    ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def _ingest(ingest_id):
    ctx = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


@pytest.fixture
def workflow_id(data_dir):
    ctx = AppWfCtx(req=AppWfReq(workflow_name="t_ingest", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def ingest_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def new_execution(workflow_id):
    """Creates an execution of the workflow; pass an ingest id to attach it to that ingest."""

    def create(ingest=None):
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=ingest))
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    return create


# ---- input


@pytest.mark.parametrize("status", ["requested", "running", "", None])
def test_only_started_completed_and_failed_can_be_reported(new_execution, status):
    execution_id = new_execution()
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status=status))
    assert ctx.resp.code == INVALID_INPUT
    assert (ctx.resp.execution, ctx.resp.ingest) == (None, None)
    assert _execution(execution_id).status == "requested"


@pytest.mark.parametrize("execution_id", [None, "", "   "])
def test_a_blank_execution_id_is_invalid(data_dir, execution_id):
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == INVALID_INPUT


def test_an_unknown_execution_is_not_found(data_dir):
    assert _report(WfExecStatusReq(execution_id="no-such-execution", status="started")).resp.code == NOT_FOUND


def test_a_too_long_engine_run_id_is_invalid_and_changes_nothing(new_execution):
    execution_id = new_execution()
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", engine_run_id="r" * 129))
    assert ctx.resp.code == INVALID_INPUT
    assert _execution(execution_id).status == "requested"


# ---- an execution without an ingest row


def test_an_execution_without_an_ingest_changes_only_the_execution(new_execution):
    execution_id = new_execution()
    started = _report(
        WfExecStatusReq(execution_id=execution_id, status="started", engine_run_id="run-1", rows_loaded=10)
    )
    assert started.resp.code == SUCCESS
    assert started.resp.ingest is None  # the volume fields are ignored: there is no ingest row
    assert (started.resp.execution.status, started.resp.execution.engine_run_id) == ("started", "run-1")
    assert started.resp.execution.started_at is not None
    done = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="ok"))
    assert done.resp.code == SUCCESS
    assert (done.resp.execution.status, done.resp.execution.message) == ("completed", "ok")
    assert done.resp.execution.finished_at is not None


def test_a_repeated_report_is_success_and_keeps_the_times(new_execution):
    execution_id = new_execution()
    first = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    again = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    assert again.resp.code == SUCCESS
    assert again.resp.execution.started_at == first.resp.execution.started_at


def test_an_out_of_order_report_is_a_conflict_and_changes_nothing(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="m", rows_loaded=5))
    assert ctx.resp.code == CONFLICT
    assert (ctx.resp.execution, ctx.resp.ingest) == (None, None)
    assert (_execution(execution_id).status, _execution(execution_id).message) == ("requested", None)
    assert (_ingest(ingest_id).status, _ingest(ingest_id).rows_loaded) == ("requested", None)


# ---- the ingest follows its executions


def test_started_moves_a_requested_ingest_to_started(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", message="go", batch_count=2))
    assert ctx.resp.code == SUCCESS
    assert ctx.resp.execution.status == "started"
    assert (ctx.resp.ingest.id, ctx.resp.ingest.status) == (ingest_id, "started")
    assert (ctx.resp.ingest.message, ctx.resp.ingest.batch_count) == ("go", 2)
    assert ctx.resp.ingest.started_at is not None


def test_a_second_execution_starting_leaves_a_started_ingest_and_its_message_alone(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    before = _report(WfExecStatusReq(execution_id=first, status="started", message="first")).resp.ingest
    after = _report(WfExecStatusReq(execution_id=second, status="started", message="second")).resp.ingest
    assert (after.status, after.started_at, after.message) == ("started", before.started_at, "first")


def test_completed_moves_the_ingest_only_when_every_execution_is_completed(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    for execution_id in (first, second):
        assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == SUCCESS
    one = _report(WfExecStatusReq(execution_id=first, status="completed", rows_loaded=100))
    assert one.resp.code == SUCCESS
    assert (one.resp.ingest.status, one.resp.ingest.rows_loaded) == ("started", 100)  # the volume is a note
    both = _report(WfExecStatusReq(execution_id=second, status="completed", message="all done", rows_loaded=250))
    assert both.resp.code == SUCCESS
    ingest = both.resp.ingest
    assert (ingest.status, ingest.message, ingest.rows_loaded) == ("completed", "all done", 250)
    assert ingest.finished_at is not None


def test_failed_moves_the_ingest_to_failed_with_the_message(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=first, status="started"))
    failed = _report(WfExecStatusReq(execution_id=first, status="failed", message="disk full"))
    assert failed.resp.code == SUCCESS
    assert (failed.resp.ingest.status, failed.resp.ingest.message) == ("failed", "disk full")
    assert _execution(second).status == "requested"  # other executions are not touched


def test_failed_from_requested_fails_a_requested_ingest(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="failed", message="could not start"))
    assert ctx.resp.code == SUCCESS
    assert (ctx.resp.execution.status, ctx.resp.ingest.status) == ("failed", "failed")


def test_a_final_ingest_is_left_alone_but_the_execution_moves_and_the_volume_is_written(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=first, status="failed", message="boom"))
    started = _report(WfExecStatusReq(execution_id=second, status="started", message="late"))
    assert started.resp.code == SUCCESS and started.resp.execution.status == "started"
    done = _report(WfExecStatusReq(execution_id=second, status="completed", increment_marker="2026-03-31"))
    assert done.resp.code == SUCCESS and done.resp.execution.status == "completed"
    ingest = done.resp.ingest
    assert (ingest.status, ingest.message, ingest.increment_marker) == ("failed", "boom", "2026-03-31")


def test_duplicate_reports_after_the_ingest_completed_are_success_and_change_nothing(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    first = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="done")).resp
    again = _report(WfExecStatusReq(execution_id=execution_id, status="completed"))
    assert again.resp.code == SUCCESS
    assert again.resp.ingest == first.ingest
    assert again.resp.execution.finished_at == first.execution.finished_at
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == CONFLICT
    assert _ingest(ingest_id) == first.ingest


def test_a_late_failed_after_completed_is_a_conflict_and_keeps_both_rows(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    _report(WfExecStatusReq(execution_id=execution_id, status="completed"))
    late = _report(WfExecStatusReq(execution_id=execution_id, status="failed", message="late", rows_loaded=1))
    assert late.resp.code == CONFLICT
    assert (_execution(execution_id).status, _execution(execution_id).message) == ("completed", None)
    assert (_ingest(ingest_id).status, _ingest(ingest_id).rows_loaded) == ("completed", None)


# ---- one transaction


def test_an_invalid_volume_rolls_back_the_execution_too(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", rows_loaded=-1))
    assert ctx.resp.code == INVALID_INPUT
    assert _execution(execution_id).status == "requested"
    assert _ingest(ingest_id).status == "requested"


def test_if_the_ingest_write_fails_the_execution_is_not_changed(new_execution, ingest_id, monkeypatch):
    execution_id = new_execution(ingest_id)

    def broken(self, ctx):
        raise RuntimeError("disk error")

    monkeypatch.setattr(SqlAlchemyMioIngestLogDao, "update", broken)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    assert ctx.resp.code == FAILURE and ctx.resp.execution is None
    monkeypatch.undo()
    assert _execution(execution_id).status == "requested"
    assert _ingest(ingest_id).status == "requested"


def test_an_ingest_conflict_is_a_failure_not_the_executions_conflict(new_execution, ingest_id, monkeypatch):
    execution_id = new_execution(ingest_id)
    monkeypatch.setattr(SqlAlchemyMioIngestLogDao, "update", lambda self, ctx: CONFLICT)
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == FAILURE
    monkeypatch.undo()
    assert _execution(execution_id).status == "requested"


# ---- the facade


def test_the_facade_hands_the_report_to_the_service(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id=execution_id, status="started"))
    assert FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx) == SUCCESS
    assert ctx.resp.code == SUCCESS
    assert (ctx.resp.execution.status, ctx.resp.ingest.status) == ("started", "started")
    missing = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id="no-such-execution", status="started"))
    assert FacadesObjectsFactory.get_wf_exec_status_facade().report(missing) == NOT_FOUND
    assert missing.resp.code == NOT_FOUND
```

(The nested `create(ingest=None)` and `broken(self, ctx)` live in a test file, which `tests/test_ctx_only_signatures.py` does not scan; the existing tests use the same style.)

In `tests/test_singletons.py`:

- after the line `from app.core.facades.impl.tasks.data_ingest_validate_request_task import DataIngestValidateRequestTask`, add:

```python
from app.core.facades.impl.tasks.wf_exec_status_call_service_task import WfExecStatusCallServiceTask
from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl
```

- after the line `from app.core.facades.objects_factory import FacadesObjectsFactory`, add:

```python
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade
```

- after the line `from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl`, add:

```python
from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl
```

- after the line `from app.core.services.objects_factory import ServicesObjectsFactory`, add:

```python
from app.core.services.wf_exec_status_service import WfExecStatusService
```

- in `test_factories_return_the_same_object_typed_as_the_interface`, after the line `        (ServicesObjectsFactory.get_dataset_status_service, DatasetStatusService),`, add:

```python
        (ServicesObjectsFactory.get_wf_exec_status_service, WfExecStatusService),
        (FacadesObjectsFactory.get_wf_exec_status_facade, WfExecStatusFacade),
```

- in `test_the_classes_themselves_are_singletons`, after the line `    assert DatasetStatusServiceImpl() is DatasetStatusServiceImpl()`, add:

```python
    assert WfExecStatusServiceImpl() is WfExecStatusServiceImpl()
    assert WfExecStatusFacadeImpl() is WfExecStatusFacadeImpl()
```

  and in the task tuple of the same test, after the line `        DataIngestCollectResponseTask,`, add:

```python
        WfExecStatusCallServiceTask,
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_wf_exec_status_service.py tests/test_singletons.py -v`
Expected: both files fail at collection with `ModuleNotFoundError` (`app.core.common.dtos.wf_exec_status_dtos` and `app.core.facades.impl.tasks.wf_exec_status_call_service_task`).

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/wf_exec_status_dtos.py`:

```python
"""Ctx, Req and Resp of the workflow execution status service: an engine reports a status of one execution, and the
execution log and its MIO ingest log row change together in one transaction (DESIGN.md D60)."""

from dataclasses import dataclass, field

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogRecord
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogRecord
from app.core.common.dtos.transaction_dtos import TransactionalCtx
from app.core.common.return_codes import SUCCESS


@dataclass
class WfExecStatusReq:
    """What the engine reports. A field left as None means "not given". status is started, completed or failed;
    engine_run_id and message go to the execution; rows_loaded, batch_count and increment_marker go to the ingest row
    (ignored when the execution has none)."""

    execution_id: str | None = None
    status: str | None = None
    engine_run_id: str | None = None
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None


@dataclass
class WfExecStatusResp:
    execution: AppWfExecLogRecord | None = None  # the execution after the call
    ingest: MioIngestLogRecord | None = None  # its ingest row after the call; None when it has none
    code: int = SUCCESS


@dataclass
class WfExecStatusCtx(TransactionalCtx):  # carries the transaction the service opens for the call
    req: WfExecStatusReq = field(default_factory=WfExecStatusReq)
    resp: WfExecStatusResp = field(default_factory=WfExecStatusResp)
```

Create `app/core/common/dtos/wf_exec_status_facade_dtos.py`:

```python
"""Ctx of the workflow execution status facade. The request and the response have the same shape as the service's,
so they reuse its Req and Resp; the facade ctx carries the service's own ctx as an additional member (section 2.1)."""

from dataclasses import dataclass, field

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq, WfExecStatusResp


@dataclass
class WfExecStatusFacadeCtx:
    req: WfExecStatusReq = field(default_factory=WfExecStatusReq)
    resp: WfExecStatusResp = field(default_factory=WfExecStatusResp)
    status_ctx: WfExecStatusCtx = field(default_factory=WfExecStatusCtx)
```

- [ ] **Step 4: Add the service**

Create `app/core/services/wf_exec_status_service.py`:

```python
"""Interface of the service that records a status an engine reports for one workflow execution (DESIGN.md D60)."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusService(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one WfExecStatusCtx and returns an integer code
    (app.core.common.return_codes), also written to ctx.resp.code."""

    @abstractmethod
    def record(self, ctx: WfExecStatusCtx) -> int:
        """Needs req.execution_id and req.status (started, completed or failed). Changes the execution (D30 rules,
        with engine_run_id and message) and, when it has a mios_ingest_log_id, its ingest row, in ONE transaction:
        either both change or neither does.

        The ingest row follows the execution: started moves a requested ingest to started; failed moves an ingest
        that is not final to failed; completed moves a started ingest to completed once every execution of that
        ingest is completed. Any other move is skipped, so the ingest never makes the call fail: a final ingest
        stays as it is. The callback's message goes to the ingest only when its status moves; rows_loaded,
        batch_count and increment_marker are written to the ingest on every call that gives them.

        INVALID_INPUT for a blank execution_id, any other status, or an invalid field; NOT_FOUND for an unknown
        execution; CONFLICT for a move of the execution D30 does not allow (nothing changes); the same status again
        is SUCCESS. NOT_FOUND and CONFLICT always describe the execution: when the ingest side fails any other way
        the call is FAILURE and nothing changes. resp.execution and resp.ingest hold the rows after the call."""
```

Create `app/core/services/impl/wf_exec_status_service_impl.py`:

```python
"""WfExecStatusService: the execution and its MIO ingest row change in one transaction (D39, D60).

Each step takes the ctx and returns an integer code; the first step that does not return SUCCESS stops the run and the
transaction is rolled back, otherwise it is committed. The service is a singleton and keeps no per-call state.
"""

import logging

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.wf_exec_status_service import WfExecStatusService

log = logging.getLogger(__name__)

REPORTED_STATUSES = (ExecStatus.STARTED.value, ExecStatus.COMPLETED.value, ExecStatus.FAILED.value)


class WfExecStatusServiceImpl(WfExecStatusService):
    def __init__(self):
        self._steps = [self._update_execution, self._read_ingest, self._follow_ingest]

    def record(self, ctx: WfExecStatusCtx) -> int:
        ctx.resp.execution = None
        ctx.resp.ingest = None
        if not self._is_valid_report(ctx):
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        transaction_dao = DaoObjectsFactory.get_transaction_dao()
        ctx.transaction = TransactionCtx()
        code = transaction_dao.begin(ctx.transaction)
        if code != SUCCESS:
            ctx.transaction = None
            ctx.resp.code = code
            return code
        try:
            for step in self._steps:
                code = step(ctx)
                if code != SUCCESS:
                    break
        except Exception:
            log.exception("workflow execution status report failed")
            code = FAILURE
        if code == SUCCESS:
            code = transaction_dao.commit(ctx.transaction)
        else:
            transaction_dao.rollback(ctx.transaction)
        ctx.transaction = None
        if code != SUCCESS:
            ctx.resp.execution = None
            ctx.resp.ingest = None
        ctx.resp.code = code
        return code

    # ---- steps (each takes the ctx; the shared transaction is ctx.transaction)

    @staticmethod
    def _is_valid_report(ctx: WfExecStatusCtx) -> bool:
        execution_id = ctx.req.execution_id
        has_id = isinstance(execution_id, str) and bool(execution_id.strip())
        return has_id and ctx.req.status in REPORTED_STATUSES

    @staticmethod
    def _update_execution(ctx: WfExecStatusCtx) -> int:
        req = ctx.req
        change = AppWfExecLogReq(
            id=req.execution_id, status=req.status, engine_run_id=req.engine_run_id, message=req.message
        )
        dao_ctx = AppWfExecLogCtx(req=change, transaction=ctx.transaction)
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().update(dao_ctx)
        if code == SUCCESS:
            ctx.resp.execution = dao_ctx.resp.records[0]
        return code  # NOT_FOUND, INVALID_INPUT and CONFLICT describe the execution

    @staticmethod
    def _read_ingest(ctx: WfExecStatusCtx) -> int:
        ingest_id = ctx.resp.execution.mios_ingest_log_id
        if ingest_id is None:
            return SUCCESS  # a workflow without a MIO: only the execution changes
        dao_ctx = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id), transaction=ctx.transaction)
        code = DaoObjectsFactory.get_mio_ingest_log_dao().get(dao_ctx)
        if code != SUCCESS:
            log.error("mios_ingest_log row %s of execution %s cannot be read", ingest_id, ctx.resp.execution.id)
            return FAILURE  # the reference never dangles (no delete, D58); NOT_FOUND here would describe the execution
        ctx.resp.ingest = dao_ctx.resp.records[0]
        return SUCCESS

    def _follow_ingest(self, ctx: WfExecStatusCtx) -> int:
        if ctx.resp.ingest is None:
            return SUCCESS
        req = ctx.req
        target = self._ingest_target(ctx)
        change = MioIngestLogReq(
            id=ctx.resp.ingest.id,
            status=target,
            message=req.message if target is not None else None,
            rows_loaded=req.rows_loaded,
            batch_count=req.batch_count,
            increment_marker=req.increment_marker,
        )
        dao_ctx = MioIngestLogCtx(req=change, transaction=ctx.transaction)
        code = DaoObjectsFactory.get_mio_ingest_log_dao().update(dao_ctx)
        if code == SUCCESS:
            ctx.resp.ingest = dao_ctx.resp.records[0]
            return SUCCESS
        if code == INVALID_INPUT:
            return INVALID_INPUT  # an invalid volume field
        # CONFLICT (a rival moved the ingest between the read and the write) or FAILURE: retryable, and never the
        # execution's 409.
        log.warning("mios_ingest_log row %s could not follow execution %s", change.id, ctx.resp.execution.id)
        return FAILURE

    def _ingest_target(self, ctx: WfExecStatusCtx) -> str | None:
        """The status the ingest moves to after this report, or None to leave its status as it is."""
        execution = ExecStatus(ctx.resp.execution.status)
        ingest = ExecStatus(ctx.resp.ingest.status)
        if execution == ExecStatus.COMPLETED and not self._every_execution_completed(ctx):
            return None
        return execution.value if execution in ingest.next_statuses else None

    @staticmethod
    def _every_execution_completed(ctx: WfExecStatusCtx) -> bool:
        """True when every execution of the ingest (this one included, already changed in this transaction) is
        completed."""
        req = AppWfExecLogReq(mios_ingest_log_id=ctx.resp.ingest.id)
        dao_ctx = AppWfExecLogCtx(req=req, transaction=ctx.transaction)
        if DaoObjectsFactory.get_app_wf_exec_log_dao().list(dao_ctx) != SUCCESS:
            raise RuntimeError("the executions of the ingest cannot be listed")
        return all(record.status == ExecStatus.COMPLETED.value for record in dao_ctx.resp.records)
```

Why `_every_execution_completed` raises instead of returning a code: it answers a yes/no question for `_ingest_target`; a failed list is a database fault, and `record` turns any exception into FAILURE with a rollback (the same guard as `DatasetStatusServiceImpl._run`).

Replace the whole of `app/core/services/objects_factory.py` with:

```python
"""The only module of the services package that may import from services/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.wf_exec_status_service import WfExecStatusService


class ServicesObjectsFactory:
    @staticmethod
    def get_dataset_status_service() -> DatasetStatusService:
        from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl

        return DatasetStatusServiceImpl()

    @staticmethod
    def get_wf_exec_status_service() -> WfExecStatusService:
        from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl

        return WfExecStatusServiceImpl()
```

- [ ] **Step 5: Add the facade**

Create `app/core/facades/wf_exec_status_facade.py`:

```python
"""Interface of the workflow execution status facade (the engine's status callback, D60). The API depends on this,
never on facades/impl."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusFacade(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one WfExecStatusFacadeCtx and returns an integer
    code (app.core.common.return_codes), also written to ctx.resp.code. The facade only runs its tasks in order and
    stops at the first task that does not return SUCCESS."""

    @abstractmethod
    def report(self, ctx: WfExecStatusFacadeCtx) -> int:
        """An engine reports a status of one execution (ctx.req). The codes and the ingest rule are those of
        WfExecStatusService.record; the execution and its ingest row after the call are in ctx.resp."""
```

Create `app/core/facades/wf_exec_status_facade_task.py`:

```python
"""The task interface dedicated to the workflow execution status facade. Every task of this facade implements it."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusFacadeTask(metaclass=SingletonMeta):
    """A singleton (every task is), so a task keeps no state of its own: what it needs is in the ctx."""

    @abstractmethod
    def execute(self, ctx: WfExecStatusFacadeCtx) -> int:
        """Do one step. Return SUCCESS to let the next task run, any other code to stop the facade."""
```

Create `app/core/facades/impl/tasks/wf_exec_status_call_service_task.py`:

```python
"""Hands the report to the service, which validates it and changes both logs in one transaction, and puts the
service's response on the facade ctx."""

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.facades.wf_exec_status_facade_task import WfExecStatusFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class WfExecStatusCallServiceTask(WfExecStatusFacadeTask):
    def execute(self, ctx: WfExecStatusFacadeCtx) -> int:
        ctx.status_ctx = WfExecStatusCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_wf_exec_status_service().record(ctx.status_ctx)
        ctx.resp = ctx.status_ctx.resp
        return code
```

Create `app/core/facades/impl/wf_exec_status_facade_impl.py`:

```python
"""The facade only iterates over its tasks; the tasks do the work. It is a singleton, so the task list is built once."""

from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.tasks.wf_exec_status_call_service_task import WfExecStatusCallServiceTask
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade


class WfExecStatusFacadeImpl(WfExecStatusFacade):
    def __init__(self):
        self._tasks = [WfExecStatusCallServiceTask()]

    def report(self, ctx: WfExecStatusFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
```

Replace the whole of `app/core/facades/objects_factory.py` with:

```python
"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade


class FacadesObjectsFactory:
    @staticmethod
    def get_data_ingest_facade() -> DataIngestFacade:
        from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl

        return DataIngestFacadeImpl()

    @staticmethod
    def get_wf_exec_status_facade() -> WfExecStatusFacade:
        from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl

        return WfExecStatusFacadeImpl()
```

- [ ] **Step 6: Run them and see them pass**

Run: `uv run pytest tests/test_wf_exec_status_service.py tests/test_singletons.py -v`
Expected: all PASS (24 in `test_wf_exec_status_service.py`, 3 in `test_singletons.py`).

- [ ] **Step 7: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; `337 passed, 8 skipped` (313 before plus 24; Postgres tests skipped without `CCA_TEST_POSTGRES_URL`), including `tests/test_ctx_only_signatures.py`. `openapi.json` is unchanged (no route yet).

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 43` with summary `status service and facade: execution and MIO ingest in one transaction` and files `app/core/common/dtos/wf_exec_status_dtos.py app/core/common/dtos/wf_exec_status_facade_dtos.py app/core/services/wf_exec_status_service.py app/core/services/impl/wf_exec_status_service_impl.py app/core/services/objects_factory.py app/core/facades/wf_exec_status_facade.py app/core/facades/wf_exec_status_facade_task.py app/core/facades/impl/wf_exec_status_facade_impl.py app/core/facades/impl/tasks/wf_exec_status_call_service_task.py app/core/facades/objects_factory.py tests/test_wf_exec_status_service.py tests/test_singletons.py`.

---

### Task 2: the endpoint, its models, the wiring and `openapi.json`

**Files:**
- Create: `app/api/models/wf_exec_callback_models.py`, `app/api/routers/wf_exec_callback_api.py`
- Modify: `app/api/objects_factory.py`, `openapi.json` (regenerated)
- Test: `tests/test_wf_exec_callback_api.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Consumes: `FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx)`, `WfExecStatusFacadeCtx`, `WfExecStatusReq` and the codes from Task 1; `ApiObjectsFactory.get_callback_secret_auth()` (D59); the `client` and `data_dir` fixtures of `tests/conftest.py`.
- Produces: `POST /callbacks/workflow-executions/{execution_id}/status` returning `WfExecStatusOut`; `ApiObjectsFactory.get_wf_exec_callback_api() -> WfExecCallbackApi`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wf_exec_callback_api.py`:

```python
"""The status callback through HTTP (D60): the secret (D59), the error mapping, and duplicate and out-of-order calls."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SECRET = "s3cret-value-for-tests"
HEADERS = {"X-Callback-Secret": SECRET}
SEEDED_MIO = "Customer complaints 3 months 2026"


def _url(execution_id):
    return f"/callbacks/workflow-executions/{execution_id}/status"


def _execution_status(execution_id):
    ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0].status


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


@pytest.fixture
def ingest_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def new_execution(data_dir):
    """Creates an execution of a fresh workflow; pass an ingest id to attach it to that ingest."""
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_callback", engine_type="apache_airflow", engine_workflow_id="d"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS

    def create(ingest=None):
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.resp.records[0].id, mios_ingest_log_id=ingest))
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    return create


def test_started_then_completed_moves_the_execution_and_its_ingest(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    started = client.post(_url(execution_id), json={"status": "started", "engine_run_id": "run-1"}, headers=HEADERS)
    assert started.status_code == 200
    body = started.json()
    assert (body["execution"]["id"], body["execution"]["status"]) == (execution_id, "started")
    assert body["execution"]["engine_run_id"] == "run-1"
    assert body["execution"]["mios_ingest_log_id"] == ingest_id
    assert (body["ingest"]["id"], body["ingest"]["status"]) == (ingest_id, "started")

    done = client.post(
        _url(execution_id),
        json={"status": "completed", "message": "ok", "rows_loaded": 1500, "batch_count": 3, "increment_marker": "m"},
        headers=HEADERS,
    )
    assert done.status_code == 200
    ingest = done.json()["ingest"]
    assert (ingest["status"], ingest["message"], ingest["rows_loaded"]) == ("completed", "ok", 1500)
    assert (ingest["batch_count"], ingest["increment_marker"]) == (3, "m")
    assert ingest["finished_at"] is not None


def test_an_execution_without_an_ingest_returns_a_null_ingest(client, secret, new_execution):
    response = client.post(_url(new_execution()), json={"status": "started"}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["ingest"] is None
    assert response.json()["execution"]["status"] == "started"


def test_a_duplicate_call_is_200_with_the_same_body(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    first = client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS)
    again = client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS)
    assert (first.status_code, again.status_code) == (200, 200)
    assert again.json() == first.json()


def test_an_out_of_order_call_is_409_and_changes_nothing(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    response = client.post(_url(execution_id), json={"status": "completed"}, headers=HEADERS)
    assert response.status_code == 409
    assert response.json() == {"detail": "status change not allowed in the current state"}
    assert _execution_status(execution_id) == "requested"


def test_a_late_call_after_a_final_status_is_409(client, secret, new_execution):
    execution_id = new_execution()
    assert client.post(_url(execution_id), json={"status": "failed"}, headers=HEADERS).status_code == 200
    assert client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS).status_code == 409
    assert client.post(_url(execution_id), json={"status": "failed"}, headers=HEADERS).status_code == 200


def test_an_unknown_execution_is_404(client, secret):
    response = client.post(_url("no-such-execution"), json={"status": "started"}, headers=HEADERS)
    assert response.status_code == 404
    assert response.json() == {"detail": "workflow execution not found"}


@pytest.mark.parametrize(
    "body",
    [
        {"status": "requested"},
        {"status": "bogus"},
        {},
        {"status": "started", "rows_loaded": -1},
        {"status": "started", "rows_loaded": "5"},
        {"status": "started", "batch_count": True},
        {"status": "started", "engine_run_id": "r" * 129},
        {"status": "started", "increment_marker": "m" * 256},
        {"status": "started", "unknown_field": 1},
    ],
)
def test_an_invalid_body_is_422_and_changes_nothing(client, secret, new_execution, body):
    execution_id = new_execution()
    assert client.post(_url(execution_id), json=body, headers=HEADERS).status_code == 422
    assert _execution_status(execution_id) == "requested"


def test_a_volume_beyond_the_column_maximum_is_422_from_the_service(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    response = client.post(_url(execution_id), json={"status": "started", "batch_count": 2**31}, headers=HEADERS)
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid request"}
    assert _execution_status(execution_id) == "requested"


@pytest.mark.parametrize("headers", [{}, {"X-Callback-Secret": "wrong"}])
def test_without_the_right_secret_it_is_401_and_nothing_changes(client, secret, new_execution, headers):
    execution_id = new_execution()
    response = client.post(_url(execution_id), json={"status": "started"}, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or wrong callback secret"}
    assert _execution_status(execution_id) == "requested"


def test_without_a_configured_secret_it_is_401(client, monkeypatch, new_execution):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    response = client.post(_url(new_execution()), json={"status": "started"}, headers={"X-Callback-Secret": ""})
    assert response.status_code == 401


def test_a_malformed_json_body_is_422_before_the_secret_check(client, secret, new_execution):
    """Accepted (D59, D60): FastAPI parses the body before the router's dependency runs."""
    execution_id = new_execution()
    response = client.post(_url(execution_id), content=b"{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert _execution_status(execution_id) == "requested"


def test_openapi_lists_the_callback(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths["/callbacks/workflow-executions/{execution_id}/status"]) == {"post"}
```

In `tests/test_singletons.py`:

- after the line `from app.api.routers.data_ingest_api import DataIngestApi`, add:

```python
from app.api.routers.wf_exec_callback_api import WfExecCallbackApi
```

- in `test_factories_return_the_same_object_typed_as_the_interface`, after the line `    assert isinstance(ApiObjectsFactory.get_callback_secret_auth(), CallbackSecretAuth)`, add:

```python
    assert ApiObjectsFactory.get_wf_exec_callback_api() is ApiObjectsFactory.get_wf_exec_callback_api()
    assert isinstance(ApiObjectsFactory.get_wf_exec_callback_api(), WfExecCallbackApi)
```

- in `test_the_classes_themselves_are_singletons`, after the line `    assert DataIngestApi() is DataIngestApi()`, add:

```python
    assert WfExecCallbackApi() is WfExecCallbackApi()
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_wf_exec_callback_api.py tests/test_singletons.py -v`
Expected: `test_singletons.py` fails at collection with `ModuleNotFoundError: No module named 'app.api.routers.wf_exec_callback_api'`; in `test_wf_exec_callback_api.py` every test that calls the endpoint fails (the route does not exist, so FastAPI answers 404 `Not Found`; the 404 test fails on the detail text) and `test_openapi_lists_the_callback` fails with a `KeyError`.

- [ ] **Step 3: Add the models**

Create `app/api/models/wf_exec_callback_models.py`:

```python
"""Request and response models of the status callback an engine calls (D60; these produce the OpenAPI schema).

The endpoint takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReportedStatus = Literal["started", "completed", "failed"]


class WfExecStatusReport(BaseModel):
    """The body: what the engine reports. engine_run_id and message go to the execution; the volume fields go to its
    MIO ingest row and are ignored when it has none. Unknown fields are refused."""

    model_config = ConfigDict(extra="forbid")

    status: ReportedStatus
    engine_run_id: str | None = Field(default=None, max_length=128)
    message: str | None = None
    rows_loaded: int | None = Field(default=None, ge=0, strict=True)
    batch_count: int | None = Field(default=None, ge=0, strict=True)
    increment_marker: str | None = Field(default=None, max_length=255)


class WfExecStatusReportReq(BaseModel):
    """The execution id in the path plus the report in the body."""

    execution_id: str
    body: WfExecStatusReport


class AppWfExecLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    engine_run_id: str | None = None
    status: str
    message: str | None = None
    mios_ingest_log_id: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class MioIngestLogOut(BaseModel):
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


class WfExecStatusOut(BaseModel):
    """The execution and its MIO ingest row (null when it has none) after the call."""

    execution: AppWfExecLogOut
    ingest: MioIngestLogOut | None = None
```

`strict=True` on the counts makes a JSON string (`"5"`) or a boolean (`true`) a 422 instead of being converted, matching the DAO, which treats a bool as not a whole number. The column maximums (`rows_loaded` 9223372036854775807, `batch_count` 2147483647) are checked by `MioIngestLogDao` and come back as 422 `invalid request`.

- [ ] **Step 4: Add the router class**

Create `app/api/routers/wf_exec_callback_api.py`:

```python
"""The status callback a workflow engine (Airflow) calls, as a class (D29, D60). It is a singleton.

The callback secret check (D59) is not attached here: ApiObjectsFactory attaches it to the whole router when it
includes it. The method is plain `def` so FastAPI runs the blocking database calls in a worker thread.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.wf_exec_callback_models import (
    AppWfExecLogOut,
    MioIngestLogOut,
    WfExecStatusOut,
    WfExecStatusReportReq,
)
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusReq
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class WfExecCallbackApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/callbacks", tags=["callbacks"])
        self.router.add_api_route(
            "/workflow-executions/{execution_id}/status",
            self.report_status,
            methods=["POST"],
            response_model=WfExecStatusOut,
        )

    def report_status(self, req: Annotated[WfExecStatusReportReq, Depends()]) -> WfExecStatusOut:
        ctx = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id=req.execution_id, **req.body.model_dump()))
        FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx)
        self._check(ctx)
        ingest = ctx.resp.ingest
        return WfExecStatusOut(
            execution=AppWfExecLogOut.model_validate(ctx.resp.execution),
            ingest=MioIngestLogOut.model_validate(ingest) if ingest is not None else None,
        )

    @staticmethod
    def _check(ctx: WfExecStatusFacadeCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow execution not found")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "status change not allowed in the current state")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
```

`Annotated[WfExecStatusReportReq, Depends()]` is the pattern of `DataIngestApi.update_log`: FastAPI fills `execution_id` from the path and `body` from the JSON body (the only body parameter, so the JSON is the report itself, not wrapped in `{"body": ...}`).

- [ ] **Step 5: Wire it in the api objects factory**

Replace the whole of `app/api/objects_factory.py` with:

```python
"""Builds the one FastAPI application for the whole project (one OpenAPI spec) and hands out the other singletons of
the api package (the callback secret check, D59, and the status callback API, D60). The app is a singleton."""

import threading

from fastapi import Depends, FastAPI

from app.api.routers.data_ingest_api import DataIngestApi
from app.api.routers.wf_exec_callback_api import WfExecCallbackApi
from app.api.security.callback_secret_auth import CallbackSecretAuth


class ApiObjectsFactory:
    _app: FastAPI | None = None
    _lock = threading.Lock()

    @staticmethod
    def get_app() -> FastAPI:
        if ApiObjectsFactory._app is None:
            with ApiObjectsFactory._lock:
                if ApiObjectsFactory._app is None:
                    ApiObjectsFactory._app = ApiObjectsFactory._build_app()
        return ApiObjectsFactory._app

    @staticmethod
    def get_callback_secret_auth() -> CallbackSecretAuth:
        return CallbackSecretAuth()

    @staticmethod
    def get_wf_exec_callback_api() -> WfExecCallbackApi:
        return WfExecCallbackApi()

    @staticmethod
    def _build_app() -> FastAPI:
        app = FastAPI(
            title="Consumer Complaints Hands-On API",
            version="0.1.0",
            description="Middleware API for the Consumer Complaints platform.",
        )
        app.include_router(DataIngestApi().router)
        # Every router an engine calls is protected as a whole by the callback secret (D59).
        app.include_router(
            ApiObjectsFactory.get_wf_exec_callback_api().router,
            dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())],
        )

        @app.get("/health", tags=["health"])
        def health() -> dict[str, str]:
            return {"status": "ok"}

        return app
```

- [ ] **Step 6: Run them and see them pass**

Run: `uv run pytest tests/test_wf_exec_callback_api.py tests/test_singletons.py tests/test_callback_secret_api.py -v`
Expected: all PASS (21 in `test_wf_exec_callback_api.py`, 3 in `test_singletons.py`, 13 in `test_callback_secret_api.py`: `/health` and `/data-ingest-logs` stay open).

- [ ] **Step 7: Regenerate `openapi.json`**

Run: `uv run pytest tests/test_openapi_spec.py -v`
Expected: FAIL, `openapi.json is out of date`.

Run: `uv run python scripts/export_openapi.py`
Expected: `wrote .../openapi.json`. Check with `git diff --stat openapi.json`: about 350 lines added and none removed (the new path, the `callbacks` tag and the schemas `WfExecStatusReport`, `WfExecStatusOut`, `AppWfExecLogOut`, `MioIngestLogOut`).

- [ ] **Step 8: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; `358 passed, 8 skipped`, including `tests/test_openapi_spec.py`, `tests/test_ctx_only_signatures.py` (the endpoint takes one `req`, `_check` one `ctx`, the factory method nothing) and `tests/test_import_contracts.py` (the api package imports only common and facade interfaces and factories).

- [ ] **Step 9: Commit**

Run `/ccaa-commit-push 43` with summary `status callback endpoint behind the callback secret` and files `app/api/models/wf_exec_callback_models.py app/api/routers/wf_exec_callback_api.py app/api/objects_factory.py openapi.json tests/test_wf_exec_callback_api.py tests/test_singletons.py`.

---

### Task 3: the flow on Postgres, and the design notes

**Files:**
- Modify: `tests/test_postgres.py`, `DESIGN.md`, `ARCHITECTURE.md`

**Interfaces:**
- Consumes: `ServicesObjectsFactory.get_wf_exec_status_service().record(ctx)` and the DTOs from Task 1; the `postgres` fixture and the imports already in `tests/test_postgres.py`.

- [ ] **Step 1: Write the Postgres test**

In `tests/test_postgres.py`, add directly below the line `from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq`:

```python
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq
```

Then append at the end of the file:

```python


def test_wf_exec_status_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    mio = MioCtx(req=MioReq(name="t_status_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    ingest_id = ingest.resp.records[0].id
    made = AppWfCtx(req=AppWfReq(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ids = []
    for _ in range(2):
        req = AppWfExecLogReq(workflow_id=made.resp.records[0].id, mios_ingest_log_id=ingest_id)
        execution = AppWfExecLogCtx(req=req)
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS
        ids.append(execution.resp.records[0].id)

    def report(req):
        ctx = WfExecStatusCtx(req=req)
        ServicesObjectsFactory.get_wf_exec_status_service().record(ctx)
        return ctx.resp

    for execution_id in ids:
        assert report(WfExecStatusReq(execution_id=execution_id, status="started")).code == SUCCESS
    first = report(WfExecStatusReq(execution_id=ids[0], status="completed", rows_loaded=5_000_000_000))
    assert (first.code, first.ingest.status, first.ingest.rows_loaded) == (SUCCESS, "started", 5_000_000_000)
    assert report(WfExecStatusReq(execution_id=ids[0], status="failed")).code == CONFLICT
    last = report(WfExecStatusReq(execution_id=ids[1], status="completed", message="done"))
    assert (last.code, last.ingest.status, last.ingest.message) == (SUCCESS, "completed", "done")
    again = report(WfExecStatusReq(execution_id=ids[1], status="completed"))
    assert (again.code, again.ingest) == (SUCCESS, last.ingest)
    assert report(WfExecStatusReq(execution_id=ids[1], status="completed", batch_count=-1)).code == INVALID_INPUT
    assert report(WfExecStatusReq(execution_id="no-such-execution", status="started")).code == NOT_FOUND
```

- [ ] **Step 2: Run it without Postgres**

Run: `uv run pytest tests/test_postgres.py -v`
Expected: every test SKIPPED (`CCA_TEST_POSTGRES_URL is not set`), now 9.

- [ ] **Step 3: Run the whole suite on a real Postgres**

Run, from the app root:

```bash
docker run -d --name cca-pg-0008 -e POSTGRES_PASSWORD=postgres -p 55438:5432 postgres:16
sleep 7
CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55438/postgres uv run pytest -q
docker rm -f cca-pg-0008
```

Expected: `367 passed` (nothing skipped). If `pytest` fails with a connection error, Postgres was not ready: wait a few seconds and run the `pytest` line again. Always run the `docker rm -f cca-pg-0008` line, also after a failure. If `docker` is not available, say so in the report and rely on CI's Postgres service.

- [ ] **Step 4: Mark the callback as built in the design**

In `DESIGN.md`, section `### 4.2 Endpoints`:

- in the bullet that starts `- The callback endpoints need a **shared secret**`, replace `no endpoint uses it yet, #43 is the first.` with:

```
the status callback (#43, `WfExecCallbackApi`) is the first router that uses it.
```

- in the bullet that starts `- Allowed status changes:`, replace `Designed in story #43 (spec` with:

```
Built in story #43 (`WfExecCallbackApi`, `WfExecStatusFacade`, `WfExecStatusService`; spec
```

In `DESIGN.md`, section `#### The catalog (D49)`, in the bullet that starts `- **Built (story #87, M02-0037):**`, replace `No endpoint reads them yet, and nothing derives an ingest's status from its executions.` with:

```
The status callback (#43, D60) writes both; no endpoint reads them yet.
```

In `ARCHITECTURE.md`, section `## 8. Local environment`, replace the line `` `/health` and the other endpoints need no secret.`` with:

```
The first callback endpoint is `POST /callbacks/workflow-executions/{execution_id}/status` (D60); `/health` and the
other endpoints need no secret.
```

- [ ] **Step 5: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; `358 passed, 9 skipped`, including `tests/test_portability.py` (it scans the `.md` files).

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 43` with summary `status callback on Postgres and design notes` and files `tests/test_postgres.py DESIGN.md ARCHITECTURE.md`.

---

## Self-Review (done)

1. **Spec coverage:** naming (Global Constraints, all tasks); the URL, method, router prefix and tag, the body fields with their limits, `requested` refused, unknown fields refused, strict counts (Task 2 models and tests); the response with a null ingest (Tasks 1 and 2); every error row: 401 missing, wrong and unconfigured secret, 404, 409 out of order and after a final status, 422 from FastAPI and `invalid request` from the service, 500 when the ingest write fails or conflicts (Tasks 1 and 2); malformed JSON 422 before the check (Task 2); the ingest rule step by step: validation before the transaction, the execution update, no ingest, the read, the target for started, failed and completed with the every-execution check, skipped moves on a final ingest, the message only with a move, volume always, INVALID_INPUT passing through and everything else becoming FAILURE (Task 1); every row of the duplicates table (Tasks 1 and 2); one transaction with rollback of the execution (Task 1); singletons and factory registration for every new class (Tasks 1 and 2, D26 acceptance); `openapi.json` (Task 2); Postgres (Task 3); DESIGN and ARCHITECTURE notes (Task 3). The decision itself (D60), the section 3, 4.2 and 8 edits of `DESIGN.md` and the next decision number in `Milestone_02.md` were written with the spec and are committed by the first `/ccaa-commit-push 43` (it stages the milestone file and the story's spec and plan). Not tested, by design: the Postgres race of the spec's Concurrency section (accepted gap).
2. **Placeholders:** none; every code step shows the full file or names the exact line an addition goes after or replaces.
3. **Types and names:** `WfExecStatusReq/Resp/Ctx`, `WfExecStatusFacadeCtx.status_ctx`, `WfExecStatusService.record`, `WfExecStatusFacade.report`, `WfExecStatusCallServiceTask`, `WfExecCallbackApi.report_status`, `WfExecStatusReport`, `WfExecStatusReportReq`, `WfExecStatusOut`, `AppWfExecLogOut`, `MioIngestLogOut`, the three factory methods, `REPORTED_STATUSES` and the details `workflow execution not found`, `status change not allowed in the current state`, `invalid request`, `request failed` are spelled the same in every task and in the spec. Every helper in `app` takes one ctx or one req, so `tests/test_ctx_only_signatures.py` stays green.
4. **Pre-check:** the code of Tasks 1 to 3 was run in a scratch copy of the app root under `runtime_data/tmp/` (deleted afterwards): `lint-imports` 7 kept, 0 broken; SQLite suite `358 passed, 9 skipped` (313 before, plus 24 service and facade tests and 21 HTTP tests; one more Postgres test skipped); the whole suite on a `postgres:16` container `367 passed`. Every test passed on its first run against the code, so the failures expected in each Step 2 are the missing modules and route, not logic errors.
5. **Accepted gaps (from the spec):** on Postgres, the last two executions of an ingest completing in the same instant can leave the ingest `started` until the next call for one of them; a rerun after a failure needs a new ingest row; volume values overwrite and are not added up across parts; a malformed JSON body is 422 before the secret check.
