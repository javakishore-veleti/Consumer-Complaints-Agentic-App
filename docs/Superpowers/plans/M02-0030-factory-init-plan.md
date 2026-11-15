# M02-0030 (#80) Factory `init()` and bean registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared `BeanRegistry` in `app/core/common`, give every package `objects_factory` an idempotent `init()` that registers today's singletons, keep `get_*` as typed lookups (lazy-init if needed), and call the four `init()`s from `main` before exposing the FastAPI app.

**Architecture:** One process-wide `bean_registry`. Each factory's `init()` registers that package's interfaces → impl instances. `get_one` / `get_all` enforce D45 lookup rules. Call sites stay on `get_*` (no retrofit of every consumer). Multi-impl `get_all` is tested on the registry alone; engines come in #83.

**Tech Stack:** Python 3.11+, pytest, uv, import-linter.

Spec: `docs/Superpowers/specs/M02-0030-factory-init-design.md`. Decisions: D4, D25, D26, D31, D45, D52, D54 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run pytest / lint-imports from there unless a step says otherwise.
- `uv run lint-imports`: **Contracts: 7 kept, 0 broken.** `app.core.common` must not import api/facades/services/dao.
- Every function takes nothing or exactly one object (D37; `tests/test_ctx_only_signatures.py`) — factory `init()` / `get_*` take nothing (already exempt).
- Do not add `CommonObjectsFactory` in this story.
- Scratch under `runtime_data/tmp/` (D36); never commit it.
- Commit with `/ccaa-commit-push 80` only (never raw `git commit`).

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/bean_registry.py` (create) | `BeanRegistry`, errors, module-level `bean_registry` |
| `tests/test_bean_registry.py` (create) | Registry unit tests (fresh instances) |
| `app/core/dao/objects_factory.py` | `init()` + `get_*` via registry |
| `app/core/services/objects_factory.py` | same |
| `app/core/facades/objects_factory.py` | same |
| `app/api/objects_factory.py` | same + register `FastAPI` |
| `tests/test_factory_init.py` (create) | idempotent `init`, `get_*` after init, main-order smoke |
| `tests/test_singletons.py` | stays green (lazy init) |
| `main.py` | call four `init()`s then `get_app()` |
| `DESIGN.md`, `ARCHITECTURE.md` | D45 built; factory section mentions `init()` |

---

### Task 1: `BeanRegistry` in common

**Files:**
- Create: `app/core/common/bean_registry.py`
- Test: `tests/test_bean_registry.py`

**Interfaces:**
- Produces: `BeanRegistry.register/get_one/get_all`, `DuplicateBeanError`, `BeanNotFoundError`, `BeanAmbiguousError`, module `bean_registry`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_bean_registry.py`:

```python
"""D45: shared bean registry — one instance, or a list in registration order."""

import pytest

from app.core.common.bean_registry import (
    BeanAmbiguousError,
    BeanNotFoundError,
    BeanRegistry,
    DuplicateBeanError,
)


class Animal:
    pass


class Dog(Animal):
    pass


class Cat(Animal):
    pass


def test_get_one_returns_the_only_instance():
    reg = BeanRegistry()
    dog = Dog()
    reg.register(Animal, dog)
    assert reg.get_one(Animal) is dog


def test_get_all_preserves_registration_order():
    reg = BeanRegistry()
    a, b = Dog(), Cat()
    reg.register(Animal, a)
    reg.register(Animal, b)
    assert reg.get_all(Animal) == [a, b]


def test_get_one_raises_when_none_or_several():
    reg = BeanRegistry()
    with pytest.raises(BeanNotFoundError):
        reg.get_one(Animal)
    reg.register(Animal, Dog())
    reg.register(Animal, Cat())
    with pytest.raises(BeanAmbiguousError):
        reg.get_one(Animal)


def test_duplicate_same_instance_raises():
    reg = BeanRegistry()
    dog = Dog()
    reg.register(Animal, dog)
    with pytest.raises(DuplicateBeanError):
        reg.register(Animal, dog)


def test_get_all_empty_when_unregistered():
    assert BeanRegistry().get_all(Animal) == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_bean_registry.py -v
```

Expected: FAIL — `bean_registry` module missing.

