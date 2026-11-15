# M02-0009 (#44) Shared-secret authentication for callbacks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A reusable FastAPI dependency that refuses (401) any call without the right `X-Callback-Secret` header, with the secret read from `CCA_CALLBACK_SECRET`, failing closed when it is not configured, so #43 and #77 can protect their routers with one line.

**Architecture:** `CallbackSecretAuth` is a stateless singleton (`SingletonMeta`, D26) in the new package `app/api/security/`, handed out by `ApiObjectsFactory.get_callback_secret_auth()`. Its `__call__` takes the one FastAPI `Request` (D37), reads `get_settings().callback_secret` and compares with `hmac.compare_digest`. Later stories attach it at `include_router(..., dependencies=[Depends(...)])`; this story adds no endpoint and proves the check on a router built inside the tests.

**Tech Stack:** Python 3.13, FastAPI, Starlette `TestClient`, pytest, `uv`, import-linter.

Spec: `docs/Superpowers/specs/M02-0009-callback-secret-design.md`. Decisions: D26, D27, D35, D36, D37, D42, D45, D54, D59 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there. All paths below are relative to it, except the plan and spec paths.
- Names, exactly: class `CallbackSecretAuth`, module `app/api/security/callback_secret_auth.py`, constant `CALLBACK_SECRET_HEADER = "X-Callback-Secret"`, factory method `ApiObjectsFactory.get_callback_secret_auth()`, environment variable `CCA_CALLBACK_SECRET`, setting `Settings.callback_secret`.
- Every refusal is the same: HTTP 401, body `{"detail": "missing or wrong callback secret"}`, header `WWW-Authenticate: X-Callback-Secret`.
- Not configured (unset or blank) means every call is 401. Never accept a call because the secret is missing.
- Compare with `hmac.compare_digest` on UTF-8 bytes, never with `==`.
- Never log, return or put in an exception message the configured secret or the value a caller sent.
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`... (D37, enforced by `tests/test_ctx_only_signatures.py`, which scans `app`, `alembic`, `scripts` and `main.py`). The dependency takes `request: Request`; test helpers take one object too.
- The api package may import `app.core.common` and facade interfaces only (`uv run lint-imports`: 7 contracts kept).
- No new endpoint in the app, so `openapi.json` does not change. `/health` and `/data-ingest-logs` stay open.
- Never commit a real secret or a `.env` file; only `.env.example` with empty values (D42). Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35).
- Commit with `/ccaa-commit-push 44` (it checks lint and tests, writes the `M02-0009 #44: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/config.py` (modify) | `Settings.callback_secret`, read from `CCA_CALLBACK_SECRET` |
| `app/api/security/__init__.py` (create, empty) | the new package |
| `app/api/security/callback_secret_auth.py` (create) | `CallbackSecretAuth`, `CALLBACK_SECRET_HEADER` |
| `app/api/objects_factory.py` (modify) | `get_callback_secret_auth()` |
| `tests/test_callback_secret_auth.py` (create) | the check on its own |
| `tests/test_singletons.py` (modify) | singleton and factory |
| `tests/test_callback_secret_api.py` (create) | the check through HTTP on a throwaway router; existing endpoints stay open |
| `.env.example` (create) | `CCA_CALLBACK_SECRET=` with an empty value |
| `run_app.sh` (modify) | exports `./.env` before starting the API |
| `ARCHITECTURE.md`, `DESIGN.md` (modify) | where the secret is configured; marks D59 as built |

---

### Task 1: the setting, `CallbackSecretAuth` and the factory method

**Files:**
- Modify: `app/core/common/config.py`
- Create: `app/api/security/__init__.py`, `app/api/security/callback_secret_auth.py`
- Modify: `app/api/objects_factory.py`
- Test: `tests/test_callback_secret_auth.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Produces: `Settings.callback_secret: str | None` (trimmed; `None` when unset or blank); `CALLBACK_SECRET_HEADER = "X-Callback-Secret"`; `CallbackSecretAuth.__call__(self, request: Request) -> None` (returns on a match, raises `fastapi.HTTPException` 401 otherwise); `ApiObjectsFactory.get_callback_secret_auth() -> CallbackSecretAuth`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_callback_secret_auth.py`:

