# M57-0001 JSON chronicle Implementation Plan

**Goal:** Append-only `wf_engine_data_json` / `wf_exec_data_json`; append engine entry only when optional JSON present; eye-modal pagination.

**Spec:** `docs/Superpowers/specs/2026-11-20-m57-0001-wf-exec-json-chronicle-design.md`

### Task 1: Alembic 0032 + models + DAO append
### Task 2: POST callback optional fields + append rule + start_wf append
### Task 3: workflow-logs API + Admin modal pagination
### Task 4: Airflow helper kwargs for invoked_* ; tests; PR
