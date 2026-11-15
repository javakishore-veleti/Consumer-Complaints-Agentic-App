# M02-0034 (#84) List workflows endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `GET /workflows` returns every registered `app_workflows` row (safe fields only) so the admin portal can list workflows in one call.

**Architecture:** `WfListApi` (singleton router, D29) builds a `WfListFacadeCtx` and calls `WfListFacade`; the facade's one task (under `impl/wf_list/tasks/`, D64) calls `WfListService.list`, which maps `AppWfDao.list` records to entries without `config`. `ApiObjectsFactory` includes the router with **no** callback-secret dependency (D59, D66). No migration.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, pytest, `uv`, import-linter; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0034-list-workflows-design.md`. Decisions: D5, D6, D26, D29, D32, D33, D37, D45, D54, D55, D59, D64, D66 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there. All paths below are relative to it, except the plan and spec paths.
- Endpoint exactly: `GET /workflows`, router prefix `/workflows`, tag `workflows`, response 200 with a JSON list of `WfListOut`.
- Names exactly: `WfListEntry`, `WfListReq`, `WfListResp`, `WfListCtx` (`app/core/common/dtos/wf_list_dtos.py`); `WfListFacadeCtx` (`wf_list_facade_dtos.py`); `WfListService`, `WfListServiceImpl`; `WfListFacade`, `WfListFacadeTask`, `WfListCallServiceTask`, `WfListFacadeImpl`; `WfListApi`; models `WfListReq`, `WfListOut`; factory methods `get_wf_list_service()`, `get_wf_list_facade()`, `get_wf_list_api()`.
- Facade files live under `app/core/facades/impl/wf_list/` and `impl/wf_list/tasks/` (D64). Do not add this task to the flat `impl/tasks/` folder.
- Response fields exactly: `id`, `workflow_name`, `engine_type`, `engine_workflow_id`, `enabled`. Never `config`. Empty registry → `[]`.
- No callback secret on this router. Non-SUCCESS → 500 `request failed`.
- Every class in `api`, `facades`, `services` is a singleton (`SingletonMeta`, D26) handed out by its package's `objects_factory`; no `init()` (D45, D54).
- Every function takes nothing or exactly one object (D5, D37; `tests/test_ctx_only_signatures.py`).
- The api package imports only `app.core.common` and facade interfaces/factories; `uv run lint-imports`: `Contracts: 7 kept, 0 broken.`
- `openapi.json` is regenerated with `uv run python scripts/export_openapi.py` (D32).
- Test workflow names use the prefix `t_`. Scratch files go in `runtime_data/tmp/` (D36). Never commit `.env`.
- Commit with `/ccaa-commit-push 84` only (never raw `git commit`).

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/dtos/wf_list_dtos.py` (create) | service Req/Resp/Ctx and `WfListEntry` |
| `app/core/common/dtos/wf_list_facade_dtos.py` (create) | facade ctx |
| `app/core/services/wf_list_service.py` (create) | service interface |
| `app/core/services/impl/wf_list_service_impl.py` (create) | list via `AppWfDao`, strip `config` |
| `app/core/services/objects_factory.py` (modify) | `get_wf_list_service()` |
| `app/core/facades/wf_list_facade.py`, `wf_list_facade_task.py` (create) | facade and task interfaces |
| `app/core/facades/impl/wf_list/wf_list_facade_impl.py` (create) | facade impl (D64) |
| `app/core/facades/impl/wf_list/tasks/wf_list_call_service_task.py` (create) | one task (D64) |
| `app/core/facades/impl/wf_list/__init__.py`, `tasks/__init__.py` (create) | package markers (empty) |
| `app/core/facades/objects_factory.py` (modify) | `get_wf_list_facade()` |
| `app/api/models/wf_list_models.py` (create) | empty query req + response model |
| `app/api/routers/wf_list_api.py` (create) | router class and HTTP mapping |
| `app/api/objects_factory.py` (modify) | `get_wf_list_api()`; include without secret |
| `openapi.json` (regenerate) | new path and schemas |
| `tests/test_wf_list_service.py`, `tests/test_wf_list_api.py` (create) | service, facade, HTTP |
| `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | singletons; Postgres flow |
| `DESIGN.md`, `ARCHITECTURE.md` (modify) | mark list-workflows built (D66) |

---

### Task 1: service, facade (D64 layout) and factories