```python
"""The callback secret check on its own (D59): the setting, the comparison, failing closed, and no secret in the logs."""

import logging

import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import Headers

from app.api.objects_factory import ApiObjectsFactory
from app.api.security import callback_secret_auth
from app.api.security.callback_secret_auth import CALLBACK_SECRET_HEADER
from app.core.common.config import get_settings

SECRET = "s3cret-value-for-tests"


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


@pytest.fixture
def no_secret(monkeypatch):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)


@pytest.fixture
def auth_log(caplog, monkeypatch):
    """Alembic's fileConfig, run by the migrating fixtures of other tests, disables loggers that already exist."""
    logger = logging.getLogger(callback_secret_auth.__name__)
    monkeypatch.setattr(logger, "disabled", False)
    caplog.set_level(logging.WARNING, logger=logger.name)
    return caplog


def _request(headers: Headers) -> Request:
    return Request({"type": "http", "headers": headers.raw})


def _refused(request: Request) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        ApiObjectsFactory.get_callback_secret_auth()(request)
    return caught.value


def test_the_setting_is_read_trimmed_and_blank_means_not_configured(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "  abc  \n")
    assert get_settings().callback_secret == "abc"
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert get_settings().callback_secret is None
    monkeypatch.delenv("CCA_CALLBACK_SECRET")
    assert get_settings().callback_secret is None


def test_the_settings_repr_never_shows_the_secret(secret):
    assert secret not in repr(get_settings())


def test_the_right_secret_passes(secret):
    assert ApiObjectsFactory.get_callback_secret_auth()(_request(Headers({CALLBACK_SECRET_HEADER: secret}))) is None


def test_the_header_name_is_case_insensitive(secret):
    assert ApiObjectsFactory.get_callback_secret_auth()(_request(Headers({"x-callback-secret": secret}))) is None


def test_a_missing_header_is_401_with_a_challenge(secret):
    error = _refused(_request(Headers({})))
    assert error.status_code == 401
    assert error.detail == "missing or wrong callback secret"
    assert error.headers == {"WWW-Authenticate": "X-Callback-Secret"}


@pytest.mark.parametrize("given", ["wrong", "", SECRET + "x", SECRET[:-1], SECRET.upper(), "é" + SECRET])
def test_a_wrong_secret_is_401(secret, given):
    assert _refused(_request(Headers({CALLBACK_SECRET_HEADER: given}))).status_code == 401


def test_without_a_configured_secret_everything_is_refused(no_secret):
    for headers in (Headers({}), Headers({CALLBACK_SECRET_HEADER: ""}), Headers({CALLBACK_SECRET_HEADER: "anything"})):
        assert _refused(_request(headers)).status_code == 401


def test_a_blank_configured_secret_does_not_accept_an_empty_header(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert _refused(_request(Headers({CALLBACK_SECRET_HEADER: ""}))).status_code == 401


def test_the_secret_is_read_on_every_call(monkeypatch):
    request = _request(Headers({CALLBACK_SECRET_HEADER: "first"}))
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "first")
    assert ApiObjectsFactory.get_callback_secret_auth()(request) is None
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "second")
    assert _refused(request).status_code == 401


def test_refusals_are_logged_without_any_secret(secret, auth_log):
    _refused(_request(Headers({CALLBACK_SECRET_HEADER: "a-guess-from-a-caller"})))
    assert "missing or wrong X-Callback-Secret header" in auth_log.text
    assert secret not in auth_log.text
    assert "a-guess-from-a-caller" not in auth_log.text


def test_a_missing_setting_is_logged(no_secret, auth_log):
    _refused(_request(Headers({CALLBACK_SECRET_HEADER: "a-guess-from-a-caller"})))
    assert "CCA_CALLBACK_SECRET is not set" in auth_log.text
    assert "a-guess-from-a-caller" not in auth_log.text
```

Why the `auth_log` fixture: `alembic/env.py` calls `logging.config.fileConfig`, which disables every logger that exists at that moment. The `client` and `data_dir` fixtures of other test files run the migrations, so in the full suite this module's logger is already disabled when these tests run. The fixture turns it back on for the test only.

In `tests/test_singletons.py`, add after the line `from app.api.routers.data_ingest_api import DataIngestApi`:

```python
from app.api.security.callback_secret_auth import CallbackSecretAuth
```

In `test_factories_return_the_same_object_typed_as_the_interface`, after the line `assert ApiObjectsFactory.get_app() is ApiObjectsFactory.get_app()`, add:

```python
    assert ApiObjectsFactory.get_callback_secret_auth() is ApiObjectsFactory.get_callback_secret_auth()
    assert isinstance(ApiObjectsFactory.get_callback_secret_auth(), CallbackSecretAuth)
```

In `test_the_classes_themselves_are_singletons`, after the line `assert DataIngestApi() is DataIngestApi()`, add:

