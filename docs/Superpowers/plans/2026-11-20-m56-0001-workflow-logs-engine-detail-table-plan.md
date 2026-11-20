# M56-0001 Workflow Logs engine + table UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or implement inline under manager-only.

**Goal:** Workflow Engine column/filter, Completed column, eye→detail modal, default 60 rows with pagination, sortable + per-column searchable table.

**Spec:** `docs/Superpowers/specs/2026-11-20-m56-0001-workflow-logs-engine-detail-table-design.md`

---

### Task 1: EngineType catalog + labels + API page size 60 + engine_type filter

**Files:**
- `app/core/common/app_types_constants.py` — add spring_batch, bpmn, spark_job, aws_emr
- `app/core/common/workflow_log_categories.py` — PAGE_SIZE_MAX=60, ENGINE_TYPE_LABELS
- `app/api/models/workflow_logs_models.py` — limit le=60, engine_type query, engine_label on Out
- `app/api/routers/workflow_logs_api.py` — pass engine_type; set engine_label
- Tests: update limit 31→61; engine_type filter; EngineType.values()

**Commit:** `M56-0001 #396: engine catalog + workflow-logs limit 60`

### Task 2: Portal table UX

**Files:**
- `core/workflow-logs.ts` — page size 60, engine_type filter
- `pages/workflow-logs/workflow-exec-logs-page.component.{ts,html}` — columns, sort, search, pagination, eye modal
- Spec test for engine column / modal if easy

**Commit:** `M56-0001 #396: Workflow Logs table engine detail sort search`

### Task 3: Verify + PR

lint, pytest, portal tests, openapi, PR, merge, story-complete.
