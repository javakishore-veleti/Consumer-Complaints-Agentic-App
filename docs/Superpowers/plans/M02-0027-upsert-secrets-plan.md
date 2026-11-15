# M02-0027 (#77) Upsert .env values to Airflow Variables Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `POST /management/airflow/upsert-secrets` copies the names in `CICD/Local/airflow/Airflow_Variables_Upsert.txt` from the process environment into Airflow Variables (JWT + Variables REST), returning per-name outcomes never values, protected by `X-Callback-Secret`.

**Architecture:** API → facade (one task) → service → private `AirflowVariablesClient` (`httpx`, mocked in tests). Singletons via package factories (D26). No `init()` yet (D45, D54).

**Tech Stack:** Python 3.11+, FastAPI, httpx (runtime), pytest, uv, import-linter.

Spec: `docs/Superpowers/specs/M02-0027-upsert-secrets-design.md`. Decisions: D5, D11, D26, D29, D35, D36, D37, D42, D45, D51, D54, D59 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there unless a path is absolute from the repo root. Paths under `app/`, `tests/`, `.env.example` are relative to the app root; `CICD/...` and `docs/...` are relative to the repo root (`PROJECT_ROOT.parents[1]`).
- Outcomes are exactly `created`, `updated`, `missing`. Never return or log Variable values, JWT, or passwords.
- Every function takes nothing or exactly one object (D37; `tests/test_ctx_only_signatures.py`).
- `uv run lint-imports`: **Contracts: 7 kept, 0 broken.** The api package imports only common and facade interfaces.
- Never commit `.env` or real secrets. Scratch under `runtime_data/tmp/` (D36).
- Commit with `/ccaa-commit-push 77` only (never raw `git commit`).

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/config.py` | Airflow API Settings + upsert list path |
| `app/core/common/dtos/airflow_upsert_secrets_dtos.py` | Service + client DTOs |
| `app/core/common/dtos/airflow_upsert_secrets_facade_dtos.py` | Facade ctx |
| `app/core/services/impl/airflow_variables_client.py` | JWT + GET/POST/PATCH Variables |
| `app/core/services/airflow_upsert_secrets_service.py` | Interface |
| `app/core/services/impl/airflow_upsert_secrets_service_impl.py` | Read list + env + client |
| `app/core/services/objects_factory.py` | `get_airflow_upsert_secrets_service()` |
| `app/core/facades/airflow_upsert_secrets_facade.py` | Interface |
| `app/core/facades/airflow_upsert_secrets_facade_task.py` | Task ABC |
| `app/core/facades/impl/tasks/airflow_upsert_secrets_call_service_task.py` | One task |
| `app/core/facades/impl/airflow_upsert_secrets_facade_impl.py` | Facade impl |
| `app/core/facades/objects_factory.py` | `get_airflow_upsert_secrets_facade()` |
| `app/api/models/airflow_upsert_secrets_models.py` | Response models |
| `app/api/routers/airflow_upsert_secrets_api.py` | Router |
| `app/api/objects_factory.py` | Include router with callback secret |
| `pyproject.toml` | Move `httpx` to runtime dependencies |
| `CICD/Local/airflow/Airflow_Variables_Upsert.txt` | Initial names |
| `.env.example`, `run_app.sh`, `ARCHITECTURE.md` | Document new env names |
| `openapi.json` | Regenerate |
| `tests/test_airflow_variables_client.py`, `tests/test_airflow_upsert_secrets_service.py`, `tests/test_airflow_upsert_secrets_api.py`, `tests/test_singletons.py` | Tests |

---

### Task 1: Settings, DTOs, `AirflowVariablesClient`, service

**Files:**
- Modify: `app/core/common/config.py`, `pyproject.toml`, `app/core/services/objects_factory.py`
- Create: DTOs, client, service interface + impl
- Test: `tests/test_airflow_variables_client.py`, `tests/test_airflow_upsert_secrets_service.py`

**Interfaces:**
- Produces: `Settings.airflow_api_base_url/username/password`, `airflow_variables_upsert_path`; `AirflowUpsertSecretsService.upsert(ctx) -> int`; outcomes on `ctx.resp.results`.

- [ ] **Step 1: Add httpx as a runtime dependency**

In `pyproject.toml`, move `httpx` from `[dependency-groups] dev` into `[project] dependencies` (keep it in dev too is fine, or only runtime). Then from the app root:

```bash
uv lock && uv sync
```

- [ ] **Step 2: Extend Settings**

Replace `Settings` / `get_settings` in `app/core/common/config.py` with:

```python
@dataclass(frozen=True)
class Settings:
    db_url: str
    data_dir: Path
    callback_secret: str | None = field(default=None, repr=False)
    airflow_api_base_url: str = "http://127.0.0.1:8080"
    airflow_api_username: str = "airflow"
    airflow_api_password: str = field(default="airflow", repr=False)
    airflow_variables_upsert_path: Path = field(
        default_factory=lambda: PROJECT_ROOT.parents[1]
        / "CICD"
        / "Local"
        / "airflow"
        / "Airflow_Variables_Upsert.txt"
    )


