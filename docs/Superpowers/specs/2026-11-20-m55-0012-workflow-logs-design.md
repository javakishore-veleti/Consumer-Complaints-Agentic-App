# M55-0012 Workflow Logs — design

**Story:** #394 · **Date:** 2026-11-20

## Problem

Admin **Ingestion Logs** only covers lakehouse zone partition queues (`ingest_log_*`). Operators also need a reverse chronicle of every UI → Middleware → (optional Airflow) workflow click for **DataSets Import**, **DB Ingest**, and lakehouse hydrates — with **started / completed / failed** and an optional external engine run id.

## Decision (approved via manager “carry on / don’t wait”)

### Canonical wf_log

- Product name **wf_log** = existing table `app_workflows_exec_log` (do **not** rename the physical table — breaking).
- Already has: `status` (`requested` → `started` → `completed` | `failed` per D30), `engine_run_id` (optional Airflow dag run id / external engine id), `engine_type`, `engine_workflow_id`, timestamps.
- UI maps status for display: `requested`/`started` → **started**; `completed` → **completed**; `failed` → **failed**.

### Zone partition queues (unchanged tables)

- Keep `ingest_log_{raw,refined,curated,taxonomy,chroma}` as **partition claim queues** (pending → in_progress → done|failed). Not renamed to `wf_log_*` (wrong semantics).
- Still linked via optional `workflow_execution_id` → exec log id.
- Remain listable under Workflow Logs → zone sub-items (same pages, renamed parent).

### Admin UI

- Rename left-nav **Ingestion Logs** → **Workflow Logs** (`testId`: `top-nav-workflow-logs`).
- Routes: `/workflow-logs/...` (redirect old `/ingestion-logs/...` if cheap).
- Subnav:
  1. **DataSets Import** → list `app_workflows_exec_log` filtered by Import workflow name prefixes
  2. **DB Ingest** → exec log filtered by DB-ingest workflow prefixes
  3. **Raw / Refined / Curated / Taxonomy / Chroma** → existing zone partition listing (paths `/workflow-logs/{zone}`)

### Category → workflow name filters

| Nav item | `workflow_name` / `engine_workflow_id` prefix (LIKE / startswith) |
|----------|-------------------------------------------------------------------|
| DataSets Import | `download_cfpb`, `filter_cfpb`, `ingest_cfpb_imports` |
| DB Ingest | `ingest_cfpb` (exclude `ingest_cfpb_imports*`) |
| Raw | (zone page) partition queue `ingest_log_raw`; optional exec filter `hydrate_raw` |
| Refined | zone + `hydrate_refined` |
| Curated | zone + `hydrate_curated` |
| Taxonomy | zone + `hydrate_taxonomy` |
| Chroma | zone + `hydrate_chroma` / `index_cfpb_chroma` |

Exact prefix lists live in one shared constant (API + portal) so filters stay aligned.

### API

- New Admin-open list: `GET /workflow-logs` (or `/workflows/executions`) over `app_workflows_exec_log`.
- Query: `category` (import | db_ingest | raw | refined | curated | taxonomy | chroma) **or** raw filters: `status`, `engine_run_id`, `workflow_id`, `workflow_name_prefix`, date range on `requested_at`, `limit`≤30 (default 30), `offset`.
- Reverse chronicle by `requested_at` desc.
- Reuse DAO `list`; extend Req with `workflow_name_prefix` / `requested_after` / `requested_before` if missing.
- Zone partition CRUD stays under `/ingestion-logs/{zone}` **or** alias `/workflow-logs/partitions/{zone}` (prefer keep existing paths + UI route rename only for nav).

### Write path (no behavior change required if already correct)

- Workflow start facade already inserts exec log (`requested`/`started`).
- Airflow callbacks already set `started`/`completed`/`failed` + `engine_run_id`.
- Story verifies Import + DB Ingest + Lakehouse starts still produce rows; fill gaps only if a start path skips the exec log.

## Approaches considered

1. **Recommended:** UI + list API over existing `app_workflows_exec_log`; rename nav; keep zone tables. Low risk, matches D30/D50.
2. New physical `wf_log` table duplicating exec log — rejected (two sources of truth).
3. Rename `ingest_log_*` → `wf_log_*` and overload as both queue + chronicle — rejected (breaks claim semantics / status vocab).

## Acceptance

1. Nav shows **Workflow Logs** with Import, DB Ingest, and five zone children.
2. Import + DB Ingest pages list ≤30 newest exec rows with status + optional `engine_run_id`; filters work.
3. Zone pages still list partition queues under the new parent name/routes.
4. Middleware list API + DAO filters green; portal tests update nav labels; lint + pytest green.

## Out of scope

- Physical rename of `app_workflows_exec_log` or `ingest_log_*`.
- Vector Stores / App Endpoints workflow categories (can follow later with same API).
- Changing D30 status state machine.
