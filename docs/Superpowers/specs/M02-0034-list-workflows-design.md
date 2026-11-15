# M02-0034 (#84) List workflows endpoint

Decisions: D5, D6, D26, D29, D37, D43, D45, D54, D55, D59, D64 and **D66** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D66); review and reverse if needed. D63–D65 belong to parallel stories (#57, #62); this story follows D64's layout and records D66 for the portal list.

## Goal

One call returns every registered workflow (`app_workflows`) so the admin portal can list them before starting a run (#42). The portal is the only caller. No migration; `AppWfDao` already exists (#81). Never return `config` or any secret.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | `GET /app-workflows` mirroring the table name | Verbose; clashes with future CRUD naming |
| B (chosen) | `GET /workflows` returning safe fields only | Matches section 4.2; short portal URL; leaves room for `POST /workflows/{id}/start` later |
| C | Skip the service and call `AppWfDao` from a facade task | Breaks the MioStatus pattern and puts list mapping in the facade |

## Naming

| What | Name |
|---|---|
| Endpoint | `GET /workflows` (router prefix `/workflows`, tag `workflows`) |
| API class (singleton, D29) | `WfListApi` in `app/api/routers/wf_list_api.py`, method `list` |
| API models | `app/api/models/wf_list_models.py`: `WfListReq` (empty query object, D37), `WfListOut` |
| Facade (D6, D64) | `WfListFacade.list(ctx)`, task interface `WfListFacadeTask`, one task `WfListCallServiceTask`, impl `WfListFacadeImpl` under `app/core/facades/impl/wf_list/` with tasks in `impl/wf_list/tasks/` |
| Service | `WfListService.list(ctx)`, impl `WfListServiceImpl` |
| DTOs | `app/core/common/dtos/wf_list_dtos.py`: `WfListEntry`, `WfListReq`, `WfListResp`, `WfListCtx`; `wf_list_facade_dtos.py`: `WfListFacadeCtx` (reuses service Req/Resp, carries `list_ctx`) |
| Factory methods (D26) | `ServicesObjectsFactory.get_wf_list_service()`, `FacadesObjectsFactory.get_wf_list_facade()`, `ApiObjectsFactory.get_wf_list_api()` |

`Wf` shortens `Workflows` (D55). Short package `wf_list` (D64). No `init()` yet (D45 after MVP, D54): lazy singletons via package factories; the facade builds its one-task list in its constructor like `MioStatusFacade`.

## Request

| Field | Where | Rules |
|---|---|---|
| (none) | — | Return every workflow, ordered by `workflow_name` (`AppWfDao.list` with an empty req) |

No body. No path id. No filters and no pagination (D54). No `X-Callback-Secret`: the portal calls this from a browser (D59). `ApiObjectsFactory` includes the router **without** the callback-secret dependency.

## Response

200 with a JSON **list**, one object per workflow:

```json
[
  {
    "id": "...",
    "workflow_name": "download_cfpb_all",
    "engine_type": "apache_airflow",
    "engine_workflow_id": "download_cfpb_all",
    "enabled": true
  }
]
```

- Ordered by `workflow_name` (the DAO's order).
- Includes disabled rows (`enabled: false`) so the portal can show or gray them out; filtering is a later concern.
- **`config` is never returned** (acceptance: no secret and no config value that could hold one).
- Times (`created_at`, `updated_at`) are omitted for MVP.
- An empty registry is `[]`.

## Errors

| Status | When | Body |
|---|---|---|
| 500 | anything non-SUCCESS (a DAO failure) | `{"detail": "request failed"}` |

No 401 from this router. No 404 or 422 (no filters). No 409 (read-only).

## How the service builds the list

`WfListService.list` (no write transaction; the DAO commits on its own):

1. `AppWfDao.list` with an empty `AppWfReq` through `DaoObjectsFactory.get_app_wf_dao()`.
2. Non-SUCCESS → put that code on `resp` and return it.
3. Map each `AppWfRecord` to `WfListEntry` with only `id`, `workflow_name`, `engine_type`, `engine_workflow_id`, `enabled` (drop `config` and times).
4. `resp.entries` holds the list; `resp.code` is SUCCESS.

## Layers

`WfListApi.list` builds a `WfListFacadeCtx` from the empty request object, calls the facade, maps `ctx.resp.code` to HTTP, and turns each `WfListEntry` into `WfListOut`. The facade's only task builds the service ctx from `ctx.req`, calls the service through `ServicesObjectsFactory`, and puts the service's resp on the facade ctx. The service talks only to `AppWfDao`. Every method takes one ctx (D5, D37); the api package imports only common and facade interfaces (import-linter, 7 contracts).

Facade layout (D64):

```text
app/core/facades/wf_list_facade.py
app/core/facades/wf_list_facade_task.py
app/core/facades/impl/wf_list/wf_list_facade_impl.py
app/core/facades/impl/wf_list/tasks/wf_list_call_service_task.py
```

Do **not** put this facade's task in the flat `impl/tasks/` folder. Existing facades stay where they are.

`ApiObjectsFactory._build_app` includes the router with **no** secret dependency. `openapi.json` is regenerated (D32).

## Tests

- `tests/test_wf_list_service.py` (service and facade on a migrated SQLite database): empty registry → `[]`; seeded workflows appear ordered by name with no `config` on the entry; disabled rows are included; the facade hands the list on.
- `tests/test_wf_list_api.py` (HTTP, real app): 200 list; response keys never include `config`; no secret header needed (with and without `CCA_CALLBACK_SECRET` set); the path is in the OpenAPI document.
- `tests/test_singletons.py`: the new factory methods and classes are singletons.
- `tests/test_postgres.py`: the service flow on Postgres (D33).
- Unchanged and green: `tests/test_ctx_only_signatures.py`, `tests/test_import_contracts.py`, `tests/test_callback_secret_api.py` (portal routes stay open), `tests/test_openapi_spec.py` (after regenerating `openapi.json`).

## Out of scope

- Starting a workflow (#42), the engine interface (#83), Angular list UI (#64 / portal stories).
- Filtering by `enabled` or `engine_type`, pagination, `GET /workflows/{id}`.
- Returning `config`, credentials, or times.
- Protecting portal endpoints with a user session or the callback secret.
- Moving existing facades into `impl/<short>/` packages (D64: new facades only).
