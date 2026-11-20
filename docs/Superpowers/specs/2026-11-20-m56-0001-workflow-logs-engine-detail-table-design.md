# M56-0001 Workflow Logs table UX — design

**Story:** #396 · **Date:** 2026-11-20

## Problem

Workflow Logs (Import / DB Ingest) hide which engine ran the job, bury completion time, lack row detail drill-down, and only show 30 rows without sort/search.

## Decision

### Data (already on `app_workflows_exec_log`)

| UI | Field |
|----|--------|
| Workflow | `workflow_name` |
| Workflow Engine | `engine_type` (+ display label) |
| Status | `display_status` / `status` |
| Engine run id | `engine_run_id` |
| Requested | `requested_at` |
| Started | `started_at` |
| Completed | `finished_at` |
| Message | `message` |

No new RDBMS columns. Expand `EngineType` enum + `ENGINE_TYPE_LABELS` map for: `apache_airflow`, `aws_step_functions`, `spring_batch`, `bpmn`, `spark_job`, `aws_emr`. Unknown codes still display as the raw code.

### API

- Raise list page max/default to **60** (`WORKFLOW_LOG_PAGE_SIZE_MAX = 60`).
- Add query `engine_type` on `GET /workflow-logs` (DAO already filters).
- Response already includes `engine_type`; add optional `engine_label` for convenience (or portal maps labels).

### Admin table UX (Import / DB Ingest pages)

1. Columns: Workflow | Workflow Engine | Status | Engine run id | Requested | Started | **Completed** | Message | **Actions** (eye).
2. Default load: newest 60 (`limit=60`, `requested_at` desc). Pagination: Prev/Next via `offset` (page size 60).
3. Sortable headers: click toggles asc/desc on loaded rows (client-side).
4. Per-column search inputs under headers: case-insensitive substring filter on loaded rows (client-side).
5. Eye icon opens modal/card with **all** fields (ids, engine code+label, engine_workflow_id, engine_run_id, statuses, timestamps, message) + **Close**.

Zone partition pages unchanged this story (optional shared page-size constant only if trivial).

## Acceptance

1. Engine column + filter; Completed column; detail modal; 60/page; sort; column search.
2. EngineType catalog expanded; lint + tests green.