```python
    assert CallbackSecretAuth() is CallbackSecretAuth()
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_callback_secret_auth.py tests/test_singletons.py -v`
Expected: both files fail at collection with `ModuleNotFoundError: No module named 'app.api.security'`.

- [ ] **Step 3: Add the setting**

In `app/core/common/config.py`, change `from dataclasses import dataclass` to:

```python
from dataclasses import dataclass, field
```

and replace the `Settings` class and `get_settings` (end of file) with:

```python
@dataclass(frozen=True)
class Settings:
    db_url: str
    data_dir: Path
    callback_secret: str | None = field(default=None, repr=False)  # repr=False keeps it out of logs and tracebacks


def get_settings() -> Settings:
    """CCA_DATA_DIR: folder for the SQLite files (default: .data in the project).
    CCA_DB_URL: full SQLAlchemy URL; set it to use Postgres or another database instead of SQLite.
    CCA_CALLBACK_SECRET: the shared secret Airflow sends with every callback (D59). Unset or blank means not
    configured, and then every protected endpoint answers 401."""
    data_dir = Path(os.environ.get("CCA_DATA_DIR", PROJECT_ROOT / ".data")).resolve()
    db_url = os.environ.get("CCA_DB_URL", f"sqlite:///{data_dir}/operational.sqlite")
    callback_secret = os.environ.get("CCA_CALLBACK_SECRET", "").strip() or None
    return Settings(db_url=db_url, data_dir=data_dir, callback_secret=callback_secret)
```

- [ ] **Step 4: Add the check**

Create the empty file `app/api/security/__init__.py`.

Create `app/api/security/callback_secret_auth.py`:

```python
"""The shared-secret check of the endpoints Airflow calls (D59). A singleton, like every class in api.

It is a FastAPI dependency. The API objects factory attaches it to a whole router when it includes the router, never
to single endpoints:

    app.include_router(SomeCallbackApi().router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())])

The secret is read from the settings on every call (so tests can change it) and is never logged or returned. With no
secret configured every call is refused: a missing setting never leaves an endpoint open.
"""

import hmac
import logging

from fastapi import HTTPException, Request, status

from app.core.common.config import get_settings
from app.core.common.singleton import SingletonMeta

CALLBACK_SECRET_HEADER = "X-Callback-Secret"

log = logging.getLogger(__name__)


class CallbackSecretAuth(metaclass=SingletonMeta):
    def __call__(self, request: Request) -> None:
        expected = get_settings().callback_secret
        if expected is None:
            log.warning("callback refused: CCA_CALLBACK_SECRET is not set, so every callback is refused")
            raise self._unauthorized()
        given = request.headers.get(CALLBACK_SECRET_HEADER, "")
        # Constant time, on bytes: compare_digest rejects str with non-ASCII characters.
        if not hmac.compare_digest(given.encode(), expected.encode()):
            log.warning("callback refused: missing or wrong %s header", CALLBACK_SECRET_HEADER)
            raise self._unauthorized()

    @staticmethod
    def _unauthorized() -> HTTPException:
        return HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "missing or wrong callback secret",
            headers={"WWW-Authenticate": CALLBACK_SECRET_HEADER},
        )
```

- [ ] **Step 5: Register it in the api objects factory**

In `app/api/objects_factory.py`, replace the module docstring (line 1) with:

```python
"""Builds the one FastAPI application for the whole project (one OpenAPI spec) and hands out the other singletons of
the api package (the callback secret check, D59). The app is a singleton."""
```

add after the line `from app.api.routers.data_ingest_api import DataIngestApi`:

```python
from app.api.security.callback_secret_auth import CallbackSecretAuth
```

and add this method between `get_app` and `_build_app`:

```python
    @staticmethod
    def get_callback_secret_auth() -> CallbackSecretAuth:
        return CallbackSecretAuth()
```

