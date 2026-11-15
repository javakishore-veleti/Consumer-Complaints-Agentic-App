# M02-0008 (#43) Airflow status callback endpoint

Decisions: D5, D6, D11, D26, D29, D30, D37, D39, D45, D50, D51, D54, D58, D59 and D60 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D60); review and reverse if needed.

## Goal

A workflow engine (Airflow) reports a status of one execution by calling the API: `started`, `completed` or `failed`, with an optional engine run id and message. The API changes the execution log row and, when the execution belongs to a MIO ingest, that `mios_ingest_log` row, in one transaction. Airflow never writes the database (D11, D51). Duplicate, out-of-order and late calls are harmless (D30). The endpoint is the first real user of the callback secret (D59).

## Naming

| What | Name |
|---|---|
| Endpoint | `POST /callbacks/workflow-executions/{execution_id}/status` (router prefix `/callbacks`, tag `callbacks`) |
| API class (singleton, D29) | `WfExecCallbackApi` in `app/api/routers/wf_exec_callback_api.py`, method `report_status` |
| API models | `app/api/models/wf_exec_callback_models.py`: `WfExecStatusReport` (body), `WfExecStatusReportReq` (path id + body, the one request object, D37), `WfExecStatusOut`, `AppWfExecLogOut`, `MioIngestLogOut` |
| Facade (D6) | `WfExecStatusFacade.report(ctx)`, task interface `WfExecStatusFacadeTask`, one task `WfExecStatusCallServiceTask`, impl `WfExecStatusFacadeImpl` |
| Service (D39) | `WfExecStatusService.record(ctx)`, impl `WfExecStatusServiceImpl` |
| DTOs | `app/core/common/dtos/wf_exec_status_dtos.py`: `WfExecStatusReq`, `WfExecStatusResp`, `WfExecStatusCtx` (a `TransactionalCtx`); `wf_exec_status_facade_dtos.py`: `WfExecStatusFacadeCtx` (reuses the service's Req and Resp, carries the service ctx as `status_ctx`) |
| Factory methods (D26) | `ServicesObjectsFactory.get_wf_exec_status_service()`, `FacadesObjectsFactory.get_wf_exec_status_facade()`, `ApiObjectsFactory.get_wf_exec_callback_api()` |

`Wf` shortens `Workflows` in class names (D55). No `init()` yet (D45 is after the MVP, D54): the new classes are lazy singletons handed out by their package's factory, and the facade builds its task list in its constructor like the data ingest facade.

## Request

Path: `execution_id`, the `app_workflows_exec_log` id the API handed to the engine when it started the run (D51). Header: `X-Callback-Secret` (D59). Body (JSON):

| Field | Type | Goes to | Rules |
|---|---|---|---|
| `status` | `started`, `completed` or `failed` | execution, then the ingest rule | required; `requested` is refused: only the API creates a requested row |
| `engine_run_id` | string | execution | optional, up to 128 characters (the exec-log column) |
| `message` | string | execution; the ingest only when its status moves | optional |
| `rows_loaded` | integer | ingest | optional, 0 or more, a JSON integer (not a string, not a boolean) |
| `batch_count` | integer | ingest | optional, 0 or more, a JSON integer |
| `increment_marker` | string | ingest | optional, up to 255 characters |

Unknown fields are refused (422), so a typo in the DAG fails loudly instead of being dropped. The volume fields are ignored when the execution has no ingest row: a generic callback task can send them for every workflow. The values are what the engine knows now and overwrite what was there (they are not added up): a workflow split in parts sends the totals, or only its last task sends them.

## Response

200 with the rows after the call, so the engine and the tests see the result:

```json
{
  "execution": {"id": "...", "workflow_id": "...", "workflow_name": "...", "engine_type": "apache_airflow",
                "engine_workflow_id": "...", "engine_run_id": "...", "status": "started", "message": null,
                "mios_ingest_log_id": "...", "requested_at": "...", "started_at": "...", "finished_at": null},
  "ingest": {"id": "...", "mio_id": "...", "status": "started", "message": null, "rows_loaded": null,
             "batch_count": null, "increment_marker": null, "requested_at": "...", "started_at": "...",
             "finished_at": null}
}
```

`ingest` is `null` for an execution without an ingest row. `config_used` is not returned (the engine reads it from the database, D51).

## Errors

| Status | When | Body |
|---|---|---|
| 401 | missing or wrong `X-Callback-Secret`, or no secret configured (D59) | `{"detail": "missing or wrong callback secret"}` |
| 404 | no execution with that id | `{"detail": "workflow execution not found"}` |
| 409 | a move of the execution D30 does not allow (out of order, or after a final status); nothing changes | `{"detail": "status change not allowed in the current state"}` |
| 422 | the body fails FastAPI's checks (status, types, lengths, unknown field, malformed JSON) | FastAPI's validation body |
| 422 | the service refuses a value FastAPI does not check (a volume above its column maximum) | `{"detail": "invalid request"}` |
| 500 | anything else (database error, the ingest moved by a rival in the same instant); nothing changes and the call can be retried | `{"detail": "request failed"}` |

404 and 409 always describe the execution, never the ingest: the ingest never makes a callback fail with them. A malformed JSON body is refused with 422 before the secret check runs (FastAPI parses the body before the router's dependency); it never reaches the endpoint or the database, so D59's accepted exception stays as it is.

For #59 (the Airflow side): treat 2xx as done; 409 as done too (the execution has already moved past this status, retrying cannot help); 5xx and connection errors as retryable; 401, 404 and 422 as a bug that fails the task.

## The ingest rule

The service runs these steps in one transaction (D39), opened through the `TransactionDao` and put on every DAO ctx; the first step that does not return SUCCESS rolls everything back:

1. Before the transaction: the execution id is a non-blank string and the status is `started`, `completed` or `failed`, else INVALID_INPUT.
2. `AppWfExecLogDao.update(id, status, engine_run_id, message)`: the D30 move with its conditional `UPDATE` (story #82). NOT_FOUND, INVALID_INPUT and CONFLICT pass through unchanged.
3. If the execution has no `mios_ingest_log_id`, stop: commit. Otherwise read the ingest row (`MioIngestLogDao.get`). A missing row is FAILURE: the reference is checked on create and the ingest log has no delete (D58), so it would be a fault, and NOT_FOUND here would wrongly read as "execution not found".
4. Work out the ingest's target from the execution's status after step 2:
   - `started`: `started`.
   - `failed`: `failed`.
   - `completed`: `completed`, but only when every execution of the ingest (`AppWfExecLogDao.list(mios_ingest_log_id)`, which in the same transaction already sees this execution as completed) is `completed`; otherwise no target.
   - The target is used only when D30 allows the ingest to move there from where it is (`target in ExecStatus(ingest.status).next_statuses`); otherwise there is no target and the ingest's status stays as it is. So a `requested` ingest goes to `started` or `failed`, a `started` ingest goes to `completed` or `failed`, and a final ingest never moves.
5. `MioIngestLogDao.update(id, status=target or none, message=the callback's message only when there is a target, rows_loaded, batch_count, increment_marker)`. INVALID_INPUT (a volume field the DAO refuses) passes through; any other non-SUCCESS (a CONFLICT from a rival that moved the ingest between steps 3 and 5, or FAILURE) becomes FAILURE.

The message goes to the ingest only when the ingest moves, so the ingest's message explains its own status (the failure that made it fail), and a later message from another execution never overwrites it. Volume fields are notes and are written on every call that carries them, also on a final ingest (D58), so a late callback can still fill in the final volume.

## Duplicates, out-of-order and late calls (D30)

| Case | Execution | Ingest | Response |
|---|---|---|---|
| first `started` | requested to started | requested to started, message written | 200 |
| the same `started` again | status and times kept, notes written | rule runs again, no move | 200 |
| `started` of a second execution of the ingest | requested to started | stays started, message not written | 200 |
| `completed` while other executions of the ingest are not completed | started to completed | stays started, volume written | 200 |
| `completed` of the last execution not yet completed | started to completed | started to completed, message written | 200 |
| `failed` (from requested or started) | moves to failed | to failed when not final, message written | 200 |
| any legal move while the ingest is already final | moves | status and message kept, volume written | 200 |
| the same `completed` (or `failed`) again | unchanged | unchanged | 200, the same body |
| `completed` before `started` | unchanged | unchanged | 409 |
| `started` or `failed` after `completed`, `started` or `completed` after `failed` | unchanged | unchanged | 409 |
| an invalid volume (above the column maximum) | rolled back | rolled back | 422 |
| the ingest write fails | rolled back | rolled back | 500 |

The repeated call runs the ingest rule again. That keeps a retry harmless (the rule moves nothing a second time), and it heals one rare case: when the ingest was left `started` by the race below, any later call for one of its executions completes it.

A rerun after a failed execution cannot share the failed execution's ingest: the first failure makes the ingest `failed`, which is final (D30). A rerun therefore needs a new ingest row (the start-workflow story #42 creates it); the failed ingest stays as history. This narrows D50's "reruns after failures" for now; a "this execution replaces that one" link can lift it later. Parallel batches or parts of one ingest share it as D50 says.

## Concurrency

- Two calls for the same execution at once: the exec-log DAO's conditional `UPDATE` decides (the first to commit wins; the second gets 409, or 200 when it made the same move).
- Two calls for different executions of the same ingest on SQLite: SQLite lets one writer at a time, so the second transaction waits for the first to commit and then sees its result; the "every execution completed" check is exact.
- The same on Postgres (READ COMMITTED): when the last two executions of an ingest complete in the same instant, each transaction may still see the other as `started`, so neither completes the ingest; it stays `started` until any later call for one of its executions (a retry is enough). Accepted for the MVP; a row lock on the ingest (`SELECT ... FOR UPDATE` in a new DAO method) closes it later. A rival that moves the ingest between the read and the write is a CONFLICT from the ingest DAO, which the service turns into a 500 (retryable), never into the execution's 409.

## Layers

`WfExecCallbackApi.report_status` builds a `WfExecStatusFacadeCtx` from the one request object, calls the facade interface, maps `ctx.resp.code` to HTTP, and turns the two records into the response models. The facade's only task builds the service ctx from `ctx.req`, calls the service through `ServicesObjectsFactory`, and puts the service's resp on the facade ctx. The service holds the rule and the transaction; the two DAOs stay one per table (D7). Every method takes one ctx (D5, D37); the api package imports only common and facade interfaces (import-linter, 7 contracts).

`ApiObjectsFactory._build_app` includes the router with `dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())]` (D59). `openapi.json` is regenerated (D32); no OpenAPI security scheme is declared (D59 (5)).

## How Airflow calls it (for #59)

```bash
curl -sf -X POST "$CCA_API_URL/callbacks/workflow-executions/$EXECUTION_ID/status" \
  -H "X-Callback-Secret: $CCA_CALLBACK_SECRET" -H "Content-Type: application/json" \
  -d '{"status": "started", "engine_run_id": "'"$AIRFLOW_RUN_ID"'"}'
```

The DAG gets `EXECUTION_ID` from its run configuration (D51) and the secret from a masked Airflow Variable (#77, D42). From inside the Airflow containers the API is reached through the host (ARCHITECTURE section 8).

## Tests

- `tests/test_wf_exec_status_service.py` (service and facade on a migrated SQLite database): only `started`, `completed`, `failed` accepted; blank id; unknown execution; too long engine run id; an execution without an ingest (volume ignored, times set); a repeated report keeps the times; out of order is CONFLICT and changes neither row; started moves a requested ingest; a second execution starting leaves the ingest and its message alone; completed moves the ingest only when every execution is completed (volume written before that); failed moves the ingest with the message and leaves other executions alone; failed from requested; a final ingest is left alone while the execution moves and the volume is written; duplicates after the ingest completed change nothing; a late failed after completed is CONFLICT; an invalid volume rolls back the execution; a failing ingest write rolls back the execution; an ingest CONFLICT becomes FAILURE; the facade hands the report on.
- `tests/test_wf_exec_callback_api.py` (HTTP, real app): started then completed with an ingest; a null ingest; a duplicate call returns the same body; 409 out of order and after a final status; 404; 422 for `requested`, an unknown status, no status, a negative, string or boolean count, a too long run id or marker, an unknown field; 422 `invalid request` for a count above the column maximum; 401 without the right secret (nothing changes) and with no secret configured; malformed JSON is 422; the path is in the OpenAPI document.
- `tests/test_singletons.py`: the new factory methods and classes are singletons.
- `tests/test_postgres.py`: the service flow on Postgres (D33).
- Unchanged and green: `tests/test_ctx_only_signatures.py`, `tests/test_import_contracts.py`, `tests/test_callback_secret_api.py`, `tests/test_openapi_spec.py` (after regenerating `openapi.json`).

## Out of scope

- The Airflow side that calls the endpoint (#59) and the start endpoint that creates executions and ingest rows (#42).
- Reading the status for the portal (#45).
- A link between a rerun and the execution it replaces; a row lock for the Postgres race above.
- Moving the secret check ahead of body parsing; an OpenAPI security scheme.
- Adding volume across parts (the engine sends totals).