**Files:**
- Create: `app/core/common/dtos/wf_list_dtos.py`, `app/core/common/dtos/wf_list_facade_dtos.py`, `app/core/services/wf_list_service.py`, `app/core/services/impl/wf_list_service_impl.py`, `app/core/facades/wf_list_facade.py`, `app/core/facades/wf_list_facade_task.py`, `app/core/facades/impl/wf_list/__init__.py`, `app/core/facades/impl/wf_list/tasks/__init__.py`, `app/core/facades/impl/wf_list/wf_list_facade_impl.py`, `app/core/facades/impl/wf_list/tasks/wf_list_call_service_task.py`
- Modify: `app/core/services/objects_factory.py`, `app/core/facades/objects_factory.py`
- Test: `tests/test_wf_list_service.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Consumes: `AppWfDao.list` through `DaoObjectsFactory.get_app_wf_dao()`.
- Produces: `WfListEntry(id, workflow_name, engine_type, engine_workflow_id, enabled)`, `WfListReq()`, `WfListResp(entries, code)`, `WfListCtx`; `WfListFacadeCtx`; `FacadesObjectsFactory.get_wf_list_facade().list(ctx) -> int`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wf_list_service.py`:

```python
"""Every registered workflow without config (D66)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory


def _list() -> WfListCtx:
    ctx = WfListCtx(req=WfListReq())
    ServicesObjectsFactory.get_wf_list_service().list(ctx)
    return ctx


def test_empty_registry_is_empty_list(data_dir):
    ctx = _list()
    assert ctx.resp.code == SUCCESS
    assert ctx.resp.entries == []


def test_lists_every_workflow_ordered_by_name_without_config(data_dir):
    for name, enabled in (("t_b", True), ("t_a", False), ("t_c", True)):
        ctx = AppWfCtx(
            req=AppWfReq(
                workflow_name=name,
                engine_type="apache_airflow",
                engine_workflow_id=f"dag_{name}",
                enabled=enabled,
                config={"secretish": "nope"},
            )
        )
        assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS

    ctx = _list()
    assert ctx.resp.code == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == ["t_a", "t_b", "t_c"]
    assert [e.enabled for e in ctx.resp.entries] == [False, True, True]
    assert all(e.engine_type == "apache_airflow" for e in ctx.resp.entries)
    assert [e.engine_workflow_id for e in ctx.resp.entries] == ["dag_t_a", "dag_t_b", "dag_t_c"]
    assert all(not hasattr(e, "config") for e in ctx.resp.entries)
    assert all(e.id for e in ctx.resp.entries)


def test_facade_hands_the_list_on(data_dir):
    made = AppWfCtx(
        req=AppWfReq(workflow_name="t_facade", engine_type="apache_airflow", engine_workflow_id="d")
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ctx = WfListFacadeCtx(req=WfListReq())
    assert FacadesObjectsFactory.get_wf_list_facade().list(ctx) == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == ["t_facade"]
```

In `tests/test_singletons.py`, add imports and assert:

```python
from app.core.facades.impl.wf_list.tasks.wf_list_call_service_task import WfListCallServiceTask
from app.core.facades.impl.wf_list.wf_list_facade_impl import WfListFacadeImpl
from app.core.facades.wf_list_facade import WfListFacade
from app.core.services.impl.wf_list_service_impl import WfListServiceImpl
from app.core.services.wf_list_service import WfListService
```

Add `(ServicesObjectsFactory.get_wf_list_service, WfListService)` and `(FacadesObjectsFactory.get_wf_list_facade, WfListFacade)` to the factory loop; assert `WfListServiceImpl()`, `WfListFacadeImpl()`, and `WfListCallServiceTask()` are singletons (same pattern as `MioStatus*`).

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_wf_list_service.py -v
```

Expected: FAIL with import / attribute errors for `wf_list_*` modules and factory methods.

- [ ] **Step 3: Write DTOs**

`app/core/common/dtos/wf_list_dtos.py`:

```python
"""Ctx, Req and Resp of the workflow list service (DESIGN.md D66)."""

from dataclasses import dataclass, field

from app.core.common.return_codes import SUCCESS


@dataclass
class WfListEntry:
    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    enabled: bool


@dataclass
class WfListReq:
    """No filters for MVP (D54, D66)."""


@dataclass
class WfListResp:
    entries: list[WfListEntry] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class WfListCtx:
    req: WfListReq = field(default_factory=WfListReq)
    resp: WfListResp = field(default_factory=WfListResp)
```

`app/core/common/dtos/wf_list_facade_dtos.py`:

```python
"""Ctx of the workflow list facade. Reuses the service's Req and Resp; carries list_ctx."""

from dataclasses import dataclass, field

from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq, WfListResp


@dataclass
class WfListFacadeCtx:
    req: WfListReq = field(default_factory=WfListReq)
    resp: WfListResp = field(default_factory=WfListResp)
    list_ctx: WfListCtx = field(default_factory=WfListCtx)