Do not attach the check to any router in `_build_app`: no endpoint of the app needs it yet (#43 is the first).

- [ ] **Step 6: Run them and see them pass**

Run: `uv run pytest tests/test_callback_secret_auth.py tests/test_singletons.py -v`
Expected: all PASS (16 in `test_callback_secret_auth.py`, 3 in `test_singletons.py`).

- [ ] **Step 7: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; all tests PASS (Postgres tests skipped without `CCA_TEST_POSTGRES_URL`), including `tests/test_ctx_only_signatures.py` and `tests/test_openapi_spec.py`.

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 44` with summary `callback secret check and its factory method` and files `app/core/common/config.py app/api/security/__init__.py app/api/security/callback_secret_auth.py app/api/objects_factory.py tests/test_callback_secret_auth.py tests/test_singletons.py`.

---

### Task 2: through HTTP on a throwaway router, `.env.example`, `run_app.sh` and the docs

**Files:**
- Test: `tests/test_callback_secret_api.py` (create)
- Create: `.env.example`
- Modify: `run_app.sh`, `ARCHITECTURE.md`, `DESIGN.md`

**Interfaces:**
- Consumes: `ApiObjectsFactory.get_callback_secret_auth()` and the 401 contract from Task 1; the `client` fixture of `tests/conftest.py` (the real app on a fresh migrated database).
- Produces: the pattern #43 and #77 copy: `app.include_router(router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())])`.

- [ ] **Step 1: Write the HTTP tests**

Create `tests/test_callback_secret_api.py`:

```python
"""The callback secret through HTTP (D59): a router protected the way #43 and later stories attach it, and the
existing endpoints that stay open. The protected router exists only in this test; the app gains no endpoint."""

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory

SECRET = "s3cret-value-for-tests"
CALLS = []


def _ping() -> dict[str, str]:
    CALLS.append("ping")
    return {"status": "ok"}


@pytest.fixture
def protected():
    """A throwaway app with one router protected at include time, exactly as ApiObjectsFactory will do it."""
    CALLS.clear()
    router = APIRouter(prefix="/test-callbacks")
    router.add_api_route("/ping", _ping, methods=["POST"])
    app = FastAPI()
    app.include_router(router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())])
    return TestClient(app)


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


def test_the_right_secret_reaches_the_endpoint(protected, secret):
    response = protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": secret})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert CALLS == ["ping"]


