# Milestone M12 - Airflow status reliability

**Scope:** Finalize / `notify_finished` always reports `completed` or `failed` to Middleware on Airflow 3 so Admin is not stuck on `started`.

**Status: in progress.**

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #239 | M12-0001 | Story | Airflow finalize status callback must always report (Airflow 3) |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #239 | 1 | `/ccaa-story-start 239` | Done | 2026-11-17 15:54 |
| #239 | 2 | brainstorming / design | In progress | 2026-11-17 15:54 |
| #239 | 3 | `/using-git-worktrees` | Planned | - |
| #239 | 4 | `/writing-plans` | Planned | - |
| #239 | 5 | TDD + implement shared finalize + all DAGs | Planned | - |
| #239 | 6 | `/ccaa-commit-push` after tasks | Planned | - |
| #239 | 7 | `/ccaa-story-complete 239` | Planned | - |

## 3. Notes

- Root cause: `dag_run.get_task_instance(...)` missing on Airflow 3 → finalize crashes → Middleware never gets `failed`.