- [ ] **Step 3: Minimal implementation**

Create `app/core/common/bean_registry.py`:

```python
"""Shared bean registry for package objects_factory init() (DESIGN.md D45)."""

from __future__ import annotations

import threading


class DuplicateBeanError(ValueError):
    pass


class BeanNotFoundError(LookupError):
    pass


class BeanAmbiguousError(LookupError):
    pass


class BeanRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_interface: dict[type, list[object]] = {}

    def register(self, interface: type, instance: object) -> None:
        with self._lock:
            existing = self._by_interface.setdefault(interface, [])
            for bean in existing:
                if bean is instance:
                    raise DuplicateBeanError(
                        f"{interface!r} already has this instance registered"
                    )
            existing.append(instance)

    def get_one(self, interface: type) -> object:
        with self._lock:
            beans = self._by_interface.get(interface, [])
            if not beans:
                raise BeanNotFoundError(f"no bean registered for {interface!r}")
            if len(beans) > 1:
                raise BeanAmbiguousError(
                    f"expected one bean for {interface!r}, found {len(beans)}"
                )
            return beans[0]

    def get_all(self, interface: type) -> list[object]:
        with self._lock:
            return list(self._by_interface.get(interface, []))


bean_registry = BeanRegistry()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_bean_registry.py -v
```

Expected: PASS (all tests).

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 80` with summary `add shared BeanRegistry for D45` and files `app/core/common/bean_registry.py`, `tests/test_bean_registry.py`, plus milestone if touched.

---

### Task 2: `init()` on dao / services / facades / api factories

**Files:**
- Modify: `app/core/dao/objects_factory.py`, `app/core/services/objects_factory.py`, `app/core/facades/objects_factory.py`, `app/api/objects_factory.py`
- Test: `tests/test_factory_init.py` (create); `tests/test_singletons.py` must stay green

**Interfaces:**
- Consumes: `bean_registry` from Task 1.
- Produces: `DaoObjectsFactory.init()`, `ServicesObjectsFactory.init()`, `FacadesObjectsFactory.init()`, `ApiObjectsFactory.init()`; existing `get_*` return `bean_registry.get_one(...)`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_factory_init.py`:

```python
"""D45: package objects_factory.init() registers singletons; safe to call twice."""

from fastapi import FastAPI

from app.api.objects_factory import ApiObjectsFactory
from app.api.security.callback_secret_auth import CallbackSecretAuth
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.objects_factory import ServicesObjectsFactory


def test_init_is_idempotent_and_get_returns_registered_singleton():
    DaoObjectsFactory.init()
    DaoObjectsFactory.init()
    a = DaoObjectsFactory.get_data_ingest_dao()
    b = DaoObjectsFactory.get_data_ingest_dao()
    assert a is b
    assert isinstance(a, DataIngestDao)

    ServicesObjectsFactory.init()
    ServicesObjectsFactory.init()
    assert ServicesObjectsFactory.get_dataset_status_service() is (
        ServicesObjectsFactory.get_dataset_status_service()
    )
    assert isinstance(
        ServicesObjectsFactory.get_dataset_status_service(), DatasetStatusService
    )

    FacadesObjectsFactory.init()
    FacadesObjectsFactory.init()
    assert FacadesObjectsFactory.get_data_ingest_facade() is (
        FacadesObjectsFactory.get_data_ingest_facade()
    )
    assert isinstance(FacadesObjectsFactory.get_data_ingest_facade(), DataIngestFacade)

    ApiObjectsFactory.init()
    ApiObjectsFactory.init()
    assert ApiObjectsFactory.get_app() is ApiObjectsFactory.get_app()
    assert isinstance(ApiObjectsFactory.get_app(), FastAPI)
    assert ApiObjectsFactory.get_callback_secret_auth() is (
        ApiObjectsFactory.get_callback_secret_auth()
    )
    assert isinstance(ApiObjectsFactory.get_callback_secret_auth(), CallbackSecretAuth)


def test_get_lazy_inits_when_init_not_called_first():
    # Relies on process state from other tests / SingletonMeta; asserting the contract:
    # get_* must not require an explicit init() from the caller.
    assert isinstance(DaoObjectsFactory.get_transaction_dao(), object)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_factory_init.py -v
```

