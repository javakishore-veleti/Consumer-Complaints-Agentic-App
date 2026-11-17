# Milestone M11 - Import runs and selective Mongo ingest

**Scope:** UTC timestamped import landing folders, import registry, selective Mongo ingest UI, wrapper + core Airflow DAGs. Local path first; location abstraction for later S3/etc.

**Status: planned.** Spec: `docs/Superpowers/specs/2026-11-17-import-runs-selective-mongo-ingest-design.md`

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

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #229 | — | written spec pending user review | Planned | — |
| #230 | 1 | `/ccaa-story-start 230` | Planned | — |
| #231 | 1 | `/ccaa-story-start 231` | Planned | — |
| #232 | 1 | `/ccaa-story-start 232` | Planned | — |
| #233 | 1 | `/ccaa-story-start 233` | Planned | — |
| #234 | 1 | `/ccaa-story-start 234` | Planned | — |

## 3. Notes

- Folder name = import/stage **workflow start** (UTC).
- Sequential/parallel chosen when starting **Mongo ingest** workflow.
- Iteration in wrapper DAG, not Middleware.
