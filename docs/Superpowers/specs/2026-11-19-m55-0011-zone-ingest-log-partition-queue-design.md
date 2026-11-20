# M55-0011 Zone ingest_log partition queue — design

**Story:** #391 · **Date:** 2026-11-19

## Problem

Full curated (and later other zone) hydrates OOM under Docker ~8 GiB. In-job hash batching alone is not durable across Airflow/Spark retries. Work must be tracked in the **Middleware operational RDBMS** (Postgres locally; SQLite elsewhere), not in Iceberg.

## Decision (approved)

- **Not Iceberg-specific.** Five sibling tables, created by **Alembic on API startup** (same path as other admin tables; this repo’s equivalent of Liquibase):
  - `ingest_log_raw`
  - `ingest_log_refined`
  - `ingest_log_curated`
  - `ingest_log_taxonomy`
  - `ingest_log_chroma`
- Distinct from existing `mios_ingest_log` (MIO-level run status).

## Table shape (same columns on each)

| Column | Type / notes |
|--------|----------------|
| `id` | UUID PK |
| `partition_key` | string (bucket / yyyy-mm / batch id) |
| `data_tech` | `iceberg` \| `s3` \| `database` |
| `source_end_point_id` | soft ref → `app_endpoints.id` (no FK) |
| `dest_end_point_id` | soft ref → `app_endpoints.id` (no FK) |
| `workflow_execution_id` | optional soft ref → `app_workflows_exec_log.id` (filterable; no FK) |
| `status` | `pending` \| `in_progress` \| `done` \| `failed` |
| `status_on` | when current status was entered |
| `status_updated_on` | last touch |
| `configs_json` | JSON text (claim size, spark overrides, error detail, etc.) |

Unique constraint (per table): `(partition_key, source_end_point_id, dest_end_point_id)`.  
Indexes: `(status, status_updated_on)`, `(workflow_execution_id)`, `(status_updated_on)`.

## Claim / run flow

1. **Seed** — on zone job start (or seed API): insert missing partitions as `pending` (idempotent on unique key).
2. **Claim** — Middleware API claims up to **5** `pending` rows → `in_progress`; bumps `status_on` / `status_updated_on`; returns rows to Spark/Airflow. **API is sole writer.**
3. **Complete** — callback/API sets `done` or `failed`; updates timestamps; may enrich `configs_json`.
4. **Re-run** — only claims further `pending`. `failed` → `pending` only via explicit reset API (not automatic).

## API surface (Middleware)

- Full **CRUD** per zone table (create / get / list / update / delete) via Middleware (sole writer of ops store).
- Extra ops for the queue: seed, claim(`limit=5`), complete, reset-failed.
- Zone-parameterized routes (or five thin twins) under admin/management.
- DAO + Alembic model(s) following existing singleton / ctx / factory patterns.
- Spark/Airflow call Middleware; never write these tables directly.

### List / filter contract

- Default list: **reverse chronicle** by `status_updated_on` (newest first).
- **Page size max 30** (default 30).
- Narrowing beyond the latest page requires criteria on the listing request, e.g.:
  - start date / end date
  - start time / end time (with dates, or as datetime range)
  - workflow / execution id (and optionally `partition_key`, `status`, endpoint ids)
- Without extra criteria, UI/API only surfaces the latest ≤30 rows for that zone.

## Admin portal (Ingestion Logs)

- New left-nav parent: **Ingestion Logs**.
- Sub-items (one listing page per table):
  - Raw → `ingest_log_raw`
  - Refined → `ingest_log_refined`
  - Curated → `ingest_log_curated`
  - Taxonomy → `ingest_log_taxonomy`
  - Chroma → `ingest_log_chroma`
- Each listing: reverse chronicle, page size ≤30; filter form for date/time range, workflow id, etc. before deeper history / specifics.
- CRUD affordances consistent with other admin resources (create/edit/delete where operators need them; claim/complete remain system-driven).

## Out of scope (this story)

- Iceberg UI Docker (`local:containers:iceberg-ui:*`) — separate story.
- Changing Docker Desktop memory.
- Auto-claim wiring for every zone in one PR if too large: tables + CRUD + Admin list for all five; curated claim path first for OOM relief; other zones seed/claim can follow in the same story only if plan tasks stay small.

## Acceptance

1. Alembic upgrade creates all five tables on empty admin DB (Postgres + SQLite).
2. Claim returns ≤5 `pending` → `in_progress` atomically (no double-claim under concurrent callers).
3. Curated hydrate can drive off claimed partitions and finish without exit 137 / OOMKilled when pending work is batched ≤5 per run.
4. CRUD APIs + Admin **Ingestion Logs** nav with five sub-pages; list newest-first, max 30/page; filters required for deeper history.
5. Layer lint + unit/DAO/portal tests green; no Iceberg control table required.
