# M02-0019 (#58) 3 months filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Airflow DAG `filter_cfpb_3_months` that reads the All zip from the D63 landing directory, filters rows on `Date received` for the last N calendar months, writes `complaints_3_months.csv.zip`, reports status via D67, and register the workflow in `app_workflows` (migration `0009`).

**Architecture:** Stdlib filter helper under `Middleware/Airflow-dags/ccaa/`. DAG mirrors `download_cfpb_all` (started + ALL_DONE finalize). Catalog landing via existing `db_reader`. No portal changes.

**Tech Stack:** Apache Airflow 3.4.0, SQLAlchemy (`text`), stdlib `zipfile`/`csv`/`datetime`, Alembic, pytest, `uv`.

Spec: `docs/Superpowers/specs/M02-0019-3-months-filter-design.md`. Decisions: D63, D67, **D70**.

## Global Constraints

- Paths relative to repository root unless noted. App tests: `Middleware/ConsumerComplaintsHandsOn` with `uv run pytest` / `npm run local:api:test`.
- DAGs only in `Middleware/Airflow-dags` (D44). Never `import app.*` from that folder.
- `engine_type` is `apache_airflow`. DAG id = `filter_cfpb_3_months`.
- Airflow reads DB only (D11 / D51).
- Scratch under `runtime_data/tmp/`. Commits: `M02-0019 #58: ...` via `/ccaa-commit-push 58`.

## File Structure

| File | Responsibility |
|---|---|
| `Middleware/Airflow-dags/ccaa/filter_by_date.py` | Calendar-month cutoff + zip/CSV filter |
| `Middleware/Airflow-dags/filter_cfpb_3_months.py` | DAG + D67 tasks |
| `.../alembic/versions/0009_seed_filter_cfpb_3_months_workflow.py` | Seed |
| `DESIGN.md` / `Milestone_02.md` | D70; next decision D71 |
| `tests/test_ccaa_filter_by_date.py` | Unit tests |
| `tests/test_filter_cfpb_3_months_dag_file.py` | Path / topology |
| `tests/test_schema.py` + list/postgres/app_wf tests | Seed + ordered names |

---

### Task 1: Filter helper (TDD)

**Files:** Create `ccaa/filter_by_date.py`; test `test_ccaa_filter_by_date.py`.

- [ ] **Step 1: Write failing tests** for `subtract_calendar_months`, filter keep/drop/bad dates, missing column, missing source, optional expected count mismatch (caller-side or helper).
- [ ] **Step 2: Run tests — expect fail.**
- [ ] **Step 3: Implement helper** (stdlib only).
- [ ] **Step 4: Run tests — expect pass.**
- [ ] **Step 5: Commit** `M02-0019 #58: add ccaa filter_by_date helper for Date received windows`

### Task 2: DAG + D67 wiring (TDD)

**Files:** `filter_cfpb_3_months.py`; `test_filter_cfpb_3_months_dag_file.py`.

- [ ] **Step 1: Write path/topology test** (dag_id, notify_finished, ALL_DONE, status_callback, no app imports).
- [ ] **Step 2: Implement DAG** mirroring `download_cfpb_all` with filter logic + optional `expected_row_count` / `as_of_date`.
- [ ] **Step 3: Tests pass; commit** `M02-0019 #58: add filter_cfpb_3_months DAG with D67 callbacks`

### Task 3: Seed migration + registry tests

**Files:** `0009_...py`; extend `test_schema.py`; update `test_wf_list_*`, `test_app_wf_dao.py`, `test_postgres.py` ordered-name assertions; DESIGN.md D70; Milestone next D71.

- [ ] **Step 1: Failing schema/list tests expecting seed.**
- [ ] **Step 2: Migration `0009` with fixed UUID `4d3f1ee0-0b02-51cb-8959-2499896cc20e`.**
- [ ] **Step 3: Fix list/postgres assertions for two seeded workflows.**
- [ ] **Step 4: Record D70; next decision D71.**
- [ ] **Step 5: Lint + full API tests; commit** `M02-0019 #58: seed filter_cfpb_3_months workflow and record D70`

### Task 4: Verify and finish branch

- [ ] `npm run local:api:lint` and `npm run local:api:test`
- [ ] Milestone log through finishing; open PR closing #58; do not merge