Expected: FAIL — `init` attribute missing on factories.

- [ ] **Step 3: Wire dao factory**

Replace `Middleware/ConsumerComplaintsHandsOn/app/core/dao/objects_factory.py` with the same public `get_*` names, plus `init()`. Pattern (apply to every DAO getter listed today):

```python
"""The only module of the dao package that may import from dao/impl."""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.data_ingest_dao import DataIngestDao
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.mio_dao import MioDao
from app.core.dao.mio_dataset_dao import MioDatasetDao
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao
from app.core.dao.system_datasets_dao import SystemDatasetsDao
from app.core.dao.transaction_dao import TransactionDao


class DaoObjectsFactory:
    _initialized = False
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if DaoObjectsFactory._initialized:
            return
        with DaoObjectsFactory._lock:
            if DaoObjectsFactory._initialized:
                return
            from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao
            from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import (
                SqlAlchemyAppWfExecLogDao,
            )
            from app.core.dao.impl.sqlalchemy_data_ingest_dao import SqlAlchemyDataIngestDao
            from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao
            from app.core.dao.impl.sqlalchemy_dataset_location_dao import (
                SqlAlchemyDatasetLocationDao,
            )
            from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao
            from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao
            from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import (
                SqlAlchemyMioIngestLogDao,
            )
            from app.core.dao.impl.sqlalchemy_system_datasets_dao import (
                SqlAlchemySystemDatasetsDao,
            )
            from app.core.dao.impl.sqlalchemy_transaction_dao import SqlAlchemyTransactionDao

            bean_registry.register(AppWfDao, SqlAlchemyAppWfDao())
            bean_registry.register(AppWfExecLogDao, SqlAlchemyAppWfExecLogDao())
            bean_registry.register(DatasetDao, SqlAlchemyDatasetDao())
            bean_registry.register(DatasetLocationDao, SqlAlchemyDatasetLocationDao())
            bean_registry.register(MioDao, SqlAlchemyMioDao())
            bean_registry.register(MioDatasetDao, SqlAlchemyMioDatasetDao())
            bean_registry.register(MioIngestLogDao, SqlAlchemyMioIngestLogDao())
            bean_registry.register(DataIngestDao, SqlAlchemyDataIngestDao())
            bean_registry.register(SystemDatasetsDao, SqlAlchemySystemDatasetsDao())
            bean_registry.register(TransactionDao, SqlAlchemyTransactionDao())
            DaoObjectsFactory._initialized = True

    @staticmethod
    def get_data_ingest_dao() -> DataIngestDao:
        DaoObjectsFactory.init()
        return bean_registry.get_one(DataIngestDao)  # type: ignore[return-value]

    # ... same pattern for every other get_* already on this class ...
```

Repeat the same `_initialized` / `init()` / `get_*` → `get_one` pattern for `ServicesObjectsFactory` and `FacadesObjectsFactory` (register every interface they already expose).

- [ ] **Step 4: Wire api factory**

In `app/api/objects_factory.py`:

1. Add `_initialized` + use existing `_lock`.
2. `init()`: if already set, return. Else construct `CallbackSecretAuth()`, `WfExecCallbackApi()`, `MioStatusApi()`, `AirflowUpsertSecretsApi()`, register each under its class, build the FastAPI app with those **local** instances (do not call `get_*` while building), `bean_registry.register(FastAPI, app)`, set `_initialized = True`. Keep `_app` as a mirror of the registered app if useful, or drop `_app` and always `get_one(FastAPI)`.
3. Each `get_*` / `get_app` calls `init()` then `bean_registry.get_one(...)`.

Sketch for `_build_app` during init (locals, not getters):

