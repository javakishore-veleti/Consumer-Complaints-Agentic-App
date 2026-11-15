# M02-0018 (#57) Download DAG for the All dataset

Decisions: D11, D42, D43, D44, D51, D52, D54, D57, D62, **D63** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Goal

An Airflow DAG that downloads the full CFPB Consumer Complaint Database zip. It appears under `Middleware/Airflow-dags`, is registered in `app_workflows`, and writes the file to the catalog's `local` location. The API passes only `execution_id` (D51); the DAG reads workflow config and dataset locations from the operational database via Airflow Variable `CCA_DB_URL`. Status callback reporting is story #59 — this story downloads successfully and leaves no-op / TODO hooks only.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Hardcode the CFPB URL and a host path in the DAG | Fast, but rejects D57 / the open item (must use location rows) |
| B | `config` holds `source_location_id` and `landing_location_id` UUIDs | Explicit; seed must stay in sync with catalog ids; more conf surface |
| C (chosen) | `config` holds `dataset_code: "CFPB"`; DAG loads that dataset's locations and picks **source = `http`**, **landing = `local`** by `location_type` (D63) | Smallest coherent design; matches seed #86; no MIO/ingest required for MVP |

## Decision D63 (summary)

1. **Source** = the dataset's `datasets_location` row with `location_type=http` (`path` is the URL).
2. **Landing** = the same dataset's row with `location_type=local` (`local_env_var_name`, e.g. `LOCAL_DATA_PATH_CFPB`); resolve the directory from the Airflow worker environment, falling back to an Airflow Variable of the same name; write `complaints.csv.zip` under that directory.
3. **Workflow** `download_cfpb_all`, `engine_type=apache_airflow`, `engine_workflow_id=download_cfpb_all` (DAG id), `config={"dataset_code":"CFPB"}`, seeded by Alembic `0008`.
4. **Run conf:** `{"execution_id": "<uuid>"}` (required). Optional `mio_id` is ignored in MVP (MIO labels are not data selectors, D57; attaching workflows to MIOs stays open).
5. **DB access:** a small standalone reader under `Middleware/Airflow-dags/ccaa/` using SQLAlchemy `text` queries against `CCA_DB_URL`. **Must not import `app.*`.**
6. **Docker / SQLite (D51):** when Airflow runs in Docker, prefer a **Postgres** `CCA_DB_URL` the containers can reach. Mounting the API's SQLite `.data` directory into Airflow is documented as a fragile fallback only (locking / path mismatch). Landing directory must also be writable inside the worker (compose mount + `LOCAL_DATA_PATH_CFPB`).

## Layout

| Path | Role |
|---|---|
| `Middleware/Airflow-dags/download_cfpb_all.py` | DAG definition (`dag_id="download_cfpb_all"`) |
| `Middleware/Airflow-dags/ccaa/__init__.py` | Package marker (no DAG objects) |
| `Middleware/Airflow-dags/ccaa/db_reader.py` | Read-only catalog / exec-log queries |
| `Middleware/Airflow-dags/ccaa/download.py` | HTTP download helper (stream to landing path) |
| `alembic/versions/0008_seed_download_cfpb_all_workflow.py` | Seed `app_workflows` row |
| `.env.example` + `Airflow_Variables_Upsert.txt` | Document / upsert `LOCAL_DATA_PATH_CFPB` (and existing `CCA_DB_URL`) |

## Runtime flow

```text
dag_run.conf.execution_id
        │
        ▼
Variable CCA_DB_URL ──► ccaa.db_reader
        │                   │
        │                   ├─ app_workflows_exec_log by id → config_used.dataset_code
        │                   ├─ datasets by code
        │                   └─ datasets_location for dataset → http path + local env name
        ▼
resolve LOCAL_DATA_PATH_* (env, else Variable)
        │
        ▼
ccaa.download.download_url_to_path(url, landing_dir / "complaints.csv.zip")
        │
        ▼
TODO #59 status hooks (no-op placeholders only)
```

### DB reader contract

- `connect(db_url: str) -> Engine` — for SQLite URLs that point at the API's operational file, ATTACH admin schema files the same way the app does (`consumer_comp_admin_db.sqlite` beside the main file). Prefer Postgres in Docker so ATTACH is unnecessary.
- `load_execution_config(conn, execution_id) -> dict` — reads `config_used` from `consumer_comp_admin_db.app_workflows_exec_log`; raises if missing.
- `load_dataset_locations(conn, dataset_code: str) -> { "http": {"path": ...}, "local": {"local_env_var_name": ...} }` — looks up `datasets` then `datasets_location`; requires both types.

The reader uses only `sqlalchemy.create_engine` and `text(...)`. No ORM models, no FastAPI imports.

### Download helper contract

- `download_url_to_path(url: str, dest: Path) -> Path` — creates parent dirs, streams HTTP GET to a temp file in the same directory, then replaces `dest`. Raises on non-2xx. Uses stdlib `urllib.request` (no extra Airflow image deps for MVP).

### DAG tasks (MVP)

1. `resolve_and_download` — conf → reader → download (one task is enough for D54).
2. Inline comments / stub callables `_notify_started` / `_notify_finished` marked `# TODO story #59` that do nothing.

`schedule=None`, `catchup=False`, paused at creation (compose default). Manual / API-triggered runs only.

## Seed (migration `0008`)

Fixed id: `uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0018/download_cfpb_all")` written as a literal string in the migration.

| Column | Value |
|---|---|
| workflow_name | `download_cfpb_all` |
| engine_type | `apache_airflow` |
| engine_workflow_id | `download_cfpb_all` |
| config | `{"dataset_code": "CFPB"}` |
| enabled | true |

Downgrade deletes that id only. No change to catalog seed (#86): all four MIOs already point at the http location; this workflow downloads the All file for the dataset, not a MIO-specific slice (time-window filtering is a later story).

## Local Docker notes

1. Upsert `CCA_DB_URL` (Postgres preferred) and `LOCAL_DATA_PATH_CFPB` via #77 after setting them in the app `.env`.
2. Mount a host directory into Airflow workers at the same path `LOCAL_DATA_PATH_CFPB` names (document in compose header comment; exact volume line is an implementation detail of the plan if a default local path is added).
3. Manual check (not CI): wait ≥10s after adding the DAG file, `airflow dags list` shows `download_cfpb_all`, trigger with a real `execution_id`, confirm `complaints.csv.zip` on disk.

## Tests

| Test | Asserts |
|---|---|
| Unit: `ccaa.download` | Mocked HTTP → file bytes at dest; non-2xx raises |
| Unit: `ccaa.db_reader` | In-memory / temp SQLite with minimal tables, or mocked connection returning rows for config + locations |
| Path: DAG file | `Middleware/Airflow-dags/download_cfpb_all.py` exists; file text contains `dag_id="download_cfpb_all"` (or equivalent) |
| Schema: `0008` | After upgrade, `app_workflows` has the seed row; downgrade removes it |
| Manual | Live Airflow discovery + one download (documented; not CI) |

Tests live under `Middleware/ConsumerComplaintsHandsOn/tests/` and put `Middleware/Airflow-dags` on `sys.path` when importing `ccaa.*` (same REPO_ROOT pattern as `test_airflow_dags_folder.py`).

## Out of scope

- Full status callback client (#59).
- Start-workflow API (#42) and engine interface (#83).
- 3-month filter (#58) or any MIO time window.
- Linking a workflow to a MIO in the catalog.
- Custom Airflow image / extra pip packages beyond stdlib + SQLAlchemy already in the image.
- Writing to the operational DB from Airflow (D11 / D51: read only).
