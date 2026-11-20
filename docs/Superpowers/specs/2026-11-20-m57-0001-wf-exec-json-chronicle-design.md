# M57-0001 wf_engine_data_json + wf_exec_data_json — design

**Story:** #398 · **Date:** 2026-11-20

## Problem

Workflow Logs need a durable, append-only chronicle of high-level engine and Middleware events (not noisy task logs), shown in the Admin eye-modal with pagination.

## Decision

### Columns on `app_workflows_exec_log`

| Column | Writer | Shape |
|--------|--------|--------|
| `wf_engine_data_json` | Engine via POST status callback | `{"invocations":[...]}` |
| `wf_exec_data_json` | Middleware | `{"invocations":[...]}` |

Each invocation element:

```json
{
  "invoked_for": "started" | "completed" | "failed",
  "invoked_at": "ISO-8601 UTC",
  "invoked_configs": { },
  "invoked_info": { }
}
```

Omit null keys when writing an element (`invoked_configs` / `invoked_info` only if provided).

### Append rule (hard)

- **Do not append** to `wf_engine_data_json.invocations` when both optional inputs are null/absent (`invoked_configs` and `invoked_info` both null). Status / `engine_run_id` / `message` updates still apply.
- Append only when at least one of `invoked_configs` or `invoked_info` is a non-null object (may be `{}`).
- Cap list length soft (e.g. keep last 100) to avoid unbounded growth.

### API

- Existing **POST** `/callbacks/workflow-executions/{execution_id}/status` (already POST — no GET→POST change).
- Extend body with optional `invoked_configs: object | null`, `invoked_info: object | null`.
- `GET /workflow-logs` includes both JSON columns.
- Middleware on workflow start appends one high-level entry to `wf_exec_data_json` (workflow name, engine type, execution id).

### Admin UI

Eye modal: paginate `wf_engine_data_json.invocations` (e.g. 10/page, newest last or newest first — newest last = chronological append order). Also show `wf_exec_data_json` summary.

## Out of scope

Rewriting every DAG to always send chronicle payload (optional; Airflow helper accepts kwargs when callers pass them).
