# M03-0018 (#141) MIO↔workflow binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind workflows to MIOs via catalog table `mios_workflows`, seed an All MIO for `download_cfpb_all`, expose `allowed_workflows` on `GET /mios/status`, reject unbound starts, and make Imports pickers non-misleading.

**Architecture:** Mirror `mios_datasets` (DAO + Alembic + Mongo bootstrap). Extend `MioStatusService` to attach allowed workflows per MIO. Enforce in `StartWfService` when `mio_id` is set. Portal Imports uses `entry.allowed_workflows` only (stop global workflow list on Imports). Record **D84** in DESIGN.md.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, Mongo bootstrap, pytest; Angular 22 portal; Node 22.

## Global Constraints

- Spec: `docs/Superpowers/specs/M03-0018-mio-workflow-binding-design.md`. Decision **D84**.
- Work only under `.worktrees/m03-0018-mio-workflow-binding` on branch `m03-0018-mio-workflow-binding`.
- App root: `Middleware/ConsumerComplaintsHandsOn`. Portal: `Portals/consumer-complaints-admin`.
- D37 ctx-only signatures. D57: never derive binding from MIO **name**. D64: prefer extending existing packages (mio_status, start_wf) — no new facade package unless unavoidable.
- Migration `0011` revises `0010`. Fixed UUID5 seed ids (same style as `0006`/`0008`/`0009`).
- Commit via `/ccaa-commit-push 141` after each task. Message `M03-0018 #141: <imperative summary>`. Strip AI trailers.
- Do **not** add filter DAGs for 6/9/12 months in this story.

---

## File map

| Path | Responsibility |
|---|---|
| `app/core/common/dtos/mio_workflow_dtos.py` | MioWorkflow Record/Req/Resp/Ctx |
| `app/core/dao/mio_workflow_dao.py` | Interface |
| `app/core/dao/impl/models.py` | `MioWorkflowModel` → `mios_workflows` |
| `app/core/dao/impl/sqlalchemy_mio_workflow_dao.py` | SQLAlchemy DAO |
| `app/core/dao/impl/mongo/mongo_mio_workflow_dao.py` | Mongo DAO |
| `app/core/dao/objects_factory.py` | Register + `get_mio_workflow_dao()` |
| `alembic/versions/0011_mios_workflows_and_all_mio_seed.py` | Table + All MIO + bindings |
| `app/core/dao/impl/mongo/bootstrap.py` | Collection, indexes, same seed |
| `app/core/common/dtos/mio_status_dtos.py` | `allowed_workflows` on `MioStatusEntry` |
| `app/core/services/impl/mio_status_service_impl.py` | Fill allowed list |
| `app/core/services/impl/start_wf_service_impl.py` (or equivalent) | Reject unbound |
| `Portals/.../mio-status.ts` (+ specs) | Type + load |
| `Portals/.../imports-page.component.ts` (+ html/spec) | Per-MIO allowed picker |
| `DESIGN.md`, `ARCHITECTURE.md`, PRODUCT_FEATURES, e2e happy-path | D84 + docs |

---

### Task 1: `mios_workflows` table + DAO (SQLAlchemy) — TDD

**Files:** model, DTOs, interface, SQLAlchemy DAO, `objects_factory`, `tests/test_mio_workflow_dao.py`, `tests/test_schema.py`, `tests/test_singletons.py`

**Seed ids (plan fixed values in migration task; DAO tests use ephemeral rows):**

- [ ] **Step 1: Failing tests** — create/get/list-by-mio/delete; unique `(mio_id, workflow_id)` → CONFLICT; missing parent → INVALID_INPUT; schema asserts table after migrate head once migration exists (or skip schema until Task 2 if preferred — **prefer Task 1 table via migration stub**). *Practical order:* write DAO tests against `alembic upgrade` with Task 2 migration in same PR sequence: implement migration first in Task 2 if tests need the table — **combine:** Task 1 implements interface + SQLAlchemy against model registered for create_all in tests OR wait for migration.

**Preferred sequence for this repo:** migration creates table (Task 2); Task 1 is DTOs + DAO + tests that run after migrate. So **reorder: treat Task 1 as DTOs+DAO after Task 2**, OR do Task 2 first.

**Use this order instead:**

### Task 1 (revised): Alembic `0011` — table + All MIO + bindings

**Files:**
- Create: `alembic/versions/0011_mios_workflows_and_all_mio_seed.py`
- Modify: `tests/test_schema.py`

