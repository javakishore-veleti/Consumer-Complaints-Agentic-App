# M02-0010 (#45) Read MIO status endpoint

Decisions: D5, D6, D26, D29, D37, D45, D46, D49, D50, D54, D57, D58, D59, D60 and D61 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D61); review and reverse if needed.

## Goal

One call returns every MIO with the status of its latest ingest and that ingest's executions — what the admin portal accordions show (#64). The portal is the only caller. No migration; the catalog and both logs already exist (#86, #87). The status callback (#43, D60) writes the rows this endpoint reads.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | `GET /mios` returning status-shaped rows | Collides with a future catalog CRUD list of MIOs |
| B (chosen) | `GET /mios/status` returning one entry per MIO with nested `latest_ingest` and its `executions` | Clear purpose; one round-trip for the portal; leaves `/mios` free for CRUD later |
| C | Separate list-MIOs and get-ingest endpoints | Extra round-trips for every accordion refresh; rejects D54 |

## Naming

| What | Name |
|---|---|
| Endpoint | `GET /mios/status` (router prefix `/mios`, tag `mios`) |
| API class (singleton, D29) | `MioStatusApi` in `app/api/routers/mio_status_api.py`, method `list_status` |
| API models | `app/api/models/mio_status_models.py`: `MioStatusListReq` (optional query `mio_id`, the one request object, D37), `MioStatusIngestOut`, `MioStatusOut`; reuse `AppWfExecLogOut` from `wf_exec_callback_models.py` |
| Facade (D6) | `MioStatusFacade.read(ctx)`, task interface `MioStatusFacadeTask`, one task `MioStatusCallServiceTask`, impl `MioStatusFacadeImpl` |
| Service | `MioStatusService.read(ctx)`, impl `MioStatusServiceImpl` |
| DTOs | `app/core/common/dtos/mio_status_dtos.py`: `MioStatusEntry`, `MioStatusIngest`, `MioStatusReq`, `MioStatusResp`, `MioStatusCtx`; `mio_status_facade_dtos.py`: `MioStatusFacadeCtx` (reuses the service's Req and Resp, carries the service ctx as `status_ctx`) |
| Factory methods (D26) | `ServicesObjectsFactory.get_mio_status_service()`, `FacadesObjectsFactory.get_mio_status_facade()`, `ApiObjectsFactory.get_mio_status_api()` |

No `init()` yet (D45 is after the MVP, D54): the new classes are lazy singletons handed out by their package's factory, and the facade builds its task list in its constructor like the status-callback facade.

## Request

| Field | Where | Rules |
|---|---|---|
| (none) | — | Return every MIO, ordered by name (`MioDao.list`) |
| `mio_id` | query string | Optional. When given (non-blank after trim), return that one MIO or 404. Blank or whitespace-only is 422. No other filters. No pagination. No path for a single MIO (`GET /mios/{id}/status` is out of scope). |

No body. No `X-Callback-Secret`: the portal calls this from a browser, which cannot keep a shared secret (D59). `ApiObjectsFactory` includes the router **without** the callback-secret dependency.

## Response

200 with a JSON **list** (same shape as `GET /data-ingest-logs`), one object per MIO:

```json
[
  {
    "id": "...",
    "name": "Customer complaints 3 months 2026",
    "description": "...",
    "latest_ingest": {
      "id": "...",
      "mio_id": "...",
      "status": "started",
      "message": null,
      "rows_loaded": 1500,
      "batch_count": 3,
      "increment_marker": "m",
      "requested_at": "...",
      "started_at": "...",
      "finished_at": null,
      "executions": [
        {
          "id": "...",
          "workflow_id": "...",
          "workflow_name": "...",
          "engine_type": "apache_airflow",
          "engine_workflow_id": "...",
          "engine_run_id": "...",
          "status": "started",
          "message": null,
          "mios_ingest_log_id": "...",
          "requested_at": "...",
          "started_at": "...",
          "finished_at": null
        }
      ]
    }
  }
]
```

- MIOs are ordered by name (the DAO's order).
- `latest_ingest` is the newest `mios_ingest_log` row for that MIO (`list` with `mio_id` and `limit=1`, newest first, D58), or `null` when the MIO has never been ingested.
- `executions` is every `app_workflows_exec_log` row of that latest ingest (`list` filtered by `mios_ingest_log_id`, newest first). Empty when the ingest has no executions yet. `config_used` is not returned (same as the callback's `AppWfExecLogOut`).
- An empty MIO catalog is `[]`.
- With `?mio_id=` of an existing MIO that has no ingest: a one-element list with `latest_ingest: null`.

## Errors

| Status | When | Body |
|---|---|---|
| 404 | `mio_id` given and no such MIO | `{"detail": "mio not found"}` |
| 422 | blank / whitespace-only `mio_id`, or any other INVALID_INPUT from the service | `{"detail": "invalid request"}` |
| 500 | anything else (a DAO failure) | `{"detail": "request failed"}` |

No 401 from this router. No 409 (read-only).

## How the service builds the list

`MioStatusService.read` (no write transaction; each DAO call commits on its own, D39's "with no transaction"):

1. If `req.mio_id` is a non-empty string after trim: `MioDao.get` by id. NOT_FOUND and INVALID_INPUT pass through. Otherwise the MIO list is that one record.
2. Else: `MioDao.list` (every MIO by name). Any non-SUCCESS passes through.
3. For each MIO: `MioIngestLogDao.list(mio_id=..., limit=1)`. Empty → `latest_ingest=null`. Non-SUCCESS → FAILURE for the whole call.
4. When there is a latest ingest: `AppWfExecLogDao.list(mios_ingest_log_id=...)`. Non-SUCCESS → FAILURE. Put the records on the ingest entry as `executions`.
5. `resp.entries` holds the built list; `resp.code` is SUCCESS.

A MIO deleted from the catalog but still named by an old ingest row never appears here: the list starts from `mios`, not from the ingest log (D58: the ingest log survives the MIO).

## Layers

`MioStatusApi.list_status` builds a `MioStatusFacadeCtx` from the one request object, calls the facade, maps `ctx.resp.code` to HTTP, and turns each `MioStatusEntry` into `MioStatusOut` (reusing `AppWfExecLogOut` for executions). The facade's only task builds the service ctx from `ctx.req`, calls the service through `ServicesObjectsFactory`, and puts the service's resp on the facade ctx. The service talks to the three DAOs through `DaoObjectsFactory`. Every method takes one ctx (D5, D37); the api package imports only common and facade interfaces (import-linter, 7 contracts).

`ApiObjectsFactory._build_app` includes the router with **no** secret dependency. `openapi.json` is regenerated (D32).

## Tests

- `tests/test_mio_status_service.py` (service and facade on a migrated SQLite database): every seeded MIO appears ordered by name with `latest_ingest=null` and no executions; one MIO with two ingests shows only the newest and its executions (newest first); a MIO with an ingest but no executions has `executions=[]`; optional `mio_id` returns one entry; unknown `mio_id` is NOT_FOUND; blank `mio_id` is INVALID_INPUT; the facade hands the read on.
- `tests/test_mio_status_api.py` (HTTP, real app): 200 list for the seed; a MIO with ingest and executions matches the nested shape; `?mio_id=` of a seeded MIO; 404 unknown id; 422 blank `mio_id`; no secret header needed (with and without `CCA_CALLBACK_SECRET` set); the path is in the OpenAPI document.
- `tests/test_singletons.py`: the new factory methods and classes are singletons.
- `tests/test_postgres.py`: the service flow on Postgres (D33).
- Unchanged and green: `tests/test_ctx_only_signatures.py`, `tests/test_import_contracts.py`, `tests/test_callback_secret_api.py` (portal routes stay open), `tests/test_openapi_spec.py` (after regenerating `openapi.json`).

## Out of scope

- Starting a workflow (#42), the status callback write path (#43, already built), the Angular accordions (#64).
- `GET /mios/{id}/status`, pagination, filter by status or name, historical ingest lists.
- Protecting portal endpoints with a user session or the callback secret.
- A shared read transaction across the three DAOs (accepted MVP gap: a concurrent callback can make the nested snapshot one step behind; the next poll heals it).
- Returning `config_used` or every historical ingest of a MIO.
