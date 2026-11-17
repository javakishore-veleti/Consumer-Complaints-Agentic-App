# M15-0001 (#242) Design: DAG config via Middleware API

## Decision

Airflow DAGs must not open ops Postgres (`CCA_DB_URL`) for catalog / execution config. Middleware exposes a callback-secret GET that returns what `db_reader` used to load.

Bulk data (CSV zips, Mongo complaint docs, vector stores) stays on file/Mongo/vector backends — not via this API.

## Endpoint

`GET /callbacks/workflow-executions/{execution_id}/dag-context`

- Auth: `X-Callback-Secret` (same as status callbacks)
- Optional query: `app_endpoint` — if set, resolve that AppEndpoint (from/to)
- Response:
  - `config_used`: object from `app_workflows_exec_log`
  - `dataset_locations`: map by location_type when `config_used.dataset_code` present (else null)
  - `app_endpoint`: resolved endpoint payload when `app_endpoint` query set (else null)

## DAG side

`ccaa/dag_context.py`: `fetch_dag_context(execution_id, *, app_endpoint=None)` using `CCA_API_URL` + secret (reuse resolve helpers from `status_callback.py`).

Wire: `filter_cfpb_3_months`, `download_cfpb_all`, `ingest_cfpb_all`, `index_cfpb_*` — remove `make_engine` / `CCA_DB_URL` for these lookups.

## Out of scope this story

- Streaming huge datasets through Middleware
- Removing `CCA_DB_URL` Variable entirely (may remain unused until Sync list cleaned)
