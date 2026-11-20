# Milestone M55 - Lakehouse Spark PATH hotfix

**Type:** Working **product** milestone (not docs-only).

**Demoable outcome:** `hydrate_*` spark-submit works inside `cca-spark-iceberg` (no `spark-submit: command not found`); Lakehouse dropdown shows pipeline sequence `1.`…`5.` with raw as default; hydrate_raw finds lift batches via Airflow Variable.

**Status: Open.** Stories left to build: 2. Stories already done: 1.

**GitHub Milestone:** M55 - Lakehouse Spark PATH hotfix (api id 56)

**Feature:** —

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #371 | M55-0001 | Story | Absolute spark-submit path in lakehouse_spark |
| 2 | #372 | M55-0002 | Story | Number and order Lakehouse hydrate dropdown |
| 3 | #374 | M55-0003 | Story | hydrate_raw sense_lift uses Variable landing path |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #371 | 1 | `/ccaa-story-start 371` | Done | 2026-11-19 20:00 | 2026-11-19 20:00 |
| #371 | 2 | `/brainstorming Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 3 | `/using-git-worktrees Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 4 | `/writing-plans Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 5 | `/test-driven-development Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 6 | `/subagent-driven-development Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 7 | `/ccaa-commit-push 371 (after each task)` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 8 | `/verification-before-completion Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 9 | `/requesting-code-review Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 10 | `/ccaa-commit-push 371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 11 | `/finishing-a-development-branch Story #371` | Done | 2026-11-19 20:01 | 2026-11-19 20:01 |
| #371 | 12 | `/ccaa-story-complete 371` | Done | 2026-11-19 20:26 | 2026-11-19 20:26 |
| #372 | 1 | `/ccaa-story-start 372` | Planned | - | - |
| #372 | 2 | `/brainstorming Story #372` | Planned | - | - |
| #372 | 3 | `/using-git-worktrees Story #372` | Planned | - | - |
| #372 | 4 | `/writing-plans Story #372` | Planned | - | - |
| #372 | 5 | `/test-driven-development Story #372` | Planned | - | - |
| #372 | 6 | `/subagent-driven-development Story #372` | Planned | - | - |
| #372 | 7 | `/ccaa-commit-push 372 (after each task)` | Planned | - | - |
| #372 | 8 | `/verification-before-completion Story #372` | Planned | - | - |
| #372 | 9 | `/requesting-code-review Story #372` | Planned | - | - |
| #372 | 10 | `/ccaa-commit-push 372` | Planned | - | - |
| #372 | 11 | `/finishing-a-development-branch Story #372` | Planned | - | - |
| #372 | 12 | `/ccaa-story-complete 372` | Planned | - | - |
| #374 | 1 | `/ccaa-story-start 374` | Done | 2026-11-19 20:26 | 2026-11-19 20:26 |
| #374 | 2 | `/brainstorming Story #374` | Done | 2026-11-19 20:26 | 2026-11-19 20:26 |
| #374 | 3 | `/using-git-worktrees Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 4 | `/writing-plans Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 5 | `/test-driven-development Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 6 | `/subagent-driven-development Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 7 | `/ccaa-commit-push 374 (after each task)` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 8 | `/verification-before-completion Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 9 | `/requesting-code-review Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 10 | `/ccaa-commit-push 374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 11 | `/finishing-a-development-branch Story #374` | Done | 2026-11-19 20:30 | 2026-11-19 20:30 |
| #374 | 12 | `/ccaa-story-complete 374` | In progress | 2026-11-19 20:30 | - |