```

- [ ] **Step 4: Write service interface and impl**

`app/core/services/wf_list_service.py`:

```python
"""Interface: list every registered workflow without config (D66)."""

from abc import abstractmethod

from app.core.common.dtos.wf_list_dtos import WfListCtx
from app.core.common.singleton import SingletonMeta


class WfListService(metaclass=SingletonMeta):
    @abstractmethod
    def list(self, ctx: WfListCtx) -> int:
        """Return SUCCESS with resp.entries, or a DAO failure code."""
```

`app/core/services/impl/wf_list_service_impl.py`:

```python
"""Maps AppWfDao.list rows to safe portal entries (D66)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListEntry
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.wf_list_service import WfListService


class WfListServiceImpl(WfListService):
    def list(self, ctx: WfListCtx) -> int:
        dao_ctx = AppWfCtx()
        code = DaoObjectsFactory.get_app_wf_dao().list(dao_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.entries = [
            WfListEntry(
                id=r.id,
                workflow_name=r.workflow_name,
                engine_type=r.engine_type,
                engine_workflow_id=r.engine_workflow_id,
                enabled=r.enabled,
            )
            for r in dao_ctx.resp.records
        ]
        ctx.resp.code = SUCCESS
        return SUCCESS
```

- [ ] **Step 5: Write facade interfaces, D64 impl and task**

`app/core/facades/wf_list_facade.py` and `wf_list_facade_task.py` mirror `mio_status_facade*` (method `list` / `execute`).

`app/core/facades/impl/wf_list/tasks/wf_list_call_service_task.py`:

```python
"""Hands the list to the service and puts the service's response on the facade ctx."""

from app.core.common.dtos.wf_list_dtos import WfListCtx
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.facades.wf_list_facade_task import WfListFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class WfListCallServiceTask(WfListFacadeTask):
    def execute(self, ctx: WfListFacadeCtx) -> int:
        ctx.list_ctx = WfListCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_wf_list_service().list(ctx.list_ctx)
        ctx.resp = ctx.list_ctx.resp
        return code
```

`app/core/facades/impl/wf_list/wf_list_facade_impl.py`:

```python
"""The facade only iterates over its tasks. Singleton; task list built once (D64 package)."""

from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.impl.wf_list.tasks.wf_list_call_service_task import WfListCallServiceTask
from app.core.facades.wf_list_facade import WfListFacade


