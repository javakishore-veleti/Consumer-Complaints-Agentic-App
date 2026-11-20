# M55-0011 Zone ingest_log partition queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Durable Middleware zone ingest logs (five tables) with Alembic-on-startup, CRUD + claim≤5 APIs, and Admin **Ingestion Logs** nav (reverse chronicle, max 30/page, filters).

**Architecture:** Same shape on `ingest_log_{raw,refined,curated,taxonomy,chroma}` in admin schema; SQLAlchemy models + DAO factory; zone-parameterized FastAPI router; Angular left-nav + one listing page parameterized by zone. API sole writer. Curated hydrate later consumes claim API (task at end).

**Tech Stack:** FastAPI, Alembic, SQLAlchemy, Pytest, Angular 22 admin, Postgres/SQLite ops store.

**Story:** #391 · **Spec:** `docs/Superpowers/specs/2026-11-19-m55-0011-zone-ingest-log-partition-queue-design.md`  
<!-- progress: Tasks 1–6 implemented 2026-11-19; Task7 verification/PR next -->
**Worktree:** `.worktrees/story/m55-partition-batches` · branch `story/m55-0011-partition-batches`

## Global Constraints

- No vibe coding; TDD; product edits only in story worktree.
- Soft refs only (no FKs), matching `app_endpoints` / `mios_ingest_log` style.
- List default: `ORDER BY status_updated_on DESC`, `limit` default 30 max 30.
- Claim limit hard-capped at 5.
- Discard obsolete hash-batch WIP (`hydrate_curated` partial edits + `test_m55_curated_partition_batches.py` + old partition-batches design) before Task 1.

## File map

| Area | Paths |
|------|--------|
| Migration | `Middleware/ConsumerComplaintsHandsOn/alembic/versions/0031_create_zone_ingest_logs.py` |
| Models | `…/dao/impl/models.py` — five models or shared mixin + five tables |
| Mongo bootstrap | `…/dao/impl/mongo/bootstrap.py` — five collections + indexes |
| DTOs | `…/common/dtos/zone_ingest_log_dtos.py` |
| DAO iface/impl | `…/dao/zone_ingest_log_dao.py`, `…/dao/impl/sqlalchemy_zone_ingest_log_dao.py`, mongo twin if required by factory |
| Factory | `…/dao/objects_factory.py` |
| API | `…/api/routers/zone_ingest_log_api.py`, `…/api/models/zone_ingest_log_models.py`, register in `main.py` |
| Schema tests | `tests/test_schema.py`, `tests/test_zone_ingest_log_dao.py`, `tests/test_zone_ingest_log_api.py` |
| Admin | `Portals/…/app-sidebar.component.ts`, routes, `pages/ingestion-logs/` |
| Curated claim | `CICD/Local/iceberg/scripts/hydrate_curated_3m.py` + thin Airflow/helper call to claim API (last task) |

### Zones constant

```python
ZONE_INGEST_LOG_TABLES = ("raw", "refined", "curated", "taxonomy", "chroma")
# physical names: ingest_log_{zone}
```

---

### Task 1: Discard obsolete hash-batch WIP + sync Superpowers docs into worktree

**Files:**
- Delete/revert in worktree: `CICD/Local/iceberg/scripts/hydrate_curated_3m.py` WIP, `tests/test_m55_curated_partition_batches.py`, `docs/Superpowers/specs/2026-11-19-m55-0011-curated-partition-batches-design.md`
- Ensure worktree has current: zone design spec + this plan + no-vibe / manager rules (copy from main if needed)

- [ ] **Step 1:** `git checkout -- CICD/Local/iceberg/scripts/hydrate_curated_3m.py` (or restore from `main`)
- [ ] **Step 2:** Remove obsolete untracked hash-batch test/spec
- [ ] **Step 3:** Copy/update `docs/Superpowers/specs/2026-11-19-m55-0011-zone-ingest-log-partition-queue-design.md` and this plan into worktree; commit board+docs if on branch

```bash
git add docs/Superpowers/specs/2026-11-19-m55-0011-zone-ingest-log-partition-queue-design.md \
  docs/Superpowers/plans/2026-11-19-m55-0011-zone-ingest-log-partition-queue-plan.md
git commit -m "$(cat <<'EOF'
docs(M55-0011): zone ingest_log design + implementation plan

EOF
)"
```

---

### Task 2: Alembic 0031 — five `ingest_log_*` tables

**Files:**
- Create: `Middleware/ConsumerComplaintsHandsOn/alembic/versions/0031_create_zone_ingest_logs.py`
- Modify: `tests/test_schema.py`
- Test: same

**Produces:** Tables `ingest_log_raw|refined|curated|taxonomy|chroma` with columns from spec + indexes.

- [ ] **Step 1: Failing schema test** — assert five tables exist with expected columns after migrate:

```python
ZONES = ("raw", "refined", "curated", "taxonomy", "chroma")
EXPECTED_COLS = {
    "id", "partition_key", "data_tech", "source_end_point_id", "dest_end_point_id",
    "workflow_execution_id", "status", "status_on", "status_updated_on", "configs_json",
}

def test_zone_ingest_log_tables_exist_with_expected_columns(data_dir):
    with _admin_db(data_dir) as db:
        for z in ZONES:
            name = f"ingest_log_{z}"
            assert db.execute(f"select name from sqlite_master where name = '{name}'").fetchall()
            cols = _columns(db, name)
            assert EXPECTED_COLS <= set(cols)
```

