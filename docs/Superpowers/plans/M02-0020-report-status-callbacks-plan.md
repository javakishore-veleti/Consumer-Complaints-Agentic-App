# M02-0020 (#59) Report status callbacks on download DAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `download_cfpb_all` report `started` / `completed` / `failed` to `POST /callbacks/workflow-executions/{execution_id}/status` with `X-Callback-Secret`, using a shared `ccaa` helper and an always-run `notify_finished` task so a crashed download never leaves the execution stuck in `started`.

**Architecture:** Stdlib HTTP client under `Middleware/Airflow-dags/ccaa/status_callback.py` (no `app.*`). DAG keeps D63 download in `resolve_and_download` (reports `started` first) and adds `notify_finished` with `TriggerRule.ALL_DONE`. Base URL and secret come from env else Airflow Variables (`CCA_API_URL`, `CCA_CALLBACK_SECRET`); local Docker uses `http://host.docker.internal:8000`.

**Tech Stack:** Apache Airflow 3.4.0, stdlib `urllib.request`, pytest, `uv`.

Spec: `docs/Superpowers/specs/M02-0020-report-status-callbacks-design.md`. Decisions: D11, D42, D51, D54, D59, D60, D63, **D67** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- Paths are relative to the **repository root** unless a step says otherwise. App tests run from `Middleware/ConsumerComplaintsHandsOn` with `uv run pytest`.
- DAGs live only in `Middleware/Airflow-dags` (D44). Do **not** import `app.*` from any file under that folder.
- Airflow may **read** the operational DB only (D11 / D51); status changes go only through the API callback (D60).
- Scratch / throwaway under `runtime_data/tmp/` (never commit).
- Commit with `/ccaa-commit-push 59` only (never a raw `git commit` that skips the skill).
- Do not open a PR until the story's finishing step; this plan is implementation only after design landed.

## File Structure

| File | Responsibility |
|---|---|
| `Middleware/Airflow-dags/ccaa/status_callback.py` | Resolve URL/secret; POST D60; map HTTP outcomes |
| `Middleware/Airflow-dags/download_cfpb_all.py` | `started` + always-run `notify_finished` |
| `Middleware/ConsumerComplaintsHandsOn/.env.example` | Document `CCA_API_URL` |
| `CICD/Local/airflow/Airflow_Variables_Upsert.txt` | List `CCA_API_URL` for upsert-secrets |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D67 (already written in design story; verify only) |
| `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` | Point at D67 / `CCA_API_URL` if missing |
| `tests/test_ccaa_status_callback.py` | Unit tests for the helper |
| `tests/test_download_cfpb_all_dag_file.py` | Topology / no TODO #59 |

---

### Task 1: Status callback helper (TDD)