class WfListFacadeImpl(WfListFacade):
    def __init__(self):
        self._tasks = [WfListCallServiceTask()]

    def list(self, ctx: WfListFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
```

Empty `__init__.py` files under `impl/wf_list/` and `impl/wf_list/tasks/`.

- [ ] **Step 6: Register factories**

In `ServicesObjectsFactory` add `get_wf_list_service()` returning `WfListServiceImpl()`.

In `FacadesObjectsFactory` add:

```python
@staticmethod
def get_wf_list_facade() -> WfListFacade:
    from app.core.facades.impl.wf_list.wf_list_facade_impl import WfListFacadeImpl

    return WfListFacadeImpl()
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
uv run pytest tests/test_wf_list_service.py tests/test_singletons.py -v
uv run lint-imports
```

Expected: PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 84` with summary `wf list service and facade under impl/wf_list (D64, D66)`.

---

### Task 2: API router, OpenAPI and HTTP tests

**Files:**
- Create: `app/api/models/wf_list_models.py`, `app/api/routers/wf_list_api.py`, `tests/test_wf_list_api.py`
- Modify: `app/api/objects_factory.py`, `openapi.json` (regenerate)
- Test: `tests/test_wf_list_api.py`, `tests/test_singletons.py`, `tests/test_openapi_spec.py`, `tests/test_callback_secret_api.py` (unchanged, must stay green)

**Interfaces:**
- Consumes: `FacadesObjectsFactory.get_wf_list_facade().list`
- Produces: `GET /workflows` → `list[WfListOut]`; `ApiObjectsFactory.get_wf_list_api()`

- [ ] **Step 1: Write the failing HTTP tests**

Create `tests/test_wf_list_api.py`:

```python
"""GET /workflows through HTTP (D66): portal list of registered workflows."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

URL = "/workflows"


def test_empty_registry_is_empty_list(client):
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == []


def test_lists_workflows_without_config(client):
    for name in ("t_z", "t_y"):
        ctx = AppWfCtx(
            req=AppWfReq(
                workflow_name=name,
                engine_type="apache_airflow",
                engine_workflow_id="dag",
                config={"x": 1},
            )
        )
        assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS

    body = client.get(URL).json()
    assert [row["workflow_name"] for row in body] == ["t_y", "t_z"]
    for row in body:
        assert set(row) == {"id", "workflow_name", "engine_type", "engine_workflow_id", "enabled"}
        assert "config" not in row


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.get(URL).status_code == 200


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/workflows" in spec["paths"]
    assert "get" in spec["paths"]["/workflows"]
```

- [ ] **Step 2: Run to verify fail**

```bash
uv run pytest tests/test_wf_list_api.py -v
```

Expected: FAIL (404 / missing path).

- [ ] **Step 3: Models and API class**

`app/api/models/wf_list_models.py`:

```python
"""Request and response models of GET /workflows (D66)."""

from pydantic import BaseModel, ConfigDict


class WfListReq(BaseModel):
    """No query fields for MVP."""


class WfListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    enabled: bool
```

`app/api/routers/wf_list_api.py` (mirror `MioStatusApi`):

```python
"""The portal's list of every registered workflow (D29, D66). Singleton. No callback secret (D59)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.models.wf_list_models import WfListOut, WfListReq
from app.core.common.dtos.wf_list_dtos import WfListReq as WfListServiceReq
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class WfListApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/workflows", tags=["workflows"])
        self.router.add_api_route(
            "",
            self.list,
            methods=["GET"],
            response_model=list[WfListOut],
        )

    def list(self, req: Annotated[WfListReq, Query()]) -> list[WfListOut]:
        ctx = WfListFacadeCtx(req=WfListServiceReq())
        FacadesObjectsFactory.get_wf_list_facade().list(ctx)
        self._check(ctx)
        return [WfListOut.model_validate(e) for e in ctx.resp.entries]

    @staticmethod
    def _check(ctx: WfListFacadeCtx) -> None:
        if ctx.resp.code == SUCCESS:
            return
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
```

- [ ] **Step 4: Wire ApiObjectsFactory**

Add `get_wf_list_api()` and, next to the mio-status include (portal, no secret):

```python
app.include_router(ApiObjectsFactory.get_wf_list_api().router)
```

Update the module docstring to mention the workflows list (D66). Extend `tests/test_singletons.py` for `WfListApi` / `get_wf_list_api`.

- [ ] **Step 5: Regenerate OpenAPI and run tests**

```bash
uv run python scripts/export_openapi.py
uv run pytest tests/test_wf_list_api.py tests/test_openapi_spec.py tests/test_callback_secret_api.py tests/test_singletons.py -v
uv run lint-imports
```

Expected: PASS; `/workflows` present in committed `openapi.json`.

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 84` with summary `GET /workflows portal list without config or secret`.

---

### Task 3: Postgres check and docs

**Files:**
- Modify: `tests/test_postgres.py`, `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` (and DESIGN.md only if a "built" note is still missing for D66)

**Interfaces:**
- Consumes: `ServicesObjectsFactory.get_wf_list_service().list`
- Produces: green Postgres coverage for the list path

- [ ] **Step 1: Write the failing Postgres test**

Append to `tests/test_postgres.py`:

```python
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq

def test_wf_list_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    made = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_pg_list",
            engine_type="apache_airflow",
            engine_workflow_id="dag",
            config={"hide": True},
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ctx = WfListCtx(req=WfListReq())
    assert ServicesObjectsFactory.get_wf_list_service().list(ctx) == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == ["t_pg_list"]
    assert all(not hasattr(e, "config") for e in ctx.resp.entries)
```

- [ ] **Step 2: Run when Postgres URL is set (CI always does)**

```bash
# local optional:
# CCA_TEST_POSTGRES_URL=... uv run pytest tests/test_postgres.py::test_wf_list_service_works_on_postgres -v
uv run pytest tests/test_wf_list_service.py tests/test_wf_list_api.py tests/test_singletons.py -v
```

Expected: SQLite suite PASS; Postgres test PASS in CI or when URL is set.

- [ ] **Step 3: Docs**

In `ARCHITECTURE.md`, note `GET /workflows` (D66) under the portal-facing endpoints beside `GET /mios/status`. Confirm `DESIGN.md` section 4.2 already names D66 (done in design).

- [ ] **Step 4: Full local gate then commit**

```bash
npm run local:api:lint
npm run local:api:test
```

Expected: lint and tests green.

Run `/ccaa-commit-push 84` with summary `Postgres list-workflows check and architecture note`.

---

## Self-review

1. **Spec coverage:** `GET /workflows`, safe fields, no `config`, empty `[]`, no secret, API→facade→service→`AppWfDao`, D64 `impl/wf_list/`, singletons, OpenAPI, Postgres — Tasks 1–3. Out of scope left out: filters, start-workflow, portal UI, relocating old facades.
2. **Placeholders:** none; every step has concrete code or commands.
3. **Types:** `WfListEntry` / `WfListOut` fields match; facade method is `list`; factory names `get_wf_list_*`.