def get_settings() -> Settings:
    data_dir = Path(os.environ.get("CCA_DATA_DIR", PROJECT_ROOT / ".data")).resolve()
    db_url = os.environ.get("CCA_DB_URL", f"sqlite:///{data_dir}/operational.sqlite")
    callback_secret = os.environ.get("CCA_CALLBACK_SECRET", "").strip() or None
    base = os.environ.get("CCA_AIRFLOW_API_BASE_URL", "http://127.0.0.1:8080").strip().rstrip("/")
    user = os.environ.get("CCA_AIRFLOW_API_USERNAME", "airflow").strip() or "airflow"
    password = os.environ.get("CCA_AIRFLOW_API_PASSWORD", "airflow")  # keep as configured; default airflow
    upsert_path = PROJECT_ROOT.parents[1] / "CICD" / "Local" / "airflow" / "Airflow_Variables_Upsert.txt"
    return Settings(
        db_url=db_url,
        data_dir=data_dir,
        callback_secret=callback_secret,
        airflow_api_base_url=base or "http://127.0.0.1:8080",
        airflow_api_username=user,
        airflow_api_password=password,
        airflow_variables_upsert_path=upsert_path,
    )
```

- [ ] **Step 3: Create DTOs**

Create `app/core/common/dtos/airflow_upsert_secrets_dtos.py`:

```python
"""Ctx for upserting selected .env names into Airflow Variables (DESIGN.md D42)."""

from dataclasses import dataclass, field

from app.core.common.return_codes import SUCCESS

OUTCOME_CREATED = "created"
OUTCOME_UPDATED = "updated"
OUTCOME_MISSING = "missing"


@dataclass
class UpsertSecretResult:
    name: str
    outcome: str  # created | updated | missing


@dataclass
class AirflowUpsertSecretsReq:
    pass  # no body; reserved for future filters


@dataclass
class AirflowUpsertSecretsResp:
    results: list[UpsertSecretResult] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class AirflowUpsertSecretsCtx:
    req: AirflowUpsertSecretsReq = field(default_factory=AirflowUpsertSecretsReq)
    resp: AirflowUpsertSecretsResp = field(default_factory=AirflowUpsertSecretsResp)


@dataclass
class AirflowVariableUpsertItem:
    name: str
    value: str


@dataclass
class AirflowVariablesUpsertReq:
    items: list[AirflowVariableUpsertItem] = field(default_factory=list)


@dataclass
class AirflowVariablesUpsertResp:
    results: list[UpsertSecretResult] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class AirflowVariablesUpsertCtx:
    req: AirflowVariablesUpsertReq = field(default_factory=AirflowVariablesUpsertReq)
    resp: AirflowVariablesUpsertResp = field(default_factory=AirflowVariablesUpsertResp)