**Files:**
- Create: `Middleware/Airflow-dags/ccaa/status_callback.py`
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_ccaa_status_callback.py`

**Interfaces:**
- Produces:
  - `resolve_api_base_url(*, getenv, get_variable) -> str`
  - `resolve_callback_secret(*, getenv, get_variable) -> str`
  - `report_execution_status(execution_id, status, *, engine_run_id=None, message=None, api_base_url=None, callback_secret=None, urlopen=urllib.request.urlopen) -> None`
  - Exception type `CallbackHttpError` (or reuse a clear `RuntimeError` subclass) with `status_code: int | None` for non-2xx/409 responses

- [ ] **Step 1: Write the failing tests**

Create `Middleware/ConsumerComplaintsHandsOn/tests/test_ccaa_status_callback.py`:

```python
"""Unit tests for Middleware/Airflow-dags/ccaa/status_callback.py (D67)."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import status_callback as sc  # noqa: E402


def test_resolve_api_base_url_prefers_env():
    assert (
        sc.resolve_api_base_url(
            getenv=lambda k, default=None: "http://from-env:8000" if k == "CCA_API_URL" else default,
            get_variable=lambda k: "http://from-var:8000",
        )
        == "http://from-env:8000"
    )


def test_resolve_api_base_url_falls_back_to_variable():
    assert (
        sc.resolve_api_base_url(
            getenv=lambda k, default=None: default,
            get_variable=lambda k: "http://host.docker.internal:8000" if k == "CCA_API_URL" else "",
        )
        == "http://host.docker.internal:8000"
    )


def test_resolve_callback_secret_requires_value():
    with pytest.raises(ValueError, match="CCA_CALLBACK_SECRET"):
        sc.resolve_callback_secret(
            getenv=lambda k, default=None: "" if k == "CCA_CALLBACK_SECRET" else default,
            get_variable=lambda k: "",
        )


def _fake_urlopen(status: int, body: bytes = b"{}"):
    def opener(req, timeout=None):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return body

            def getcode(self):
                return status

        if status >= 400:
            raise urllib.error.HTTPError(
                req.full_url if hasattr(req, "full_url") else "http://x",
                status,
                "err",
                hdrs=None,
                fp=io.BytesIO(body),
            )
        return Resp()

    return opener


def test_report_execution_status_posts_started():
    captured = {}

    def opener(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["secret"] = req.headers.get("X-callback-secret") or req.headers.get("X-Callback-Secret")
        captured["body"] = json.loads(req.data.decode("utf-8"))
        class Resp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return b"{}"
            def getcode(self):
                return 200
        return Resp()

    sc.report_execution_status(
        "exec-1",
        "started",
        engine_run_id="manual__2026-01-01",
        api_base_url="http://host.docker.internal:8000/",
        callback_secret="s3cret",
        urlopen=opener,
    )
    assert captured["url"] == (
        "http://host.docker.internal:8000/callbacks/workflow-executions/exec-1/status"
    )
    assert captured["method"] == "POST"
    assert captured["secret"] == "s3cret"
    assert captured["body"] == {"status": "started", "engine_run_id": "manual__2026-01-01"}


def test_report_treats_409_as_success():
    sc.report_execution_status(
        "exec-1",
        "completed",
        api_base_url="http://api",
        callback_secret="s",
        urlopen=_fake_urlopen(409),
    )


def test_report_raises_on_401():
    with pytest.raises(sc.CallbackHttpError) as ei:
        sc.report_execution_status(
            "exec-1",
            "failed",
            message="boom",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=_fake_urlopen(401),
        )
    assert ei.value.status_code == 401
    assert "s" not in str(ei.value)
    assert "s" not in repr(ei.value)


def test_report_raises_on_500_and_connection_error():
    with pytest.raises(sc.CallbackHttpError):
        sc.report_execution_status(
            "exec-1",
            "failed",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=_fake_urlopen(500),
        )

    def boom(req, timeout=None):
        raise urllib.error.URLError("down")

    with pytest.raises(urllib.error.URLError):
        sc.report_execution_status(
            "exec-1",
            "failed",
            api_base_url="http://api",
            callback_secret="s",
            urlopen=boom,
        )


def test_report_rejects_blank_secret_before_http():
    called = False

    def opener(req, timeout=None):
        nonlocal called
        called = True
        raise AssertionError("must not call")

    with pytest.raises(ValueError, match="CCA_CALLBACK_SECRET"):
        sc.report_execution_status(
            "exec-1",
            "started",
            api_base_url="http://api",
            callback_secret="  ",
            urlopen=opener,
        )
    assert called is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_status_callback.py -v
```

Expected: FAIL (import / module not found).

- [ ] **Step 3: Implement minimal helper**

`Middleware/Airflow-dags/ccaa/status_callback.py`:

```python
"""POST workflow-execution status callbacks to the API (D59 / D60 / D67)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable


class CallbackHttpError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _first_nonblank(*values: str | None) -> str | None:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_api_base_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_API_URL"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_API_URL"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_API_URL is required (env or Airflow Variable)")
    return value.rstrip("/")


