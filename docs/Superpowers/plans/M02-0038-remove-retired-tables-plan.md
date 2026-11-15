# M02-0038 (#88) Remove retired tables Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop `system_datasets` and `data_ingest_log` with Alembic `0010`, remove every DAO/service/facade/API/test that only served them, regenerate OpenAPI, and update DESIGN/ARCHITECTURE so they are no longer described as built.

**Architecture:** History migrations `0001`/`0002` stay. New migration `0010` (after `0009`) drops both tables on upgrade and recreates them on downgrade. Application code that referenced those tables is deleted; factories and remaining tests no longer register or import them. Portal and workflow paths are untouched.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, pytest, `uv`; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0038-remove-retired-tables-design.md`. Decision: **D74**.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run commands from there unless noted as repository root.
- Migration `0010_drop_retired_system_datasets_and_data_ingest_log.py`: `revision = "0010"`, `down_revision = "0009"`, schema `consumer_comp_db`.
- Do not edit `0001` or `0002`.
- Do not break catalog, `app_workflows*`, `mios_ingest_log`, callbacks, or portal routes.
- Regenerate OpenAPI with `uv run python scripts/export_openapi.py` (or `npm run local:api:openapi` from repo root).
- Commit with `/ccaa-commit-push 88` (`M02-0038 #88: ...`); strip AI trailers. Scratch in `runtime_data/tmp/` only.

## File Structure

| File | Responsibility |
|---|---|
| `alembic/versions/0010_drop_retired_system_datasets_and_data_ingest_log.py` | drop both tables (up); recreate (down) |
| `app/core/dao/impl/models.py` | remove the two models |
| DAO / service / facade / API modules listed in the spec | delete |
| `objects_factory.py` (dao, services, facades, api) | unregister and stop including |
| `tests/*` listed in the spec | delete or adapt |
| `openapi.json` | regenerate |
| `DESIGN.md`, `ARCHITECTURE.md`, milestone | D74 and wording |

---

### Task 1: Design decision D74 and docs stubs

- [ ] Write/confirm spec and plan under `docs/Superpowers/`.
- [ ] Add D74 to `DESIGN.md`; next decision D75 in DESIGN and `Milestone_02.md`.
- [ ] Commit: `M02-0038 #88: record D74 remove-retired-tables design`

### Task 2: Migration `0010` (TDD)

- [ ] Update `test_schema.py`: at head, neither table exists; add `test_migration_0010_runs_down_and_up`.
- [ ] Add migration; make schema tests pass.
- [ ] Adapt `test_postgres.py` upgrade/downgrade expectations; remove retired DAO/service Postgres cases.
- [ ] Commit: `M02-0038 #88: drop retired tables in migration 0010`

### Task 3: Remove application layers

- [ ] Delete retired modules; strip models and factory registrations.
- [ ] Delete retired unit/API tests; fix singletons, factory_init, callback_secret open-route assertion.
- [ ] Regenerate `openapi.json`.
- [ ] Commit: `M02-0038 #88: remove retired DAOs services and data-ingest API`

### Task 4: Docs + verify

- [ ] Update DESIGN section 3 / D39 example and ARCHITECTURE store tables.
- [ ] Run `npm run local:api:lint` and `npm run local:api:test` from repo root.
- [ ] Commit: `M02-0038 #88: stop describing retired tables as built`
- [ ] Open PR closing #88; do not merge.