```

Create `app/core/common/dtos/airflow_upsert_secrets_facade_dtos.py`:

```python
from dataclasses import dataclass, field

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    AirflowUpsertSecretsCtx,
    AirflowUpsertSecretsReq,
    AirflowUpsertSecretsResp,
)


@dataclass
class AirflowUpsertSecretsFacadeCtx:
    req: AirflowUpsertSecretsReq = field(default_factory=AirflowUpsertSecretsReq)
    resp: AirflowUpsertSecretsResp = field(default_factory=AirflowUpsertSecretsResp)
    service_ctx: AirflowUpsertSecretsCtx = field(default_factory=AirflowUpsertSecretsCtx)
```

- [ ] **Step 4: Write failing client + service tests**

Create `tests/test_airflow_variables_client.py`:

```python
"""Airflow Variables HTTP client (D42): JWT then GET/POST/PATCH. Values never appear in assertions on logs."""

import httpx
import pytest

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_UPDATED,
    AirflowVariableUpsertItem,
    AirflowVariablesUpsertCtx,
    AirflowVariablesUpsertReq,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.impl.airflow_variables_client import AirflowVariablesClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/auth/token" and request.method == "POST":
        return httpx.Response(201, json={"access_token": "tok"})
    if path == "/api/v2/variables/NEW" and request.method == "GET":
        return httpx.Response(404, json={"detail": "Not Found"})
    if path == "/api/v2/variables" and request.method == "POST":
        return httpx.Response(201, json={"key": "NEW", "value": "x"})
    if path == "/api/v2/variables/OLD" and request.method == "GET":
        return httpx.Response(200, json={"key": "OLD", "value": "old"})
    if path == "/api/v2/variables/OLD" and request.method == "PATCH":
        return httpx.Response(200, json={"key": "OLD", "value": "new"})
    return httpx.Response(500, json={"detail": "unexpected"})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    transport = httpx.MockTransport(_handler)
    return AirflowVariablesClient(transport=transport)


def test_create_and_update(client):
    ctx = AirflowVariablesUpsertCtx(
        req=AirflowVariablesUpsertReq(
            items=[
                AirflowVariableUpsertItem(name="NEW", value="n"),
                AirflowVariableUpsertItem(name="OLD", value="new"),
            ]
        )
    )
    assert client.upsert_all(ctx) == SUCCESS
    assert [(r.name, r.outcome) for r in ctx.resp.results] == [
        ("NEW", OUTCOME_CREATED),
        ("OLD", OUTCOME_UPDATED),
    ]


