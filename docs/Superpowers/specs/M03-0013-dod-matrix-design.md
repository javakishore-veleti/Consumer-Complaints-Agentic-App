# M03-0013 (#123) DoD matrix: prove path on SQLite, Postgres, and MongoDB

Decisions: D75–D79 (pluggable store, SQLite-first, Postgres via `.env`, lite profiles, Mongo operational store). **No new DESIGN.md decision** — this story verifies and documents the three DoD backends already built. D64: no new facades.

## Goal

Epic #111 is not Done until the Admin UI → API → Airflow → callback → operational DB → Admin UI refresh path is **proven (or CI-friendly smoke-proven) on SQLite, Postgres, and MongoDB**. Deliver a written checklist, npm targets that exercise each profile, and an evidence log. Prefer reuse of existing smokes; use mongomock / skip-if-no-URL for CI where live Airflow+DB cannot run.

## Context (already built)

| Backend | Automated proof (reuse) | Live / manual |
|---|---|---|
| **SQLite** (default) | `tests/test_e2e_happy_path_smoke.py` → `npm run local:e2e:happy-path:smoke` | `docs/local-admin-e2e-happy-path.md` + `local:e2e:happy-path:probe` |
| **Postgres** | `test_start_workflow_and_callback_persist_on_postgres` in `tests/test_postgres.py` (requires `CCA_TEST_POSTGRES_URL`; CI sets it) | Profile `local:containers:postgres:*` + `.env` `CCA_OPERATIONAL_STORE=postgres` / `CCA_DB_URL` |
| **MongoDB** | `test_start_workflow_and_callback_persist_on_mongo` in `tests/test_mongodb_operational_store.py` (mongomock; always CI) | Profile `local:containers:mongodb:*` + `.env` `CCA_OPERATIONAL_STORE=mongodb` |

Constraints from the epic: change only `.env` between backends; do **not** invent UI status (D71/D72 / #122).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Docs-only checklist for three full UI→Airflow paths | Meets “written checklist”; weak automation / CI gate |
| B (chosen) | Checklist + npm matrix targets that wrap **existing** per-backend smokes; evidence table; live Airflow remains opt-in per profile | Proves the three stores in CI where possible; no new facades; epic can close on smoke + recorded evidence |
| C | Playwright UI E2E × three live DB + Airflow stacks | Heavy, flaky, not CI-friendly; out of proportion for M03 |

## Design

### 1. Checklist doc

Add `docs/local-admin-e2e-dod-matrix.md`:

1. **Purpose** — Epic #111 DoD requires all three backends.
2. **CI / automated matrix** — one command runs the three smokes (Postgres skipped locally unless `CCA_TEST_POSTGRES_URL` is set; still runs in GitHub Actions).
3. **Per-profile live checklist** — for each of sqlite / postgres / mongodb: set `.env`, start containers (`local:containers:<profile>:start`), migrate/bootstrap, start API+Admin UI, run happy-path steps from `docs/local-admin-e2e-happy-path.md`, record evidence.
4. **Evidence table** — date, profile, command or checklist step, result (pass/fail), notes. Fill with CI/local smoke results for this story; leave live Airflow rows as optional “recorded when run”.
5. **Links** — happy-path doc, profiles (D78), PRODUCT / Milestone.

Do not invent status strings; point at D30 / `#122` expectations only.

### 2. npm targets

| Script | Behavior |
|---|---|
| `local:e2e:dod-matrix:sqlite` | Same as `local:e2e:happy-path:smoke` (SQLite TestClient path) |
| `local:e2e:dod-matrix:postgres` | `pytest tests/test_postgres.py::test_start_workflow_and_callback_persist_on_postgres -q` (skip/fail clearly if URL unset) |
| `local:e2e:dod-matrix:mongodb` | `pytest tests/test_mongodb_operational_store.py::test_start_workflow_and_callback_persist_on_mongo -q` |
| `local:e2e:dod-matrix:smoke` | Shell wrapper under `CICD/Local/` that runs all three, prints a PASS/SKIP/FAIL matrix summary, exits non-zero if any required check fails. SQLite + Mongo always required; Postgres required when `CCA_TEST_POSTGRES_URL` is set **or** when `CCA_DOD_REQUIRE_POSTGRES=1` (CI sets URL already via full pytest; wrapper still useful for focused matrix). |

Reuse existing probe via documenting `local:e2e:happy-path:probe` under each live profile — no duplicate probe script.

### 3. Thin test/marker (optional but preferred)

Add `tests/test_dod_matrix_smoke.py` that **imports/re-invokes** or simply documents selection via pytest node ids already used by npm. Prefer **no duplicated assertion logic**: either thin wrappers that call the same helpers, or npm-only selection of existing tests. Chosen: **npm + wrapper script select existing tests**; add a tiny `test_dod_matrix_smoke.py` only if it improves discoverability — e.g. three tests that `pytest.importorskip` / mark and assert the existing modules’ smoke entrypoints are collectable. YAGNI: **skip new pytest file** if npm scripts + docs are enough; add a small meta-test that asserts the three node ids exist so the matrix cannot rot.

Chosen meta-test: `tests/test_dod_matrix_smoke.py` with one test that collects/asserts the three existing test function names are importable/callable entrypoints (or runs them via subprocess of pytest -q on those node ids from within... too heavy). Simpler: one test documenting the matrix contracts by importing the three modules and checking the function objects exist.

### 4. PRODUCT / Milestone / happy-path cross-links

- Update `docs/local-admin-e2e-happy-path.md` “Related” with the DoD matrix doc and npm matrix smoke.
- On epic complete (after this story): `docs/PRODUCT_FEATURES.md` M03 row → Done; Milestone_03 status → complete via `ccaa-epic-complete`.

### 5. Out of scope

- New Middleware facades or portal features
- Making live Airflow mandatory in CI
- Changing DAO/factory behavior
- Inventing or mapping status enums in the UI

## Acceptance mapping

| Acceptance | Deliverable |
|---|---|
| Written checklist under docs (or npm smoke target) | `docs/local-admin-e2e-dod-matrix.md` + `local:e2e:dod-matrix:*` |
| Evidence SQLite | Matrix doc evidence row + smoke always green |
| Evidence Postgres | CI / `CCA_TEST_POSTGRES_URL` smoke + evidence row (SKIP noted when URL absent locally) |
| Evidence MongoDB | mongomock smoke + evidence row |
| Epic DoD only after all three | Feature #115 / epic #111 complete only after this story; checklist states that gate |

## Self-review

- No TBD placeholders; Postgres skip vs require is explicit.
- Reuses #122 / #118 / #119 smokes; no invented UI status.
- Scope is docs + npm + thin wrapper/meta-test only.
