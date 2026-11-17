# Milestone M15 - DAG config via Middleware API

**Scope:** DAGs fetch ops config via Middleware API; no direct Postgres for catalog/exec config (bulk data paths may still use stores).

**Status: in progress.** Stories left to build: 1. Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #242 | M15-0001 | Story | Middleware API for DAG execution config (replace DAG→Postgres) |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #242 | 1 | `/ccaa-story-start 242` | Done | 2026-11-17 16:13 |
| #242 | 2 | design + worktree + TDD | In progress | 2026-11-17 16:13 |
| #242 | 3 | API + DAG helper + wire all config-reading DAGs | Planned | - |
| #242 | 4 | \`/ccaa-commit-push\` | Planned | - |
| #242 | 5 | \`/ccaa-story-complete 242\` | Planned | - |

## 3. Notes

- M14 Sync rewrite (#241) closed as superseded by this approach.
