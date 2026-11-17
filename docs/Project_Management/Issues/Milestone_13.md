# Milestone M13 - Local Airflow DB URL for Docker

**Scope:** After Sync secrets, Airflow `CCA_DB_URL` must use `host.docker.internal` (not `127.0.0.1`) so DAGs can reach ops Postgres from containers; document in the 3m localhost runbook.

**Status: in progress.** Stories left to build: 1. Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #240 | M13-0001 | Story | Runbook: Airflow CCA_DB_URL must use host.docker.internal after Sync |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #240 | 1 | `/ccaa-story-start 240` | Done | 2026-11-17 16:08 |
| #240 | 2 | brainstorming / design (if needed) | Done | 2026-11-17 16:09 |
| #240 | 3 | `/using-git-worktrees` | Done | 2026-11-17 16:09 |
| #240 | 4 | Update `docs/Runbooks/Localhost/3m-pgvector-chroma.md` | Done | 2026-11-17 16:09 |
| #240 | 5 | `/ccaa-commit-push` | In progress | 2026-11-17 16:09 |
| #240 | 6 | `/ccaa-story-complete 240` | Planned | - |

## 3. Notes

- Observed: Sync copies Middleware `CCA_DB_URL=…@127.0.0.1:5432/cca` → Airflow Variable → `filter_cfpb_3_months` `resolve_and_filter` fails with connection refused inside Docker.
- Runbook §0.4 step 4 + troubleshooting row document rewrite to `host.docker.internal` after every Sync.
