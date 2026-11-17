# Milestone M11 - Import runs and selective Mongo ingest

**Scope:** UTC timestamped import landing folders, import registry, selective Mongo ingest UI, wrapper + core Airflow DAGs. Local path first; location abstraction for later S3/etc.

**Status: in progress.** Spec: `docs/Superpowers/specs/2026-11-17-import-runs-selective-mongo-ingest-design.md`. Plan: `docs/superpowers/plans/2026-11-17-import-runs-selective-mongo-ingest-plan.md`.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #229 | M11-0001 | Feature | Timestamped imports + selective Mongo ingest |
| 2 | #230 | M11-0002 | Story | Import registry table + DAO |
| 3 | #231 | M11-0003 | Story | Stage DAG: UTC run folder, metadata, registry row |
| 4 | #232 | M11-0004 | Story | Admin: list imports, ingest checkboxes, sequential/parallel |
| 5 | #233 | M11-0005 | Story | Wrapper + core Mongo ingest DAGs and registry callbacks |
| 6 | #234 | M11-0006 | Story | Runbook: timestamped imports + selective Mongo ingest |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #229 | — | written spec + plan | Done | 2026-11-17 10:00 | 2026-11-17 10:15 |
| #230 | 1 | `/ccaa-story-start 230` | Done | 2026-11-17 10:15 | 2026-11-17 10:16 |
| #230 | 2–11 | registry migration + DAO + tests | Done | 2026-11-17 10:16 | 2026-11-17 10:20 |
| #230 | 12 | `/ccaa-story-complete 230` | Done | 2026-11-17 10:20 | 2026-11-17 10:19 |
| #231 | 1 | `/ccaa-story-start 231` | Done | 2026-11-17 10:19 | 2026-11-17 10:19 |
| #231 | 2–11 | stage run folder + registry callbacks | Done | 2026-11-17 10:19 | 2026-11-17 10:25 |
| #231 | 12 | `/ccaa-story-complete 231` | In progress | 2026-11-17 10:25 | - |
| #232 | 1 | `/ccaa-story-start 232` | Planned | - | - |
| #233 | 1 | `/ccaa-story-start 233` | Planned | - | - |
| #234 | 1 | `/ccaa-story-start 234` | Planned | - | - |

## 3. Notes

- Folder name = import/stage **workflow start** (UTC).
- Sequential/parallel chosen when starting **Mongo ingest** workflow.
- Iteration in wrapper DAG, not Middleware.