@pytest.mark.parametrize("headers", [{}, {"X-Callback-Secret": "wrong"}, {"X-Callback-Secret": ""}])
def test_a_missing_or_wrong_secret_is_401_and_the_endpoint_never_runs(protected, secret, headers):
    response = protected.post("/test-callbacks/ping", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or wrong callback secret"}
    assert response.headers["WWW-Authenticate"] == "X-Callback-Secret"
    assert secret not in response.text
    assert CALLS == []


def test_the_secret_in_another_header_is_refused(protected, secret):
    response = protected.post("/test-callbacks/ping", headers={"Authorization": f"Bearer {secret}"})
    assert response.status_code == 401


def test_without_a_configured_secret_the_router_is_closed(protected, monkeypatch):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": ""}).status_code == 401
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": "anything"}).status_code == 401
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": ""}).status_code == 401
    assert CALLS == []


@pytest.mark.parametrize("configured", [SECRET, None])
def test_health_and_the_existing_endpoints_stay_open(client, monkeypatch, configured):
    if configured is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", configured)
    assert client.get("/health").status_code == 200
    assert client.get("/data-ingest-logs").status_code == 200
```

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_callback_secret_api.py -v`
Expected: all 8 PASS on the first run. Task 1 already built the behavior; these tests pin the HTTP contract (status, body, challenge header, the endpoint not running) and the open endpoints that #43 and #77 rely on. If one fails, the Task 1 code is wrong: fix it there, not in the test.

- [ ] **Step 3: Add `.env.example`**

Create `.env.example` (in the app root, next to `run_app.sh`; the root `.gitignore` ignores `.env` at any depth but not `.env.example`):

```
# Copy to .env (git-ignored) and fill in the values. Never commit a real value (D42).
# run_app.sh exports every name set here to the API.

# Shared secret Airflow sends in the X-Callback-Secret header of every callback (D59).
# Without it every callback endpoint answers 401. Generate one with: openssl rand -hex 32
CCA_CALLBACK_SECRET=
```

Check it is not ignored and `.env` is: `git check-ignore -v .env .env.example`
Expected: one line, naming the root `.gitignore` rule `.env` and the path `.env`; nothing for `.env.example`.

- [ ] **Step 4: Export `./.env` in `run_app.sh`**

In `run_app.sh`, replace these lines:

```bash
#   CCA_DB_URL             use another database (for example Postgres) instead of SQLite
set -euo pipefail
cd "$(dirname "$0")"
```

with:

```bash
#   CCA_DB_URL             use another database (for example Postgres) instead of SQLite
#   CCA_CALLBACK_SECRET    shared secret of the endpoints Airflow calls (D59); without it they answer 401
# Every name set in ./.env (git-ignored; the names are in .env.example) is exported first.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
```

Check it (all scratch files in `runtime_data/tmp`, D36; the API runs on a spare port so a running one is not disturbed):

```bash
bash -n run_app.sh && echo syntax-ok
cp .env.example .env
CCA_DATA_DIR="$PWD/../../runtime_data/tmp/m02-0009-run" API_PORT=8765 ./run_app.sh start
curl -s http://127.0.0.1:8765/health
CCA_DATA_DIR="$PWD/../../runtime_data/tmp/m02-0009-run" API_PORT=8765 ./run_app.sh stop
rm .env
rm -rf ../../runtime_data/tmp/m02-0009-run
```

Expected: `syntax-ok`, `API is up: http://127.0.0.1:8765 ...`, `{"status":"ok"}`, `Stopped`. Always run the `stop` and both `rm` lines, also after a failure. Never stage `.env`.

- [ ] **Step 5: Document where the secret is configured**

In `ARCHITECTURE.md`, section `## 8. Local environment`, after the paragraph that starts `From inside an Airflow container, the host machine is reachable as`, add:

```
**Configuration and secrets.** The API reads its settings from environment variables (`app/core/common/config.py`).
`run_app.sh` first exports every name set in the git-ignored `Middleware/ConsumerComplaintsHandsOn/.env`; the committed
`.env.example` next to it lists the names with empty values (D42). `CCA_CALLBACK_SECRET` is the shared secret Airflow
sends in the `X-Callback-Secret` header of every callback; without it every callback endpoint answers 401 (D59).
`/health` and the other endpoints need no secret.
```

In `DESIGN.md`, section `### 4.2 Endpoints`, in the bullet that starts `- The callback endpoints need a **shared secret**`, replace the last sentence `Designed in story #44.` with:

```
Built in story #44 (`CallbackSecretAuth` in `app/api/security/`, `ApiObjectsFactory.get_callback_secret_auth()`); no endpoint uses it yet, #43 is the first.
```

- [ ] **Step 6: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; all tests PASS (Postgres tests skipped), including `tests/test_portability.py` (it scans `.md` files) and `tests/test_openapi_spec.py` (no endpoint was added, so `openapi.json` is unchanged).

- [ ] **Step 7: Commit**

Run `/ccaa-commit-push 44` with summary `callback secret HTTP tests, .env.example and docs` and files `tests/test_callback_secret_api.py .env.example run_app.sh ARCHITECTURE.md DESIGN.md`.

---

## Self-Review (done)

1. **Spec coverage:** naming, the setting with trimming and `repr=False`, fail closed, constant-time compare on bytes, the 401 body and challenge, logging without secrets, the singleton and factory method (Task 1); the router-level attachment exactly as #43 will write it, the endpoint not running on 401, the secret in another header refused, `/health` and `/data-ingest-logs` open with and without a secret, `.env.example`, `run_app.sh`, `ARCHITECTURE.md` and the `DESIGN.md` note (Task 2). The README files hold no configuration, so the spec leaves them unchanged. Out of scope and not built: rotation, per-caller secrets, portal protection, the Airflow side (#59, #77), an OpenAPI security scheme.
2. **Placeholders:** none; every code step shows the full code, and every modification names the exact line it goes after or replaces.
3. **Types and names:** `CallbackSecretAuth`, `CALLBACK_SECRET_HEADER`, `get_callback_secret_auth`, `CCA_CALLBACK_SECRET`, `callback_secret`, `_unauthorized`, `X-Callback-Secret` and the detail text `missing or wrong callback secret` are spelled the same in both tasks and in the spec. `__call__` takes one `Request`, `_unauthorized` and the factory method take nothing, so `tests/test_ctx_only_signatures.py` stays green.
4. **Pre-check:** the code of Tasks 1 and 2 was run once in a scratch copy of the app root under `runtime_data/tmp/` (deleted afterwards): `lint-imports` 7 kept, 0 broken; the full suite 306 passed, 8 skipped (282 before, plus 16 and 8 new tests); `run_app.sh start` with a `.env` copied from `.env.example` came up healthy and stopped cleanly. The logging tests failed in the full suite until the `auth_log` fixture re-enabled the logger that Alembic's `fileConfig` disables; the plan includes that fixture.
5. **Accepted gaps:** the secret is refused only by value; a caller sending it over plain HTTP exposes it on the network (local Docker-to-host traffic now; TLS comes with the cloud milestone). Each refusal logs a warning, so a caller hammering the endpoint fills the log (no rate limit in the MVP). `.env` values with spaces must be quoted, because `run_app.sh` sources the file as shell.
