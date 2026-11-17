# Milestone M14 - Sync secrets rewrite loopback for Airflow

**Scope:** Sync secrets rewrites `127.0.0.1`/`localhost` → `host.docker.internal` for URL-valued Airflow Variables.

**Status: in progress.** Stories left to build: 1. Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #241 | M14-0001 | Story | Sync secrets: rewrite loopback hosts to host.docker.internal for URL Variables |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #241 | 1 | `/ccaa-story-start 241` | Done | 2026-11-17 16:11 |
| #241 | 2 | worktree + TDD + implement rewrite | In progress | 2026-11-17 16:11 |
| #241 | 3 | `/ccaa-commit-push` | Planned | - |
| #241 | 4 | `/ccaa-story-complete 241` | Planned | - |

## 3. Notes

- Sync overwrites manual Variable fixes; durable fix belongs in upsert-secrets service.
