# M02-0033 (#83) Workflow engine interface and lookup

Decisions: D5, D26, D37, D45, D52, D54, D55, D64 (no new facade package), D68 and **D73** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D73); review and reverse if needed. Next free after D72 (#65) is **D73**.

## Goal

Introduce a `WorkflowEngine` interface in `services/` for starting a workflow run in its engine, with one implementation per engine type. The Airflow implementation wraps the existing #60 `AirflowStartDagService` (af_start capability). The services factory registers engines as singletons and returns them in a fixed order (D45 `get_all`); the caller picks the engine whose `engine_type` matches. An unknown engine type returns `INVALID_INPUT`. No engine-specific code in the API or the start-workflow facade tasks. Keep `POST /workflows/{id}/start` and the portal working.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | `WorkflowEngine` in services; Airflow impl delegates to `AirflowStartDagService`; `StartWfTriggerEngineTask` looks up via `get_workflow_engines()`; `StartWfService` validates against registered types | Meets acceptance; correct layering (no facade→Airflow hardcode); first real `get_all` consumer |
| B | Keep calling `AirflowStartDagFacade` from start_wf; add unused `WorkflowEngine` | Acceptance half-met; engine code stays in the facade |
| C | Put engines under facades / wrap `af_start` facade from services | Services calling facades reverses the closed-layer direction |

## Naming

| What | Name |
|---|---|
| Interface | `WorkflowEngine` in `app/core/services/workflow_engine.py` |
| Airflow impl | `ApacheAirflowWorkflowEngineImpl` in `services/impl/apache_airflow_workflow_engine_impl.py` |
| DTOs | `workflow_engine_dtos.py`: `WorkflowEngineReq` / `Resp` / `Ctx` |
| Factory | `ServicesObjectsFactory.get_workflow_engines() -> list[WorkflowEngine]` via `bean_registry.get_all(WorkflowEngine)` |
| Property | `engine_type: str` — `EngineType.APACHE_AIRFLOW.value` for the Airflow impl (D52/D55) |

No new facade package (D64 does not apply). The existing `af_start` facade remains registered for direct callers/tests; start-workflow no longer calls it.

## Behaviour

1. **`WorkflowEngine.start(ctx)`** — one ctx in, integer out. Req carries `execution_id` only. Resp may carry `engine_run_id` and `code`. Airflow impl maps to `AirflowStartDagCtx` and calls `AirflowStartDagService.start`.
2. **Registration** — `ServicesObjectsFactory.init()` registers `ApacheAirflowWorkflowEngineImpl()` under `WorkflowEngine` after `AirflowStartDagService` (so the engine can resolve the service). Order of registration is the fixed order of `get_workflow_engines()`.
3. **Lookup** — caller iterates `get_workflow_engines()` and picks `e.engine_type == wanted`. No match → `INVALID_INPUT`. Factory methods stay argument-free (D25); lookup is not a factory method.
4. **Start-workflow wiring**
   - `StartWfServiceImpl`: refuse when `engine_type` is not among registered engines (replaces the hardcoded `== apache_airflow` check). Still requires `enabled`.
   - `StartWfResp.engine_type`: set on success so the trigger task can look up without a second DAO read. Not exposed on the HTTP `StartWfOut` (still `execution_id` only).
   - `StartWfTriggerEngineTask`: look up by `ctx.resp.engine_type`, call `WorkflowEngine.start`; no import of Airflow facade/service.
5. **Unknown type** — both the prepare step (unregistered type on the workflow row) and the trigger step (type with no bean) return `INVALID_INPUT`.

## Codes

| Condition | Code |
|---|---|
| Engine started (delegates SUCCESS) | SUCCESS |
| Blank / missing `execution_id` on engine ctx | INVALID_INPUT (delegated) |
| No registered engine for the type | INVALID_INPUT |
| Engine start FAILURE / NOT_FOUND | same as #60 |

## Layering

```text
StartWfApi → StartWfFacade
  → StartWfCallServiceTask → StartWfService (validates against registered engines)
  → StartWfTriggerEngineTask → WorkflowEngine (lookup) → AirflowStartDagService (#60)
```

No API router or OpenAPI change. No new env vars. No migration.

## Out of scope

- AWS Step Functions implementation (M03 / D52)
- Moving or deleting `AirflowStartDagFacade` / `af_start`
- Changing portal or HTTP contract of start-workflow
- Polling / status callbacks

## Acceptance mapping

| Acceptance | Design |
|---|---|
| Interface and ctx; factory returns impls in fixed order | `WorkflowEngine` + DTOs; `get_workflow_engines()` / `get_all` |
| Unknown engine type → INVALID_INPUT | Lookup miss; StartWfService registered-type check |
| Singletons in services `objects_factory` (D26) | `register(WorkflowEngine, ApacheAirflowWorkflowEngineImpl())` in `init()` |