def test_token_failure_is_failure(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")

    def bad_token(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    client = AirflowVariablesClient(transport=httpx.MockTransport(bad_token))
    ctx = AirflowVariablesUpsertCtx(
        req=AirflowVariablesUpsertReq(items=[AirflowVariableUpsertItem(name="A", value="v")])
    )
    assert client.upsert_all(ctx) == FAILURE
```

Create `tests/test_airflow_upsert_secrets_service.py`:

```python
"""Upsert-secrets service: list file + env + client outcomes (D42)."""

from pathlib import Path

import pytest

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_MISSING,
    OUTCOME_UPDATED,
    AirflowUpsertSecretsCtx,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.objects_factory import ServicesObjectsFactory


@pytest.fixture
def names_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "Airflow_Variables_Upsert.txt"
    path.write_text("# comment\n\nCCA_CALLBACK_SECRET\nCCA_DB_URL\n", encoding="utf-8")
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    # Point Settings at this file by patching get_settings path via monkeypatch on env is hard;
    # patch the path on the service by setting an env the impl reads — impl uses get_settings().
    from app.core.common import config

    real = config.get_settings

    def _settings():
        s = real()
        object.__setattr__(s, "airflow_variables_upsert_path", path)  # frozen — use replace pattern instead
        return s

    # Settings is frozen: rebuild via monkeypatch of get_settings
    def fake_get_settings():
        base = real()
        return config.Settings(
            db_url=base.db_url,
            data_dir=base.data_dir,
            callback_secret=base.callback_secret,
            airflow_api_base_url=base.airflow_api_base_url,
            airflow_api_username=base.airflow_api_username,
            airflow_api_password=base.airflow_api_password,
            airflow_variables_upsert_path=path,
        )

    monkeypatch.setattr(config, "get_settings", fake_get_settings)
    return path


def test_missing_name_is_failure_and_others_still_run(names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "s3cret")
    monkeypatch.delenv("CCA_DB_URL", raising=False)

    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod
    from app.core.common.dtos.airflow_upsert_secrets_dtos import (
        AirflowVariablesUpsertCtx,
        UpsertSecretResult as R,
        OUTCOME_UPDATED,
    )
    from app.core.common.return_codes import SUCCESS as OK

    class FakeClient:
        def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
            ctx.resp.results = [R(name=i.name, outcome=OUTCOME_UPDATED) for i in ctx.req.items]
            ctx.resp.code = OK
            return OK

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", lambda: FakeClient())
    ctx = AirflowUpsertSecretsCtx()
    code = ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx)
    assert code == FAILURE
    assert [(r.name, r.outcome) for r in ctx.resp.results] == [
        ("CCA_CALLBACK_SECRET", OUTCOME_UPDATED),
        ("CCA_DB_URL", OUTCOME_MISSING),
    ]


def test_all_present_is_success(names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "s3cret")
    monkeypatch.setenv("CCA_DB_URL", "sqlite:///x")

    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod
    from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowVariablesUpsertCtx, UpsertSecretResult as R
    from app.core.common.return_codes import SUCCESS as OK

    class FakeClient:
        def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
            ctx.resp.results = [R(name=i.name, outcome=OUTCOME_CREATED) for i in ctx.req.items]
            ctx.resp.code = OK
            return OK

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", lambda: FakeClient())
    ctx = AirflowUpsertSecretsCtx()
    assert ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx) == SUCCESS
    assert all(r.outcome == OUTCOME_CREATED for r in ctx.resp.results)
```

- [ ] **Step 5: Run tests — expect FAIL (modules missing)**

```bash
uv run pytest tests/test_airflow_variables_client.py tests/test_airflow_upsert_secrets_service.py -v
```

Expected: import / attribute errors.

- [ ] **Step 6: Implement client**

Create `app/core/services/impl/airflow_variables_client.py`. **No `SingletonMeta`** (service is the singleton). **Inline JWT and GET/POST/PATCH in `upsert_all`** — no multi-arg helpers (`_token` / `_upsert_one` would break D37 / `tests/test_ctx_only_signatures.py`). Optional `transport=` is for `httpx.MockTransport` in tests only.

```python
"""HTTP client for Airflow 3 Variables API (JWT). Never logs values or tokens. Helpers are inlined (D37)."""

from __future__ import annotations

import logging

import httpx

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_UPDATED,
    AirflowVariablesUpsertCtx,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS

logger = logging.getLogger(__name__)


class AirflowVariablesClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport

    def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
        ctx.resp.results = []
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
                        "airflow variables upsert failed: token status %s", token_response.status_code
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                token = token_response.json().get("access_token")
                if not isinstance(token, str) or not token:
                    ctx.resp.code = FAILURE
                    return FAILURE
                headers = {"Authorization": f"Bearer {token}"}
                for item in ctx.req.items:
                    get = http.get(f"/api/v2/variables/{item.name}", headers=headers)
                    if get.status_code == 404:
                        created = http.post(
                            "/api/v2/variables",
                            headers=headers,
                            json={"key": item.name, "value": item.value},
                        )
                        if created.status_code not in (200, 201):
                            logger.warning(
                                "airflow variables upsert failed: create status %s", created.status_code
                            )
                            ctx.resp.code = FAILURE
                            return FAILURE
                        ctx.resp.results.append(
                            UpsertSecretResult(name=item.name, outcome=OUTCOME_CREATED)
                        )
                        continue
                    if get.status_code != 200:
                        logger.warning("airflow variables upsert failed: get status %s", get.status_code)
                        ctx.resp.code = FAILURE
                        return FAILURE
                    patched = http.patch(
                        f"/api/v2/variables/{item.name}",
                        headers=headers,
                        json={"key": item.name, "value": item.value},
                    )
                    if patched.status_code != 200:
                        logger.warning(
                            "airflow variables upsert failed: patch status %s", patched.status_code
                        )
                        ctx.resp.code = FAILURE
                        return FAILURE
                    ctx.resp.results.append(UpsertSecretResult(name=item.name, outcome=OUTCOME_UPDATED))
        except httpx.HTTPError:
            logger.warning("airflow variables upsert failed: unreachable")
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
```

- [ ] **Step 7: Implement service**

Create `app/core/services/airflow_upsert_secrets_service.py`:

```python
from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowUpsertSecretsCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsService(metaclass=SingletonMeta):
    @abstractmethod
    def upsert(self, ctx: AirflowUpsertSecretsCtx) -> int:
        """Read Airflow_Variables_Upsert.txt, copy each name from the environment into Airflow Variables.
        SUCCESS when every name is created or updated; FAILURE when any is missing or Airflow fails.
        resp.results never includes values."""
```

Create `app/core/services/impl/airflow_upsert_secrets_service_impl.py`. Inline list-file parsing in `upsert` (no `_read_names(path: Path)` — bare `Path` breaks D37).

```python
import logging
import os

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_MISSING,
    AirflowUpsertSecretsCtx,
    AirflowVariableUpsertItem,
    AirflowVariablesUpsertCtx,
    AirflowVariablesUpsertReq,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.airflow_upsert_secrets_service import AirflowUpsertSecretsService
from app.core.services.impl.airflow_variables_client import AirflowVariablesClient

logger = logging.getLogger(__name__)


class AirflowUpsertSecretsServiceImpl(AirflowUpsertSecretsService):
    def upsert(self, ctx: AirflowUpsertSecretsCtx) -> int:
        ctx.resp.results = []
        path = get_settings().airflow_variables_upsert_path
        try:
            names: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                names.append(text)
        except OSError:
            logger.warning("airflow variables upsert failed: list file unreadable")
            ctx.resp.code = FAILURE
            return FAILURE
        present: list[AirflowVariableUpsertItem] = []
        missing: list[UpsertSecretResult] = []
        for name in names:
            value = os.environ.get(name, "").strip()
            if not value:
                missing.append(UpsertSecretResult(name=name, outcome=OUTCOME_MISSING))
            else:
                present.append(AirflowVariableUpsertItem(name=name, value=value))
        client_ctx = AirflowVariablesUpsertCtx(req=AirflowVariablesUpsertReq(items=present))
        if present:
            code = AirflowVariablesClient().upsert_all(client_ctx)
            if code != SUCCESS:
                ctx.resp.results = list(client_ctx.resp.results) + missing
                ctx.resp.code = FAILURE
                return FAILURE
            ctx.resp.results = list(client_ctx.resp.results) + missing
        else:
            ctx.resp.results = missing
        by_name = {r.name: r for r in ctx.resp.results}
        ctx.resp.results = [by_name[n] for n in names if n in by_name]
        if missing:
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
```

In tests, monkeypatch `get_settings` on the **impl module** (`airflow_upsert_secrets_service_impl.get_settings`), not only on `config`, because the impl binds the name at import time.

Register in `ServicesObjectsFactory`:

```python
@staticmethod
def get_airflow_upsert_secrets_service() -> AirflowUpsertSecretsService:
    from app.core.services.impl.airflow_upsert_secrets_service_impl import AirflowUpsertSecretsServiceImpl

    return AirflowUpsertSecretsServiceImpl()
