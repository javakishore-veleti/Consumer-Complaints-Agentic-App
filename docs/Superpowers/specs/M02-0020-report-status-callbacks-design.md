# M02-0020 (#59) Report started, completed and failed from the download DAG

Decisions: D11, D42, D51, D54, D59, D60, D63 and **D67** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D67); review and reverse if needed. D65 is reserved by story #62; D66 by story #84 — this story uses **D67**.

## Goal

The `download_cfpb_all` DAG (and shared helpers) call the Phase 2 status callback (`POST /callbacks/workflow-executions/{execution_id}/status`, D60) with `X-Callback-Secret` (D59). A **final cleanup task always runs** (`trigger_rule=all_done`) so a hard crash of the download task never leaves the execution stuck in `started`. From inside Airflow containers the API base URL uses the documented `host.docker.internal` pattern (ARCHITECTURE §8).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | `try` / `except` / `finally` inside one download task only | Simple; a SIGKILL / OOM / worker death skips `finally`, so the row can stay `started` |
| B | Airflow `on_success_callback` / `on_failure_callback` only | Not a task; harder to unit-test; still weak when the worker process dies mid-callback |
| C (chosen) | Separate `notify_finished` task with `TriggerRule.ALL_DONE`, plus `started` at the start of the download task; shared HTTP helper under `ccaa/` | Scheduler still schedules the final task after a failed/up-for-retry/upstream-failed download; matches the story's "final task always runs"; testable without a live Airflow scheduler |

## Decision D67 (summary)

