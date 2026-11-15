# M02-0021 (#60) Airflow engine: start a DAG run asynchronously

Decisions: D5, D6, D12, D24, D26, D28 (refined by D64), D37, D42 (JWT client pattern), D54, D56 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Packaging for the new facade follows **D64** (`impl/af_start/`) claimed by story #57 — do not invent D65. No new DESIGN.md decision on this branch (next free after #57's D63/D64 is D65; unused). Decided without the user present (D54 MVP); review and reverse if needed.

## Goal

Start an Airflow DAG run through Airflow 3.4's REST API and return as soon as Airflow accepts the run (do not wait for tasks). Persist Airflow's `dag_run_id` on the execution row's `engine_run_id`. Called later from the start-workflow flow (#42); later wrapped behind the workflow engine interface (#83). **This story adds no public HTTP endpoint.**

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Facade (D64 `af_start`) → service → private `httpx` DAG-runs client (JWT like #77) + `AppWfExecLogDao` | Matches layering; mockable at HTTP; #42 calls one facade method; #83 can wrap the same service |
| B | Service only, no facade | #42 would reach into services; skips the closed api→facades habit even for internal callers |
| C | Build the engine interface (#83) now | Extra story scope; D54 says refactor after MVP |

## Naming

| What | Name |
|---|---|
| Facade | `AirflowStartDagFacade` / `AirflowStartDagFacadeImpl` under `facades/impl/af_start/` |
| Task | `AirflowStartDagCallServiceTask` in `facades/impl/af_start/tasks/` |
| Task interface | `AirflowStartDagFacadeTask` in `facades/airflow_start_dag_facade_task.py` |
| Service | `AirflowStartDagService` / `AirflowStartDagServiceImpl` |
| HTTP helper (private to services) | `AirflowDagRunsClient` in `services/impl/airflow_dag_runs_client.py` |
| DTOs | `airflow_start_dag_dtos.py` (service) and `airflow_start_dag_facade_dtos.py` |
| Factory methods | `ServicesObjectsFactory.get_airflow_start_dag_service()`, `FacadesObjectsFactory.get_airflow_start_dag_facade()` |

Settings reuse `CCA_AIRFLOW_API_*` / `airflow_api_*` from #77. No new env vars. No `init()` yet (D45 after MVP).

## Input / behaviour

Caller supplies **`execution_id`** only (the `app_workflows_exec_log.id` that #42 will have just created).

1. `AppWfExecLogDao.get` → NOT_FOUND if missing.
2. `dag_id` = the row's snapshot `engine_workflow_id` (D56). Empty/blank → INVALID_INPUT. Known MVP DAG id from #57: `download_cfpb_all` (not hardcoded here).
3. `AirflowDagRunsClient.trigger`: JWT `POST /auth/token`, then `POST /api/v2/dags/{dag_id}/dagRuns` with body:
   ```json
   {"logical_date": null, "conf": {"execution_id": "<execution_id>"}}
   ```
   `logical_date: null` is required by Airflow 3 (omit → 422). Response must include string `dag_run_id`. Timeouts match Variables client: `httpx.Timeout(5.0, read=30.0)`. Never log token or password.
4. `AppWfExecLogDao.update(id, engine_run_id=<dag_run_id>)` — **notes only; do not change status** (`requested` stays until callbacks #59 / #43). INVALID_INPUT if Airflow's id is longer than 128 characters (column max).
5. Return SUCCESS with `engine_run_id` on the resp. The HTTP round-trip ends when Airflow queues the run; the service does **not** poll task state (D12).

## Codes

| Condition | Code |
|---|---|
| Triggered and `engine_run_id` stored | SUCCESS |
| Blank / missing `execution_id` | INVALID_INPUT |
| Unknown execution | NOT_FOUND |
| Blank `engine_workflow_id` on the row | INVALID_INPUT |
| Airflow credentials blank, JWT/HTTP failure, bad JSON, missing `dag_run_id`, unreachable | FAILURE |
| DAO update fails after a successful trigger | FAILURE (orphan run accepted for MVP; #42 may retry carefully) |

Double-start creates a second Airflow run; preventing that is #42's job (one start per new execution row).

## Layering

```text
AirflowStartDagFacade (one task)
  → AirflowStartDagService.start
      → AppWfExecLogDao.get
      → AirflowDagRunsClient.trigger
      → AppWfExecLogDao.update(engine_run_id)
```

No API router, no OpenAPI change, no CallbackSecretAuth (machine-to-Airflow credentials are Settings, not the callback header).

## Out of scope

- Start-workflow HTTP endpoint (#42)
- Workflow engine interface / lookup (#83)
- Status callbacks from the DAG (#59)
- Creating the execution or ingest rows
- Waiting for DAG completion
- New DESIGN.md decision (D65+)

## Tests (summary)

- Client: happy path returns `dag_run_id`; token/HTTP failures → FAILURE; assert POST path and JSON body (`logical_date` null, `conf.execution_id`).
- Service: stores run id on the row; NOT_FOUND / INVALID_INPUT / FAILURE paths; status remains `requested`.
- Facade + factories: one task; singletons typed as interfaces.