```

(Add the import of the interface at the top of the factory file.)

- [ ] **Step 8: Run client + service tests — expect PASS**

```bash
uv run pytest tests/test_airflow_variables_client.py tests/test_airflow_upsert_secrets_service.py -v
```

- [ ] **Step 9: Commit**

Run `/ccaa-commit-push 77` with summary `Airflow Variables client and upsert-secrets service` and the files this task touched.

---

### Task 2: Facade, API, list file, config docs, HTTP tests

**Files:**
- Create: facade package pieces, API router + models, `CICD/Local/airflow/Airflow_Variables_Upsert.txt`
- Modify: both objects factories, `.env.example`, `run_app.sh`, `ARCHITECTURE.md`, `tests/test_singletons.py`, openapi
- Test: `tests/test_airflow_upsert_secrets_api.py`

**Interfaces:**
- Consumes: `AirflowUpsertSecretsService.upsert`
- Produces: `POST /management/airflow/upsert-secrets` → 200/422 `UpsertSecretsOut`, 502/401/500 as in the spec

- [ ] **Step 1: Create the names list file (repo root)**

`CICD/Local/airflow/Airflow_Variables_Upsert.txt`:

```text
# Names copied from the environment into Airflow Variables by POST /management/airflow/upsert-secrets (D42).
# Values never appear here. Prefer names containing secret or password so Airflow masks them.

