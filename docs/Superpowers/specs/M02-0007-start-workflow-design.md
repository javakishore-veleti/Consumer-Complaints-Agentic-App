# M02-0007 (#42) Start-workflow endpoint

Decisions: D5, D6, D12, D26, D29, D37, D43, D45, D46, D51, D54, D55, D56, D58, D59, D60, D64 and **D68** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D68); review and reverse if needed. D67 is status callbacks (#59); this story takes **D68**.

## Goal

One portal HTTP call starts any registered workflow: look up the workflow, create the execution row (and a new MIO ingest row when a MIO is given), trigger Airflow through the #60 `AirflowStartDagFacade` (`af_start`), and return the execution id without waiting for the DAG. Unknown / not-startable workflows return 422. No callback secret (D59).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | `POST /workflows/start` with `workflow_id` in the body | Works; path less discoverable next to `GET /workflows` |
| B (chosen) | `POST /workflows/{workflow_id}/start` with optional body | Matches D66 foreshadowing; clear REST shape; portal already has the id from the list |
| C | Call `AirflowStartDagService` from `StartWfService` only | Skips the #60 facade the story requires; harder to swap engines later behind the same facade call |

## Naming

| What | Name |
|---|---|
| Endpoint | `POST /workflows/{workflow_id}/start` (router prefix `/workflows`, tag `workflows`) |
| API class (singleton, D29) | `StartWfApi` in `app/api/routers/start_wf_api.py`, method `start` |
| API models | `app/api/models/start_wf_models.py`: `StartWfBody` (`mio_id`, `dataset_location_id` optional), `StartWfOut` (`execution_id`) |
| Facade (D6, D64) | `StartWfFacade.start(ctx)`; task interface `StartWfFacadeTask`; tasks `StartWfCallServiceTask` then `StartWfTriggerEngineTask`; impl `StartWfFacadeImpl` under `app/core/facades/impl/start_wf/` with tasks in `impl/start_wf/tasks/` |
| Service | `StartWfService.start(ctx)`, impl `StartWfServiceImpl` — creates ingest (optional) + exec log only |
| Engine trigger | Existing `AirflowStartDagFacade.start` (#60) from the second facade task |
| DTOs | `start_wf_dtos.py`: `StartWfReq`, `StartWfResp`, `StartWfCtx`; `start_wf_facade_dtos.py`: `StartWfFacadeCtx` |
| Factory methods (D26 / D45) | `ServicesObjectsFactory.get_start_wf_service()`, `FacadesObjectsFactory.get_start_wf_facade()`, `ApiObjectsFactory.get_start_wf_api()` |

`Wf` shortens Workflows (D55). Short package `start_wf` (D64's own example). Factories register via `init()` (D45 / #80).

## Request

| Field | Where | Rules |
|---|---|---|
| `workflow_id` | path | Required. Trimmed. Blank / whitespace-only → 422. Must exist, be `enabled`, and have `engine_type=apache_airflow` (M02 only, D52); otherwise 422. |
| `mio_id` | JSON body, optional | When given (non-blank after trim): create a **new** `mios_ingest_log` row (`requested`) and link the new exec log to it (D50, D58, D60 rerun rule). Unknown MIO → 422. Blank string → 422. Omit or `null` → no ingest row (allowed; D50). |
| `dataset_location_id` | JSON body, optional | When given (non-blank after trim): must exist in `datasets_location` or 422. Not stored on the exec log and **not** sent to Airflow (D51: the DAG reads the catalog). Omit or `null` → skip. Blank string → 422. |

Empty body `{}` is valid. No `X-Callback-Secret` (portal / browser, D59). `ApiObjectsFactory` includes the router **without** the callback-secret dependency (same as `WfListApi` / `MioStatusApi`).

## Response

**202 Accepted** (acceptance: returns accepted without waiting):

```json
{
  "execution_id": "…"
}
```

- The execution row is `requested`; `engine_run_id` is filled by #60 after Airflow accepts the run.
- The HTTP call returns as soon as Airflow accepts the DAG run (D12 / #60); it does not poll task state.

## Errors

| Status | When | Body |
|---|---|---|
| 422 | blank path id; unknown / disabled / non-`apache_airflow` workflow; blank optional fields; unknown `mio_id` or `dataset_location_id`; other `INVALID_INPUT` | `{"detail": "invalid request"}` |
| 502 | Airflow trigger fails after the exec row was created (`FAILURE` from #60) | `{"detail": "engine start failed"}` |
| 500 | anything else (DAO / unexpected) | `{"detail": "request failed"}` |

No 401 from this router. No 404 (unknown workflow is 422 per acceptance). Orphan exec rows after a 502 are accepted for MVP (same as #60's post-trigger DAO failure note); the portal can start again (new rows).

## How the service prepares the run

`StartWfService.start` (no Airflow call):

1. Trim `workflow_id`; blank → `INVALID_INPUT`.
2. `AppWfDao.get` by id. `NOT_FOUND` → treat as `INVALID_INPUT` (422). Disabled or `engine_type != apache_airflow` → `INVALID_INPUT`.
3. Optional `dataset_location_id`: trim; blank → `INVALID_INPUT`; `DatasetLocationDao.get`; non-SUCCESS → `INVALID_INPUT` (unknown location).
4. Optional `mio_id`: trim; blank → `INVALID_INPUT`; `MioIngestLogDao.create(mio_id=…)`; non-SUCCESS → that code (`NOT_FOUND` → mapped to `INVALID_INPUT` for HTTP 422).
5. `AppWfExecLogDao.create(workflow_id=…, mios_ingest_log_id=… or None)` (D56 snapshot + D58 link).
6. `resp.execution_id` = new row id; `resp.code` = SUCCESS.

## Facade tasks (D6, D64)

```text
StartWfCallServiceTask
  → StartWfService.start  (ingest + exec log)
StartWfTriggerEngineTask
  → AirflowStartDagFacade.start(execution_id)  (#60 / af_start)
```

On non-SUCCESS the facade stops (D24). Task 2 runs only after an `execution_id` exists. Task 2 failures leave the DB rows as created (MVP).

## Layers

`StartWfApi.start` builds `StartWfFacadeCtx` from path + body, calls the facade, maps `ctx.resp.code` to HTTP, returns `StartWfOut`. The api package imports only common and facade interfaces (import-linter). Every method takes one ctx (D5, D37).

Facade layout (D64):

```text
app/core/facades/start_wf_facade.py
app/core/facades/start_wf_facade_task.py
app/core/facades/impl/start_wf/start_wf_facade_impl.py
app/core/facades/impl/start_wf/tasks/start_wf_call_service_task.py
app/core/facades/impl/start_wf/tasks/start_wf_trigger_engine_task.py
```

Do **not** put these tasks in the flat `impl/tasks/` folder. Do not refactor existing facades.

`openapi.json` is regenerated (D32).

## Tests

- `tests/test_start_wf_service.py`: creates exec without MIO; with MIO creates ingest + link; unknown / disabled / non-airflow workflow → INVALID_INPUT; blank optional ids → INVALID_INPUT; unknown location → INVALID_INPUT; facade happy path with mocked Airflow transport stores `engine_run_id`.
- `tests/test_start_wf_api.py`: 202 with `execution_id`; 422 unknown workflow; no secret required; path in OpenAPI; Airflow failure → 502 after row exists.
- `tests/test_singletons.py`: new factory methods and classes.
- `tests/test_postgres.py`: prepare+trigger flow on Postgres when `CCA_TEST_POSTGRES_URL` is set (mock Airflow HTTP).
- Unchanged green: import contracts, ctx-only signatures, callback-secret portal routes stay open, OpenAPI export.

## Out of scope

- Workflow engine interface / multi-engine dispatch (#83)
- Angular start button (#65)
- Waiting for DAG completion; status comes from #43 / #59
- Storing `dataset_location_id` on the exec log
- Passing `mio_id` in Airflow conf (D63: ignored for MVP; DAG uses `execution_id` only)
- Protecting portal endpoints with a user session
- Rolling back the exec/ingest row when Airflow fails (MVP accepts orphans)