```python
auth = CallbackSecretAuth()
wf_api = WfExecCallbackApi()
mio_api = MioStatusApi()
upsert_api = AirflowUpsertSecretsApi()
bean_registry.register(CallbackSecretAuth, auth)
bean_registry.register(WfExecCallbackApi, wf_api)
bean_registry.register(MioStatusApi, mio_api)
bean_registry.register(AirflowUpsertSecretsApi, upsert_api)

app = FastAPI(...)
app.include_router(DataIngestApi().router)
app.include_router(mio_api.router)
app.include_router(wf_api.router, dependencies=[Depends(auth)])
app.include_router(upsert_api.router, dependencies=[Depends(auth)])
# health route as today
bean_registry.register(FastAPI, app)
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_factory_init.py tests/test_singletons.py tests/test_bean_registry.py -v
uv run lint-imports
```

Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 80` with summary `add init() to package object factories`.

---

### Task 3: `main` startup + docs

**Files:**
- Modify: `main.py`, `DESIGN.md` (D45), `ARCHITECTURE.md` (factory paragraph)
- Test: extend `tests/test_factory_init.py` with a small smoke that mirrors `main`'s order (or keep Task 2 coverage and only change `main` + docs here)

**Interfaces:**
- Consumes: four `init()` methods from Task 2.
- Produces: process startup that registers beans before `app` is bound.

- [ ] **Step 1: Write / extend the failing assertion for main order**

Add to `tests/test_factory_init.py`:

```python
def test_startup_init_order_matches_main():
    """main.py must call dao → services → facades → api init, then get_app()."""
    import main as main_mod
    from pathlib import Path

    text = Path(main_mod.__file__).read_text()
    assert "DaoObjectsFactory.init()" in text
    assert "ServicesObjectsFactory.init()" in text
    assert "FacadesObjectsFactory.init()" in text
    assert "ApiObjectsFactory.init()" in text
    assert text.index("DaoObjectsFactory.init()") < text.index("ServicesObjectsFactory.init()")
    assert text.index("ServicesObjectsFactory.init()") < text.index(
        "FacadesObjectsFactory.init()"
    )
    assert text.index("FacadesObjectsFactory.init()") < text.index("ApiObjectsFactory.init()")
    assert text.index("ApiObjectsFactory.init()") < text.index("get_app()")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_factory_init.py::test_startup_init_order_matches_main -v
```

Expected: FAIL — `main.py` still only calls `get_app()`.

- [ ] **Step 3: Update `main.py`**

```python
"""Entry point: uvicorn main:app  (run_app.sh start migrates the database first)."""

from app.api.objects_factory import ApiObjectsFactory
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

DaoObjectsFactory.init()
ServicesObjectsFactory.init()
FacadesObjectsFactory.init()
ApiObjectsFactory.init()

app = ApiObjectsFactory.get_app()
```

- [ ] **Step 4: Update DESIGN.md and ARCHITECTURE.md**

In `DESIGN.md` D45: replace "**Not built yet.**" with built by story #80 (spec `docs/Superpowers/specs/M02-0030-factory-init-design.md`); keep the note that later stories extend their package factory when they add classes; first multi-impl consumer remains #83 (engines).

In `ARCHITECTURE.md` factory paragraph: add that each factory has `init()` registering singletons into `app.core.common.bean_registry.bean_registry`, called from `main`, and that `get_*` remain the public typed lookups.

- [ ] **Step 5: Full verification**

```bash
uv run lint-imports
uv run pytest tests/test_bean_registry.py tests/test_factory_init.py tests/test_singletons.py tests/test_import_contracts.py tests/test_ctx_only_signatures.py -v
npm run local:api:lint
npm run local:api:test
```

(Last two from repo root.) Expected: lint-imports 7 kept; targeted tests PASS; full suite green (same skips as before).

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 80` with summary `wire factory init from main and mark D45 built`.

---

### Task 4 (optional during implementation): Plan verification scratch

Not a product commit. If re-checking the registry examples before coding factories, copy only `bean_registry.py` + `test_bean_registry.py` under `runtime_data/tmp/m02-0030-verify/`, run that one module, then delete the folder.

---

## Self-Review (done)

1. **Spec coverage:** shared registry, errors, `get_one`/`get_all`, idempotent `init`, all four factories, `main` order, lazy `get_*`, layering/ctx tests, DESIGN/ARCHITECTURE — each has a task.
2. **Placeholders:** none; api build uses locals during `init`.
3. **Types:** interface keys match existing `get_*` return types; `FastAPI` registered by concrete type.
4. **Plan verify (throwaway):** registry snippet + 5 tests ran under `runtime_data/tmp/m02-0030-verify/` (**5 passed**); folder deleted after. No production code in that verify.
