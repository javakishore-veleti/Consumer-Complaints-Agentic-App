# M03-0013 DoD matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove (or CI-friendly smoke-prove) the M03 Admin happy path on SQLite, Postgres, and MongoDB via a documented checklist, npm matrix targets, and evidence — so epic #111 can close.

**Architecture:** Reuse existing per-backend smokes (`test_e2e_happy_path_smoke`, postgres start+callback, mongo mongomock start+callback). Add a thin matrix wrapper script, npm aliases, a meta-test that pins the three node ids, and `docs/local-admin-e2e-dod-matrix.md` with an evidence table.

**Tech Stack:** pytest, bash, npm scripts, mongomock (existing), optional `CCA_TEST_POSTGRES_URL`.

## Global Constraints

- Do not invent UI status (D71/D72 / #122).
- No new DESIGN.md decision; D64 no new facades.
- Prefer reuse of existing smoke/probe; mongomock / skip-if-no-URL for CI-friendly Postgres.
- Author commits as `javakishore-veleti`; strip AI trailers; message `M03-0013 #123: …`.

---

## File map

| File | Responsibility |
|---|---|
| `docs/local-admin-e2e-dod-matrix.md` | Checklist + evidence for three profiles |
| `CICD/Local/dod_matrix_smoke.sh` | Run three smokes; print PASS/SKIP/FAIL matrix |
| `package.json` | `local:e2e:dod-matrix:{sqlite,postgres,mongodb,smoke}` |
| `Middleware/.../tests/test_dod_matrix_smoke.py` | Meta-test: three smoke entrypoints exist |
| `docs/local-admin-e2e-happy-path.md` | Link to matrix |
| `docs/PRODUCT_FEATURES.md` | Touch only if closing M03 in this PR or note deferred to epic-complete |

---

### Task 1: Meta-test pins the three smoke entrypoints

**Files:**
- Create: `Middleware/ConsumerComplaintsHandsOn/tests/test_dod_matrix_smoke.py`

- [ ] **Step 1: Write the failing/passing meta-test**

```python
"""DoD matrix (M03-0013): pin SQLite / Postgres / Mongo smoke entrypoints."""

def test_dod_matrix_smoke_entrypoints_exist():
    from tests import test_e2e_happy_path_smoke as sqlite_mod
    from tests import test_postgres as pg_mod
    from tests import test_mongodb_operational_store as mongo_mod

    assert callable(sqlite_mod.test_happy_path_start_callback_mios_status)
    assert callable(pg_mod.test_start_workflow_and_callback_persist_on_postgres)
    assert callable(mongo_mod.test_start_workflow_and_callback_persist_on_mongo)
```

- [ ] **Step 2: Run meta-test**

```bash
cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_dod_matrix_smoke.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

`M03-0013 #123: pin DoD matrix smoke entrypoints`

---

### Task 2: Matrix smoke script + npm targets

**Files:**
- Create: `CICD/Local/dod_matrix_smoke.sh`
- Modify: `package.json`

- [ ] **Step 1: Write `dod_matrix_smoke.sh`**

Behavior:
1. `cd` to Middleware HandsOn (relative from repo root).
2. Run SQLite node id → record PASS/FAIL.
3. Run Mongo node id → record PASS/FAIL.
4. If `CCA_TEST_POSTGRES_URL` set (or `CCA_DOD_REQUIRE_POSTGRES=1`): run Postgres node id → PASS/FAIL; else SKIP (exit 0 for that cell unless require=1 without URL → FAIL).
5. Print a three-row matrix; exit 1 if any FAIL.

- [ ] **Step 2: Wire package.json**

```json
"local:e2e:dod-matrix:sqlite": "cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_e2e_happy_path_smoke.py::test_happy_path_start_callback_mios_status -q",
"local:e2e:dod-matrix:postgres": "cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_postgres.py::test_start_workflow_and_callback_persist_on_postgres -q",
"local:e2e:dod-matrix:mongodb": "cd Middleware/ConsumerComplaintsHandsOn && uv run pytest tests/test_mongodb_operational_store.py::test_start_workflow_and_callback_persist_on_mongo -q",
"local:e2e:dod-matrix:smoke": "bash CICD/Local/dod_matrix_smoke.sh"
```

- [ ] **Step 3: Run matrix smoke (no Postgres URL)**

```bash
npm run local:e2e:dod-matrix:smoke
```

Expected: SQLite PASS, Mongo PASS, Postgres SKIP; exit 0.

- [ ] **Step 4: Commit**

`M03-0013 #123: add DoD matrix npm smoke targets`

---

### Task 3: Checklist doc + cross-links + evidence

**Files:**
- Create: `docs/local-admin-e2e-dod-matrix.md`
- Modify: `docs/local-admin-e2e-happy-path.md`

- [ ] **Step 1: Write checklist** covering CI matrix command, live steps per profile, evidence table with rows filled from this session’s smoke runs (date + commands + pass/skip).
- [ ] **Step 2: Link from happy-path doc Related section.**
- [ ] **Step 3: Commit**

`M03-0013 #123: document DoD matrix checklist and evidence`

---

### Task 4: Verification

- [ ] `npm run local:api:lint`
- [ ] `npm run local:api:test` (or at least matrix + meta-test)
- [ ] `npm run local:e2e:dod-matrix:smoke`
- [ ] Confirm evidence table matches actual results
- [ ] Final `ccaa-commit-push 123` if needed