- [ ] **Step 2:** Run test — expect FAIL (tables missing)
- [ ] **Step 3:** Add migration `0031` revising `0030`; create each table + unique `(partition_key, source_end_point_id, dest_end_point_id)` + indexes; `configs_json` as `Text`
- [ ] **Step 4:** ORM models in `models.py` (five classes or factory helper); register metadata
- [ ] **Step 5:** Mongo bootstrap: five collections + same indexes
- [ ] **Step 6:** Tests pass; commit

```bash
cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_schema.py -q -k zone_ingest
```

---

### Task 3: DTOs + DAO create/get/list/update/delete + claim

**Files:**
- Create DTOs, DAO interface, SQLAlchemy impl, factory wiring
- Test: `tests/test_zone_ingest_log_dao.py`

**Interfaces:**
- `ZoneIngestLogDao.create|get|list|update|delete|claim_pending(zone, limit=5) -> int` with `ZoneIngestLogCtx`
- `list`: order by `status_updated_on DESC`; clamp limit to `[1,30]`; optional filters: datetime range on `status_updated_on`, `workflow_execution_id`, `status`, `partition_key`
- `claim_pending`: select up to `min(limit,5)` rows `status='pending'` `ORDER BY status_updated_on ASC` (oldest pending first), set `in_progress`, bump timestamps; atomic / skip locked where backend allows

- [ ] **Step 1:** Failing DAO tests (create + list newest-first + claim ≤5 + double-claim)
- [ ] **Step 2:** Implement until green
- [ ] **Step 3:** Commit

---

### Task 4: FastAPI CRUD + claim/complete/reset routes

**Files:**
- `app/api/routers/zone_ingest_log_api.py` prefix `/ingestion-logs/{zone}`
- Register router in app factory/`main.py`
- Test: `tests/test_zone_ingest_log_api.py`

**Routes:**
- `GET /ingestion-logs/{zone}` — list (query: limit≤30, start/end datetimes, workflow_execution_id, status, partition_key)
- `GET /ingestion-logs/{zone}/{id}`
- `POST /ingestion-logs/{zone}`
- `PUT /ingestion-logs/{zone}/{id}`
- `DELETE /ingestion-logs/{zone}/{id}`
- `POST /ingestion-logs/{zone}/claim` body `{ "limit": 5 }`
- `POST /ingestion-logs/{zone}/{id}/complete` body `{ "status": "done"|"failed", "configs_json": ... }`
- `POST /ingestion-logs/{zone}/{id}/reset` — failed→pending only

- [ ] **Step 1:** API tests fail
- [ ] **Step 2:** Implement router + openapi sync if required by suite
- [ ] **Step 3:** `uv run lint-imports` + pytest; commit

---

### Task 5: Admin Ingestion Logs nav + listing pages

**Files:**
- Modify: `Portals/consumer-complaints-admin/src/app/layout/shell/app-sidebar/app-sidebar.component.ts`
- Create: `pages/ingestion-logs/ingestion-logs-page.component.ts` (+ html/scss), routes in `app.routes.ts`
- Service calling `/ingestion-logs/{zone}`
- Test: Karma/Jasmine or existing portal test pattern for nav + list

**UI:**
- Parent nav **Ingestion Logs** with sub-items Raw/Refined/Curated/Taxonomy/Chroma → `/ingestion-logs/{zone}`
- Table: reverse chronicle; page size 30
- Filter form: start date, end date, start time, end time, workflow execution id (required to dig past default latest page semantics — applying filters re-queries API)

- [ ] **Step 1:** Failing nav/route test or component test
- [ ] **Step 2:** Implement sidebar + page + service
- [ ] **Step 3:** `npm run local:portal:admin:test -- --watch=false` (or project-equivalent); commit

---

### Task 6: Curated hydrate uses claim API (≤5 partitions)

**Files:**
- Modify: `CICD/Local/iceberg/scripts/hydrate_curated_3m.py` (and/or DAG helper) to claim curated partitions via Middleware, process claimed keys only
- Test: unit/script test with mocked claim response

- [ ] **Step 1:** Failing test that claim path is invoked / partition filter applied
- [ ] **Step 2:** Minimal wiring; keep M55-0008/0009/0010 memory settings
- [ ] **Step 3:** Commit

---

### Task 7: Verification + finish branch

- [ ] Full `npm run local:api:test` / targeted pytest + lint-imports + portal tests
- [ ] Update Milestone_55 Superpowers rows through verification / finish / story-complete as skills require
- [ ] `/ccaa-commit-push 391` and finishing-a-development-branch (PR)

## Spec coverage check

| Spec item | Task |
|-----------|------|
| Five Alembic tables + columns | 2 |
| Claim ≤5 + statuses | 3–4 |
| CRUD + list filters max 30 | 3–4 |
| Admin Ingestion Logs nav | 5 |
| Curated OOM batching via queue | 6 |
| No Iceberg control table | all |

## Stale artifacts (do not keep)

- `docs/Superpowers/specs/2026-11-19-m55-0011-curated-partition-batches-design.md` (hash-batch) — delete
- Any plan titled only “partition batches hash” without Middleware ingest_log — replace with this plan