**Rules:**
- Table `mios_workflows`: `id` (str PK), `mio_id`, `workflow_id`, `created_at`; unique `(mio_id, workflow_id)`; indexes on each FK column.
- Seed MIO name exactly `Customer complaints all 2026` with UUID5 `uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m03-0018/mio-all-2026")`.
- Link All MIO to same CFPB dataset + locations as month MIOs (copy pattern from `0006`).
- Bind All → workflow id of `download_cfpb_all`; 3-months MIO → `filter_cfpb_3_months`.
- Downgrade removes seed rows + table.

- [ ] **Step 1: Failing schema tests** asserting table exists at head; All MIO present; bindings as above; 6/9/12 have zero rows in `mios_workflows`.
- [ ] **Step 2: Run tests — FAIL**
- [ ] **Step 3: Write migration**
- [ ] **Step 4: Tests PASS**
- [ ] **Step 5: `/ccaa-commit-push 141`** — `M03-0018 #141: add mios_workflows and All MIO seed`

---

### Task 2: MioWorkflow DAO (SQL + Mongo) + factory

**Files:** DTOs, DAO interface, SQLAlchemy + Mongo impls, `objects_factory`, `mongo/bootstrap.py` (collection + indexes + same seed), `tests/test_mio_workflow_dao.py`, mongo/postgres smoke updates as needed.

- [ ] **Step 1: Failing DAO tests** (create, get, list by `mio_id`, delete; conflict; invalid parents)
- [ ] **Step 2: Implement**
- [ ] **Step 3: Tests PASS** including mongomock bootstrap seed parity
- [ ] **Step 4: Commit** — `M03-0018 #141: add MioWorkflowDao sqlalchemy and mongo`

---

### Task 3: `GET /mios/status` includes `allowed_workflows`

**Files:** `mio_status_dtos.py`, `mio_status_service_impl.py`, API serialization if separate, `tests/test_mio_status_*.py`

**Shape (enabled only, ordered by `workflow_name`):**

```json
"allowed_workflows": [
  {
    "id": "...",
    "workflow_name": "download_cfpb_all",
    "engine_type": "apache_airflow",
    "engine_workflow_id": "download_cfpb_all",
    "enabled": true
  }
]
```

- [ ] **Step 1: Failing API/service tests** — All entry has download; 3-month has filter; 6-month `[]`
- [ ] **Step 2: Implement service join** (MioWorkflowDao.list by mio + AppWfDao.get; skip disabled)
- [ ] **Step 3: PASS + commit** — `M03-0018 #141: expose allowed_workflows on mio status`

---

### Task 4: Start workflow enforces binding

**Files:** start-wf service (prepare path), `tests/test_start_wf_*.py` / API tests

- [ ] **Step 1: Failing tests** — All+download → SUCCESS path (engine mocked); All+filter → INVALID_INPUT; 3-month+download → INVALID_INPUT; 6-month+any → INVALID_INPUT; start **without** `mio_id` unchanged
- [ ] **Step 2: Implement check** after MIO exists, before ingest/exec create
- [ ] **Step 3: PASS + commit** — `M03-0018 #141: reject start when workflow not allowed for MIO`

---

### Task 5: Imports portal uses `allowed_workflows`

**Files:** `mio-status.ts` (+spec), `imports-page.component.ts/html/spec`

- [ ] **Step 1: Failing portal tests** — select options come from entry; empty → Start disabled; no call dependency on global list for options
- [ ] **Step 2: Implement** — remove Imports `listWorkflows` init (or ignore it); default sole/first allowed; keep testids
- [ ] **Step 3: `nvm use 22` + portal test/build PASS**
- [ ] **Step 4: Commit** — `M03-0018 #141: Imports picker uses per-MIO allowed_workflows`

---

### Task 6: DESIGN D84 + product/e2e docs

**Files:** `DESIGN.md` (D84 row; revise D72; close D63 attach-open; catalog table list), `ARCHITECTURE.md`, `docs/PRODUCT_FEATURES.md`, `docs/local-admin-e2e-happy-path.md`, Milestone notes if needed

- [ ] **Step 1: Edit docs** to match built behavior (All MIO + filter on 3-month)
- [ ] **Step 2: Commit** — `M03-0018 #141: record D84 and update Imports docs`

---

## Verification (story end)

```bash
# From repo / worktree root
npm run local:api:lint
npm run local:api:test
cd Portals/consumer-complaints-admin && source ~/.nvm/nvm.sh && nvm use 22 && npm test -- --watch=false && npm run build
```

Then `/verification-before-completion`, `/requesting-code-review`, PR via `/finishing-a-development-branch`, `/ccaa-story-complete 141`.
