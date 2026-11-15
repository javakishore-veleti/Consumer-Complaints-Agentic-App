# M03-0006 (#116) Pluggable DB seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document and wire the operational-store profile seam (SQLite default, Postgres via `CCA_DB_URL`, MongoDB via `.env`) so later stories (#117–#119) can swap backends without rewriting DAOs/facades/API.

**Architecture:** `get_settings()` resolves `operational_store` and validates profile env (D75). SQLAlchemy DAOs stay for sqlite/postgres. `DaoObjectsFactory.init()` rejects `mongodb` until #119. Docs: DESIGN D75, ARCHITECTURE §6, `.env.example` profiles.

**Tech Stack:** Python 3.11+, pytest, uv; docs in DESIGN/ARCHITECTURE/Superpowers.

Spec: `docs/Superpowers/specs/M03-0006-pluggable-db-seam-design.md`. Decision: **D75**.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run pytest / lint from there unless a step says otherwise.
- Do **not** implement Mongo DAO classes (story #119).
- Do **not** add new facade packages (D64).
- Do **not** edit files owned by parallel stories #120 / #121.
- Scratch under `runtime_data/tmp/` (D36); never commit it.
- Commit with `/ccaa-commit-push 116` only (never raw unscoped commits). Author `javakishore-veleti`; strip AI Co-authored-by trailers.
- Next free decision after this story is **D76+**.

## File Structure

| File | Responsibility |
|---|---|
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | Add D75 row |
| `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` | Three local operational backends in §6 (+ diagram note) |
| `Middleware/ConsumerComplaintsHandsOn/.env.example` | SQLite / Postgres / MongoDB profile comments + vars |
| `docs/Project_Management/Issues/Milestone_03.md` | Workflow status; next decision D76+ |
| `docs/Superpowers/specs/M03-0006-pluggable-db-seam-design.md` | Spec (this story) |
| `docs/Superpowers/plans/M03-0006-pluggable-db-seam-plan.md` | This plan |
| `app/core/common/config.py` | `operational_store`, `mongo_operational_url`, resolution + validation |
| `app/core/dao/objects_factory.py` | Fail fast when store is `mongodb` (seam hook for #119) |
| `tests/test_operational_store_settings.py` | TDD for profile resolution |

---

### Task 1: Decision + architecture + env docs

**Files:** DESIGN.md, ARCHITECTURE.md, `.env.example`, Milestone_03.md notes

- [ ] **Step 1: Add D75** to DESIGN.md after D74 (full seam rules from the spec).
- [ ] **Step 2: Update ARCHITECTURE.md** §6 (and write-rule note if needed) so SQLite / Postgres / operational Mongo are the three local admin backends; keep complaint-data Mongo (D10) distinct.
- [ ] **Step 3: Document three profiles** in `.env.example` (`CCA_OPERATIONAL_STORE`, `CCA_DB_URL`, `CCA_DATA_DIR`, `CCA_MONGO_OPERATIONAL_URL`).
- [ ] **Step 4: Milestone note** — next free decision **D76+**.
- [ ] **Step 5: Commit** — `M03-0006 #116: document pluggable DB seam (D75)`

### Task 2: Settings resolution (TDD)

**Files:**
- Create: `tests/test_operational_store_settings.py`
- Modify: `app/core/common/config.py`

- [ ] **Step 1: Write failing tests** for default sqlite, postgres via URL, explicit store, invalid store, mongodb without URL, postgres store without URL.
- [ ] **Step 2: Run tests — expect FAIL.**
- [ ] **Step 3: Implement** `operational_store` / `mongo_operational_url` on `Settings` and resolution in `get_settings()`.
- [ ] **Step 4: Run tests — expect PASS.**
- [ ] **Step 5: Commit** — `M03-0006 #116: resolve operational store profile in settings`

### Task 3: Factory seam hook for Mongo

**Files:**
- Modify: `app/core/dao/objects_factory.py`
- Extend: `tests/test_operational_store_settings.py` (or factory test)

- [ ] **Step 1: Failing test** — with `CCA_OPERATIONAL_STORE=mongodb` and a URL, `DaoObjectsFactory.init()` raises a clear error mentioning #119.
- [ ] **Step 2: Implement** the guard at the start of `init()` (after lock / before SQLAlchemy register). Reset factory `_initialized` in tests if needed.
- [ ] **Step 3: Confirm sqlite/postgres init still registers SQLAlchemy DAOs.**
- [ ] **Step 4: Commit** — `M03-0006 #116: guard mongo operational store until #119`

### Task 4: Verify and finish

- [ ] **Step 1:** `npm run local:api:lint` and `npm run local:api:test` from repo root (worktree).
- [ ] **Step 2:** Acceptance checklist vs issue #116.
- [ ] **Step 3:** Final `/ccaa-commit-push 116`, PR → main, green CI, merge, `/ccaa-story-complete 116`.