1. **Client:** `Middleware/Airflow-dags/ccaa/status_callback.py` posts JSON to D60. **Must not import `app.*`.** Stdlib only (`urllib.request`), same dependency bar as `ccaa/download.py`.
2. **URL:** resolve `CCA_API_URL` from the worker environment first, else Airflow Variable of the same name (same pattern as `LOCAL_DATA_PATH_*` in D63). Local Docker value is `http://host.docker.internal:8000` (API on the host, ARCHITECTURE §8). No trailing slash required; the client joins the path.
3. **Secret:** `CCA_CALLBACK_SECRET` from env else Variable (already upserted by #77). Sent as header `X-Callback-Secret`. Missing/blank secret fails the callback call loudly (raise) — do not POST without it.
4. **HTTP semantics (pinned by D60's "for #59" notes):** treat **2xx and 409** as success (idempotent / already moved); **401, 404, 422** as non-retryable bugs (raise a specific error, no Airflow retry hoped for beyond the task's normal retries if configured); **5xx and connection/timeout errors** as retryable (raise so Airflow can retry the task).
5. **DAG topology for `download_cfpb_all`:**
   - `resolve_and_download` — reports `started` **before** any download/DB work; then does the existing D63 download; on success does **not** report completed itself.
   - `notify_finished` — `trigger_rule=TriggerRule.ALL_DONE`, downstream of `resolve_and_download`; inspects the upstream task instance state; POSTs `completed` if upstream succeeded, else `failed` with a short `message` (exception summary or `"upstream task did not succeed"`).
6. **`engine_run_id`:** optional body field; send Airflow's `run_id` from the task context (truncated to 128 chars) on every callback when available.
7. **Config surface:** add `CCA_API_URL` to `.env.example` and `CICD/Local/airflow/Airflow_Variables_Upsert.txt`. Document the `host.docker.internal` local default in those comments and ARCHITECTURE if needed. Do not hardcode the URL in the DAG file.
8. **Crash paths:**
   - Download raises normally → `notify_finished` still runs → `failed`.
   - Worker killed after `started` → Airflow marks download failed/up_for_retry; when the TI is terminal-failed (or after retries exhausted), `notify_finished` runs → `failed`.
   - `started` never sent (crash before the first POST returns) → `notify_finished` may POST `failed` from `requested` (allowed by D30/D60); preferred over leaving the row forever `requested` while Airflow shows a failed run.
   - `notify_finished` itself fails with 5xx/connection → Airflow retries that task only; download is not re-run.
9. **Out of band:** no `rows_loaded` / volume fields for this download DAG (no ingest row on the MVP All download). No changes to the FastAPI callback endpoint.

## Layout

| Path | Role |
|---|---|
| `Middleware/Airflow-dags/ccaa/status_callback.py` | Resolve URL/secret; POST status; map HTTP outcomes |
| `Middleware/Airflow-dags/download_cfpb_all.py` | Wire `started` + always-run `notify_finished`; remove #59 TODO stubs |
| `Middleware/ConsumerComplaintsHandsOn/.env.example` | Document `CCA_API_URL` |
| `CICD/Local/airflow/Airflow_Variables_Upsert.txt` | Add `CCA_API_URL` |
| `tests/test_ccaa_status_callback.py` | Unit tests for the helper (mocked HTTP) |
| `tests/test_download_cfpb_all_dag_file.py` | Assert topology markers (`notify_finished`, `ALL_DONE` / `all_done`); drop `TODO story #59` |

## Runtime flow

```text
dag_run.conf.execution_id
        │
        ▼
resolve_and_download
        │  POST .../status  {status: started, engine_run_id?}
        │  X-Callback-Secret: <CCA_CALLBACK_SECRET>
        │  base: CCA_API_URL  (env → Variable; Docker: host.docker.internal:8000)
        │
        ├─► D63 download (db_reader + download_url_to_path)
        │
        ▼  (always: TriggerRule.ALL_DONE)
notify_finished
        │  if upstream success → completed
        │  else               → failed (+ message)
        ▼
POST .../status  {status: completed|failed, engine_run_id?, message?}
```

### Helper contract

```python
def resolve_api_base_url(*, getenv=os.getenv, get_variable) -> str: ...
def resolve_callback_secret(*, getenv=os.getenv, get_variable) -> str: ...

def report_execution_status(
    execution_id: str,
    status: str,  # "started" | "completed" | "failed"
    *,
    engine_run_id: str | None = None,
    message: str | None = None,
    api_base_url: str | None = None,
    callback_secret: str | None = None,
    urlopen=...,  # injectable for tests
) -> None:
    """POST D60. Raises on non-success per D67 HTTP rules. Never logs the secret."""
```

URL built as `{api_base_url.rstrip("/")}/callbacks/workflow-executions/{execution_id}/status`.

### DAG task contracts

- `resolve_and_download(**context)` — requires `dag_run.conf.execution_id`; calls `report_execution_status(..., "started")` first; then existing download logic; re-raises download errors (no completed/failed here).
- `notify_finished(**context)` — reads `execution_id` from conf; determines success via `context["ti"].get_dagrun().get_task_instance("resolve_and_download").state` (or equivalent Airflow 3.4 API); reports `completed` or `failed`. Missing `execution_id` raises.

## Tests

| Test | Asserts |
|---|---|
| Unit: `status_callback` | Builds correct URL/path; sends `X-Callback-Secret` and JSON body; 200 and 409 ok; 401/404/422 raise; 500 and URLError raise; blank secret raises before HTTP; never includes secret in exception message |
| Unit: resolve helpers | env wins over Variable; Variable used when env unset |
| Path: DAG file | Contains `notify_finished`, `ALL_DONE` or `all_done`, `status_callback` / `report_execution_status`; no `TODO story #59`; no `from app.` |
| Manual (not CI) | From Airflow container: callback reaches host API; kill download mid-run and confirm exec log ends `failed` |

Tests live under `Middleware/ConsumerComplaintsHandsOn/tests/` with `Middleware/Airflow-dags` on `sys.path` (same pattern as #57).

## Out of scope

- Changing `WfExecCallbackApi` / D60 request shape.
- Start-workflow API (#42) or Airflow engine start (#60).
- Other DAGs (ingest, 3-month filter).
- Retry policy tuning beyond Airflow defaults for the finalize task.
- Docker Compose `extra_hosts` for Linux-only `host.docker.internal` (document if missing; add only if local Linux compose already needs it — Mac Docker Desktop provides it).
- Writing status into the DB from Airflow (still forbidden, D11 / D51).
