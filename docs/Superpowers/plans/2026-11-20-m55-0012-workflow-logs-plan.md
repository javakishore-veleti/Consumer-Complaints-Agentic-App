# M55-0012 Workflow Logs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement this plan task-by-task.

**Goal:** Admin **Workflow Logs** (rename Ingestion Logs) listing `app_workflows_exec_log` for DataSets Import + DB Ingest, keep zone partition pages under the new nav, optional `engine_run_id` visible.

**Architecture:** Extend exec-log DAO list filters; add `GET /workflow-logs` Admin API with category prefixes; rename Angular nav/routes; new Import/DB Ingest chronicle pages; zone pages keep `/ingestion-logs` API, new `/workflow-logs/{zone}` routes.

**Tech stack:** FastAPI + SQLAlchemy/Mongo DAOs, Angular 22 admin, pytest + Karma/Jasmine.

**Spec:** `docs/Superpowers/specs/2026-11-20-m55-0012-workflow-logs-design.md`

---

### Task 1: DAO list filters for workflow_name_prefix + date range

**Files:**
- Modify: `Middleware/ConsumerComplaintsHandsOn/app/core/common/dtos/app_wf_exec_log_dtos.py`
- Modify: `Middleware/ConsumerComplaintsHandsOn/app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`
- Modify: `Middleware/ConsumerComplaintsHandsOn/app/core/dao/impl/mongo/mongo_app_wf_exec_log_dao.py` (if present)
- Test: `Middleware/ConsumerComplaintsHandsOn/tests/test_app_wf_exec_log_dao.py` (or create)

**Steps:**
1. Add failing tests: list by `workflow_name_prefix`, `requested_after`/`requested_before`, `engine_run_id`, cap default.
2. Add fields on `AppWfExecLogReq`; implement SQLAlchemy (and Mongo) `startswith` / date filters.
3. `uv run pytest` green; commit `M55-0012 #394: exec-log list filters for workflow logs`.

---

### Task 2: GET /workflow-logs API + category map

**Files:**
- Create: `…/app/core/common/workflow_log_categories.py` (prefix lists)
- Create: `…/app/api/routers/workflow_logs_api.py`, `…/app/api/models/workflow_logs_models.py`
- Modify: `…/app/main.py` (register router)
- Test: `…/tests/test_workflow_logs_api.py`

**Steps:**
1. Failing API tests: category=import|db_ingest returns filtered rows; limit max 30; status/engine_run_id filters.
2. Implement router → facade or thin service calling exec-log DAO; map UI status display optional in response.
3. OpenAPI sync if required by tests; commit.

---

### Task 3: Admin nav rename + routes

**Files:**
- Modify: `Portals/.../app-sidebar.component.ts`, `app.routes.ts`, `app.spec.ts`
- Rename/move pages: `pages/ingestion-logs/` → `pages/workflow-logs/` (or keep files, change labels/paths)
- Create: Import + DB Ingest chronicle components + `core/workflow-logs.ts` HTTP helper

**Steps:**
1. Failing portal tests for `top-nav-workflow-logs` and subnav Import/DB Ingest.
2. Implement nav + routes `/workflow-logs/import`, `/workflow-logs/db-ingest`, `/workflow-logs/:zone`.
3. Zone page title **Workflow Logs — {zone}**; Import/DB pages list exec API.
4. `npm run local:portal:admin:test -- --watch=false`; commit.

---

### Task 4: Verify start paths write exec log (smoke)

**Files:** tests only if gap found; otherwise document in story.

**Steps:**
1. Grep start-workflow facade; assert Import + DB Ingest + hydrate create exec log with engine fields.
2. Add regression test only if a path skips create.
3. Commit if code changed.

---

### Task 5: Verify + finish

1. `npm run local:api:lint` + `npm run local:api:test`
2. Portal tests; openapi if touched
3. PR + `/ccaa-story-complete 394`

---

## Category prefix constants (lock)

```python
WORKFLOW_LOG_CATEGORIES = {
  "import": ("download_cfpb", "filter_cfpb", "ingest_cfpb_imports"),
  "db_ingest": ("ingest_cfpb_all",),  # exact or startswith ingest_cfpb_ excluding imports
  "raw": ("hydrate_raw",),
  "refined": ("hydrate_refined",),
  "curated": ("hydrate_curated",),
  "taxonomy": ("hydrate_taxonomy",),
  "chroma": ("hydrate_chroma", "index_cfpb_chroma"),
}
```

For `db_ingest`: match `workflow_name.startswith("ingest_cfpb")` and not `startswith("ingest_cfpb_imports")`.
