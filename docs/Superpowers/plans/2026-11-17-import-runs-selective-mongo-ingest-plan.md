# Import runs + selective Mongo ingest — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development). Steps use TDD.

**Goal:** Deliver M11 stories #230–#234 per `docs/Superpowers/specs/2026-11-17-import-runs-selective-mongo-ingest-design.md`.

**Architecture:** Operational table `dataset_import_runs`; stage DAG writes UTC run folders + registry rows; ingest UI selects rows; wrapper DAG triggers core ingest per id.

**Tech:** FastAPI + SQLAlchemy/Alembic + Mongo bootstrap; Airflow 3 DAGs; Angular Admin.

## Tasks

### Task 1 — #230 Registry table + DAO
- Migration `0020_create_dataset_import_runs.py`
- Model, DTO ctxs, Dao interface, SQLAlchemy + Mongo impls, factory wiring
- Tests: create/list/mark ingested/eligibility

### Task 2 — #231 Stage run folder + metadata
- Helpers under `ccaa/` for run folder + snapshot defaults
- Update `download_cfpb_all` split path to stage into `run/dataset/`
- API/callback to register/finalize import row
- Tests for folder layout + defaults

### Task 3 — #232 Admin ingest selection UI
- List eligible imports API
- Start wrapper with `import_ids` + `mode`
- DB Ingest page: checkboxes + sequential/parallel

### Task 4 — #233 Wrapper + core DAGs
- `ingest_cfpb_imports_wrapper` + core per-import ingest
- Reject already ingested; registry status callbacks

### Task 5 — #234 Runbook
- Update localhost runbook for new flow

### Task 6 — Commit/push each story; close board
