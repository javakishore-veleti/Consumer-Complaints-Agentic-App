# Milestone M15 - DAG config via Middleware API

**Scope:** DAGs fetch ops config via Middleware API; no direct Postgres for catalog/exec config (bulk data paths may still use stores).

**Status: Done.** Stories left to build: 0. Stories already done: 1.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #242 | M15-0001 | Story | Middleware API for DAG execution config (replace DAG→Postgres) |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #242 | 1 | `/ccaa-story-start 242` | Done | 2026-11-17 16:12 |
| #242 | 2 | design + worktree + TDD | Done | 2026-11-17 16:20 |
| #242 | 3 | API + DAG helper + wire all config-reading DAGs | Done | 2026-11-17 16:20 |
| #242 | 4 | `/ccaa-commit-push` | Done | 2026-11-17 16:20 |
| #242 | 5 | `/ccaa-story-complete 242` | Done | 2026-11-17 16:21 |

## 3. Notes

- `GET /callbacks/workflow-executions/{id}/dag-context` (callback secret).
- Filter/download/ingest/index_* no longer use `CCA_DB_URL` / `make_engine` for ops config. Merged as `65a75e7`.
