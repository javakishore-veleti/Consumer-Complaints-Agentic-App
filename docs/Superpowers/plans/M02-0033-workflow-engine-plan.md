# M02-0033 Workflow engine interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `WorkflowEngine` + Airflow impl + factory `get_all` lookup; route start-workflow through it without breaking the portal.

**Architecture:** `WorkflowEngine` (services) with `engine_type` and `start(ctx)`; `ApacheAirflowWorkflowEngineImpl` delegates to `AirflowStartDagService` (#60). `ServicesObjectsFactory` registers engines under `WorkflowEngine` and exposes `get_workflow_engines()`. `StartWfService` validates against registered types; `StartWfTriggerEngineTask` looks up and starts — no Airflow imports in the facade.

**Tech Stack:** Python, existing BeanRegistry (D45), pytest, httpx mocks for Airflow.

## Global Constraints

- Ctx-only (D37); singletons + `init()` / BeanRegistry (D26/D45); engine codes from `EngineType` (D52/D55).
- No new facade package (D64 unused here). Do not break `POST /workflows/{id}/start`.
- Spec: `docs/Superpowers/specs/M02-0033-workflow-engine-design.md`. Claim **D73**.
- `/ccaa-commit-push 83` after each task. Author `javakishore-veleti`; strip AI trailers.

## File map

| Path | Role |
|---|---|
| `app/core/common/dtos/workflow_engine_dtos.py` | Req / Resp / Ctx |
| `app/core/services/workflow_engine.py` | Interface |
| `app/core/services/impl/apache_airflow_workflow_engine_impl.py` | Airflow impl |
| `app/core/services/objects_factory.py` | register + `get_workflow_engines` |
| `app/core/common/dtos/start_wf_dtos.py` | add `engine_type` on resp |
| `app/core/services/impl/start_wf_service_impl.py` | validate vs registered engines |
| `app/core/facades/impl/start_wf/tasks/start_wf_call_service_task.py` | copy `engine_type` |
| `app/core/facades/impl/start_wf/tasks/start_wf_trigger_engine_task.py` | lookup + start |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D73 + open-question close |
| `tests/test_workflow_engine.py` | engine + lookup tests |
| `tests/test_start_wf_service.py` / `test_singletons.py` | wire-through updates |

---

### Task 1: WorkflowEngine interface, Airflow impl, factory registration

**Files:**
- Create: DTOs, interface, Airflow impl, `tests/test_workflow_engine.py`
- Modify: `services/objects_factory.py`, `DESIGN.md` (D73), singletons test

- [ ] **Step 1: Write failing tests** in `tests/test_workflow_engine.py`:
  - `get_workflow_engines()` returns a non-empty list; first engine `engine_type == "apache_airflow"`; same list order on repeat.
  - Airflow engine `start` with mocked `AirflowStartDagService` / client stores `engine_run_id` (reuse httpx mock pattern from `test_start_wf_service.py`).
  - Looking up a type with no bean yields `INVALID_INPUT` (helper or inline loop).
  - Each engine instance is a singleton via factory list identity.

- [ ] **Step 2: Run tests — expect fail** (`npm run local:api:test -- -- tests/test_workflow_engine.py` or project equivalent).

- [ ] **Step 3: Implement** interface, DTOs, `ApacheAirflowWorkflowEngineImpl`, register in `init()` after `AirflowStartDagService`, add `get_workflow_engines()`, add D73 to DESIGN.md, update `test_singletons.py`.

- [ ] **Step 4: Run tests — expect pass**. Lint.

- [ ] **Step 5: Commit** `M02-0033 #83: add WorkflowEngine and Airflow impl (D73)`.

---

### Task 2: Route start-workflow through engine lookup

**Files:**
- Modify: `start_wf_dtos.py`, `start_wf_service_impl.py`, call + trigger tasks, `test_start_wf_service.py`

- [ ] **Step 1: Extend failing expectations** — `test_non_airflow_engine_is_invalid` still INVALID_INPUT; facade happy path still stores `engine_run_id`; assert trigger task does not import Airflow facade (optional import-linter / source check); `engine_type` on resp after prepare.

- [ ] **Step 2: Implement** registered-type check; copy `engine_type`; rewrite `StartWfTriggerEngineTask` to lookup + `WorkflowEngine.start`.

- [ ] **Step 3: Lint + full `npm run local:api:test`**.

- [ ] **Step 4: Commit** `M02-0033 #83: route start-workflow through WorkflowEngine lookup`.

---

### Task 3: Docs, milestone, verify, PR

- [ ] Milestone log through finishing; verification; open PR closing #83; do not merge.

---

## Self-review

1. Spec coverage: interface, ctx, fixed-order factory list, INVALID_INPUT, singletons — Tasks 1–2.
2. Out of scope left out: Step Functions, deleting af_start, portal/OpenAPI changes.