CCA_CALLBACK_SECRET
CCA_DB_URL
```

- [ ] **Step 2: Facade**

Create `app/core/facades/airflow_upsert_secrets_facade.py`:

```python
from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsFacade(metaclass=SingletonMeta):
    @abstractmethod
    def upsert(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        """Copies listed env names into Airflow Variables. Codes match AirflowUpsertSecretsService.upsert."""
```

Create `app/core/facades/airflow_upsert_secrets_facade_task.py`:

```python
from abc import abstractmethod

from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.singleton import SingletonMeta


class AirflowUpsertSecretsFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ...
```

Create `app/core/facades/impl/tasks/airflow_upsert_secrets_call_service_task.py`:

```python
from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowUpsertSecretsCtx
from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.facades.airflow_upsert_secrets_facade_task import AirflowUpsertSecretsFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class AirflowUpsertSecretsCallServiceTask(AirflowUpsertSecretsFacadeTask):
    def execute(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ctx.service_ctx = AirflowUpsertSecretsCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx.service_ctx)
        ctx.resp = ctx.service_ctx.resp
        return code
```

Create `app/core/facades/impl/airflow_upsert_secrets_facade_impl.py`:

```python
from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.impl.tasks.airflow_upsert_secrets_call_service_task import (
    AirflowUpsertSecretsCallServiceTask,
)


class AirflowUpsertSecretsFacadeImpl(AirflowUpsertSecretsFacade):
    def __init__(self):
        self._tasks = [AirflowUpsertSecretsCallServiceTask()]

    def upsert(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
```

Register `FacadesObjectsFactory.get_airflow_upsert_secrets_facade()`.

- [ ] **Step 3: API models + router**

Create `app/api/models/airflow_upsert_secrets_models.py`:

```python
from pydantic import BaseModel, ConfigDict


class UpsertSecretResultOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    outcome: str


class UpsertSecretsOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[UpsertSecretResultOut]
```

Create `app/api/routers/airflow_upsert_secrets_api.py`:

```python
"""POST /management/airflow/upsert-secrets (D42). Callback secret is attached by ApiObjectsFactory."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.models.airflow_upsert_secrets_models import UpsertSecretResultOut, UpsertSecretsOut
from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class AirflowUpsertSecretsApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/management/airflow", tags=["management"])
        self.router.add_api_route(
            "/upsert-secrets",
            self.upsert_secrets,
            methods=["POST"],
            response_model=UpsertSecretsOut,
        )

    def upsert_secrets(self) -> UpsertSecretsOut | JSONResponse:
        ctx = AirflowUpsertSecretsFacadeCtx()
        FacadesObjectsFactory.get_airflow_upsert_secrets_facade().upsert(ctx)
        out = UpsertSecretsOut(
            results=[UpsertSecretResultOut(name=r.name, outcome=r.outcome) for r in ctx.resp.results]
        )
        if ctx.resp.code == SUCCESS:
            return out
        if ctx.resp.code == FAILURE and any(r.outcome == "missing" for r in ctx.resp.results):
            return JSONResponse(status_code=422, content=out.model_dump())
        if ctx.resp.code == FAILURE:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "airflow variables upsert failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
```

Wire in `ApiObjectsFactory._build_app`:

```python
app.include_router(
    ApiObjectsFactory.get_airflow_upsert_secrets_api().router,
    dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())],
)
```

Add `get_airflow_upsert_secrets_api()` returning `AirflowUpsertSecretsApi()`.

- [ ] **Step 4: `.env.example`, `run_app.sh`, ARCHITECTURE**

Append to `.env.example`:

```text
# Operational DB URL (also upserted into Airflow Variables for DAGs, D51 / D42).
CCA_DB_URL=

# Airflow public API (local compose defaults). Used by upsert-secrets only — not upserted into Variables.
CCA_AIRFLOW_API_BASE_URL=http://127.0.0.1:8080
CCA_AIRFLOW_API_USERNAME=airflow
CCA_AIRFLOW_API_PASSWORD=
```

Document the same names in `run_app.sh` header comments and a short paragraph in `ARCHITECTURE.md` section 8 (endpoint path + list file + never log values).

- [ ] **Step 5: Write HTTP tests**

Create `tests/test_airflow_upsert_secrets_api.py` that:
- Sets `CCA_CALLBACK_SECRET`, points upsert path at a temp list file, mocks `AirflowVariablesClient.upsert_all` via monkeypatch on the impl module.
- `POST /management/airflow/upsert-secrets` with the secret → 200 and results without any secret value in `response.text`.
- Missing env name → 422 with `missing` outcome and no values.
- Wrong/missing secret → 401.
- Client FAILURE with no missing → 502.

Also extend `tests/test_singletons.py` for the three new factory getters / classes.

- [ ] **Step 6: Run lint + full suite**

```bash
uv run lint-imports
uv run pytest -q
```

Expected: `Contracts: 7 kept, 0 broken.` and all tests pass.

- [ ] **Step 7: Regenerate OpenAPI**

```bash
# from repo root, or the project npm script:
npm run local:api:openapi
```

Commit `openapi.json` with the rest.

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 77` with summary `upsert-secrets endpoint, list file and docs`.

---

### Task 3: Plan verification scratch (optional during implementation)

Not a product commit. If re-checking examples, copy only the touched modules under `runtime_data/tmp/m02-0027-verify/`, run the two new test modules with mocks, then delete the folder. Do not leave scratch in the tree.

---

## Self-Review (done)

1. **Spec coverage:** list file, env read, JWT+Variables, create/update, per-name results, missing→422, Airflow fail→502, callback secret, Settings, `.env.example`, no value logging, factories, httpx runtime — all have tasks.
2. **Placeholders:** none intentional; client is not a SingletonMeta (called out).
3. **Types:** `AirflowUpsertSecretsCtx`, outcomes, factory method names match across tasks.
4. **D63:** unused; D42 marked built in DESIGN.md by the design step.
5. **Plan verify (throwaway):** assembled under `runtime_data/tmp/m02-0027-repo/`, `lint-imports` 7 kept, full suite **389 passed** with mocked Airflow HTTP; throwaway deleted after.