def resolve_callback_secret(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_CALLBACK_SECRET"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_CALLBACK_SECRET"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_CALLBACK_SECRET is required (env or Airflow Variable)")
    return value


def report_execution_status(
    execution_id: str,
    status: str,
    *,
    engine_run_id: str | None = None,
    message: str | None = None,
    api_base_url: str | None = None,
    callback_secret: str | None = None,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str] | None = None,
) -> None:
    if not execution_id or not str(execution_id).strip():
        raise ValueError("execution_id is required")
    if status not in ("started", "completed", "failed"):
        raise ValueError(f"unsupported status: {status}")

    if get_variable is None:
        def get_variable(name: str) -> str:  # type: ignore[misc]
            from airflow.models import Variable

            return Variable.get(name)

    base = (api_base_url or resolve_api_base_url(getenv=getenv, get_variable=get_variable)).rstrip("/")
    secret = callback_secret if callback_secret is not None else resolve_callback_secret(
        getenv=getenv, get_variable=get_variable
    )
    if not str(secret).strip():
        raise ValueError("CCA_CALLBACK_SECRET is required (env or Airflow Variable)")

    body: dict[str, Any] = {"status": status}
    if engine_run_id:
        body["engine_run_id"] = str(engine_run_id)[:128]
    if message:
        body["message"] = str(message)

    url = f"{base}/callbacks/workflow-executions/{execution_id}/status"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Callback-Secret": str(secret).strip(),
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            code = getattr(resp, "getcode", lambda: 200)()
            if code is not None and int(code) >= 400 and int(code) != 409:
                raise CallbackHttpError(f"callback HTTP {code}", status_code=int(code))
    except urllib.error.HTTPError as e:
        if e.code == 409:
            return
        raise CallbackHttpError(f"callback HTTP {e.code}", status_code=e.code) from e
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_status_callback.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
# via /ccaa-commit-push 59
# message: M02-0020 #59: add ccaa status callback helper
```

---

### Task 2: Wire DAG always-run finalize + config docs (TDD)

**Files:**
- Modify: `Middleware/Airflow-dags/download_cfpb_all.py`
- Modify: `Middleware/ConsumerComplaintsHandsOn/tests/test_download_cfpb_all_dag_file.py`
- Modify: `Middleware/ConsumerComplaintsHandsOn/.env.example`
- Modify: `CICD/Local/airflow/Airflow_Variables_Upsert.txt`
- Modify: `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` (one short note on `CCA_API_URL` if not already covered by the design commit)

**Interfaces:**
- Consumes: `report_execution_status`, `resolve_*` from Task 1; existing `ccaa.db_reader` / `ccaa.download`
- Produces: tasks `resolve_and_download` >> `notify_finished` with `trigger_rule=TriggerRule.ALL_DONE`

- [ ] **Step 1: Update the failing DAG file test**

Replace assertions in `tests/test_download_cfpb_all_dag_file.py`:

```python
"""D44 / D63 / D67: download_cfpb_all DAG file under Middleware/Airflow-dags."""

from tests.conftest import REPO_ROOT

DAG = REPO_ROOT / "Middleware" / "Airflow-dags" / "download_cfpb_all.py"


def test_download_cfpb_all_dag_file_exists_with_dag_id():
    assert DAG.is_file()
    text = DAG.read_text(encoding="utf-8")
    assert 'dag_id="download_cfpb_all"' in text or "dag_id='download_cfpb_all'" in text
    assert "notify_finished" in text
    assert "ALL_DONE" in text or "all_done" in text
    assert "report_execution_status" in text or "status_callback" in text
    assert "TODO story #59" not in text
    assert "from app." not in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_download_cfpb_all_dag_file.py -v
```

Expected: FAIL on `notify_finished` / `TODO story #59` still present.

- [ ] **Step 3: Rewrite the DAG**

`Middleware/Airflow-dags/download_cfpb_all.py`:

```python
"""Download the full CFPB complaints zip (All dataset). D51 / D63 / D67."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.db_reader import (
    load_dataset_locations,
    load_execution_config,
    make_engine,
    resolve_landing_dir,
)
from ccaa.download import download_url_to_path
from ccaa.status_callback import report_execution_status


def _execution_id(context) -> str:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


def resolve_and_download(**context) -> str:
    execution_id = _execution_id(context)
    report_execution_status(
        execution_id,
        "started",
        engine_run_id=_engine_run_id(context),
    )

    db_url = Variable.get("CCA_DB_URL")
    engine = make_engine(db_url)
    with engine.connect() as conn:
        cfg = load_execution_config(conn, execution_id)
        code = cfg.get("dataset_code")
        if not code:
            raise ValueError("config_used.dataset_code is required")
        locs = load_dataset_locations(conn, code)

    url = locs["http"]["path"]
    landing = resolve_landing_dir(
        locs["local"]["local_env_var_name"],
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    name = Path(urlparse(url).path).name or "complaints.csv.zip"
    dest = landing / name
    download_url_to_path(url, dest)
    return str(dest)


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_download")
    ok = upstream is not None and str(upstream.state) == "success"
    if ok:
        report_execution_status(
            execution_id,
            "completed",
            engine_run_id=_engine_run_id(context),
        )
        return
    state = getattr(upstream, "state", None) if upstream else None
    report_execution_status(
        execution_id,
        "failed",
        engine_run_id=_engine_run_id(context),
        message=f"resolve_and_download did not succeed (state={state})",
    )


with DAG(
    dag_id="download_cfpb_all",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "download"],
) as dag:
    download = PythonOperator(
        task_id="resolve_and_download",
        python_callable=resolve_and_download,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    download >> finalize
```

Add to `.env.example` (after `CCA_CALLBACK_SECRET` block):

```bash
# Base URL the Airflow workers use to reach this API for status callbacks (D67).
# From Airflow containers on Docker Desktop: http://host.docker.internal:8000
CCA_API_URL=
```

Add to `Airflow_Variables_Upsert.txt` (with the other names):

```text
CCA_API_URL
```

- [ ] **Step 4: Run focused tests**

```bash
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_status_callback.py tests/test_download_cfpb_all_dag_file.py tests/test_ccaa_download_helpers.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
# via /ccaa-commit-push 59
# message: M02-0020 #59: wire always-run status callbacks on download DAG
```

---

### Task 3: Regression + docs check

**Files:**
- Verify: `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` D67 row present
- Verify: `ARCHITECTURE.md` mentions `CCA_API_URL` / `host.docker.internal` for callbacks

- [ ] **Step 1: Confirm D67 and ARCHITECTURE notes exist** (from the design commit); if ARCHITECTURE still lacks `CCA_API_URL`, add one sentence under §8 next to the callback secret paragraph:

```markdown
Airflow workers resolve `CCA_API_URL` (env or Variable; local Docker default
`http://host.docker.internal:8000`) and POST status callbacks with `X-Callback-Secret` (D67).
```

- [ ] **Step 2: Run lint + the helper/DAG tests**

```bash
cd /path/to/repo/root
npm run local:api:lint
cd Middleware/ConsumerComplaintsHandsOn
uv run pytest tests/test_ccaa_status_callback.py tests/test_download_cfpb_all_dag_file.py tests/test_ccaa_download_helpers.py -v
```

Expected: lint clean; tests PASS.

- [ ] **Step 3: Commit only if docs changed**

```bash
# via /ccaa-commit-push 59
# message: M02-0020 #59: document CCA_API_URL for DAG callbacks
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|---|---|
| Shared `ccaa` HTTP helper, no `app.*` | Task 1 |
| `X-Callback-Secret` + D60 path | Task 1 |
| `CCA_API_URL` env/Variable + `host.docker.internal` | Tasks 1–2 |
| `started` before work | Task 2 |
| Always-run `notify_finished` / `ALL_DONE` | Task 2 |
| Crash → `failed` | Task 2 (`ALL_DONE` + upstream state) |
| 2xx/409 ok; 401/404/422 fail; 5xx/connection raise | Task 1 |
| Upsert list + `.env.example` | Task 2 |
| Update DAG file test (drop TODO #59) | Task 2 |

## Out of scope (do not implement in this plan)

- Live Airflow/container e2e in CI
- Other DAGs
- API endpoint changes
- Compose `extra_hosts` unless a documented Linux gap blocks local use
