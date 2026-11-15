# M03-0012 (#122) E2E happy path: UI → API → Airflow → callback → UI

Decisions: D11, D30, D59, D60, D61, D63, D66, D68, D71, D72, D75 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. **No new DESIGN.md decision** — this story documents and automates verification of the path already built in M02 + #121. D64: no new facades.

## Goal

Prove and document the local happy path on the **active operational store** (SQLite first per D75): **Admin UI → start workflow → Airflow → callback APIs → DB → Admin UI refresh**, with status that is **never invented** in the UI (only values persisted via D30/D60).

## Context (already built)

| Piece | Where |
|---|---|
| Imports list / start / refresh | Portal `#121` / D71 / D72; `local:portal:admin:with-api` |
| `GET /workflows`, `POST /workflows/{id}/start` | D66 / D68 |
| `GET /mios/status` | D61 |
| Callback `POST /callbacks/workflow-executions/{id}/status` + secret | D59 / D60 |
| DAG reports started/completed/failed | D67 / `#59` |
| Seeded workflow `download_cfpb_all` | D63 / Alembic |
| Pluggable store (default SQLite) | D75 / `#116` |

Gaps for this story: a **single documented runbook**, plus a **repeatable smoke** that CI/local can run when full Airflow is unavailable.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Docs-only checklist for the full UI→Airflow path | Meets “documented”; weak on “automated where practical” |
| B (chosen) | Docs for the full path **plus** an API-level smoke script (callback → DB → `/mios/status`) runnable without Airflow; optional full mode when containers are up | Proves non-invented status from the active DB in CI/local; full Airflow remains a manual/opt-in checklist |
| C | Playwright/Cypress UI E2E in CI with live Airflow | Heavy; flakes; Airflow not always in CI; out of proportion for M03 |

## Design

### 1. Happy-path runbook (human)

Add `docs/local-admin-e2e-happy-path.md` covering SQLite-first:

1. **Prereqs:** `.env` with `CCA_CALLBACK_SECRET`, Airflow vars as needed; default store = SQLite (unset `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` per D75).
2. **Start runtime:** `npm run local:containers:all:start` (Airflow + deps) → `npm run local:api:migrate` → `npm run local:portal:admin:with-api` (or API + portal separately).
3. **UI:** open DataSets → Imports → pick MIO / `download_cfpb_all` → **Start** → **Refresh**.
4. **Expect:** execution/ingest status moves `requested` → `started` → `completed` (or `failed`) via Airflow callbacks; UI shows the same strings from `GET /mios/status` (no client-side inventing).
5. **Failure notes:** 502 `engine start failed` if Airflow down; 401 on callbacks if secret wrong; UI shows Middleware `detail` (#121).

Point from root / portal README with one line each.

### 2. Automated smoke (no invented status)

Add a root npm script, e.g. `local:e2e:happy-path:smoke`, invoking pytest for the CI gate, plus an optional live probe under `CICD/Local/` that talks to a **running** Middleware on `http://127.0.0.1:8000` (override via env). Live probe stays outside Middleware `scripts/` (D37 ctx-only signatures).

**Default mode (`api-callback`, CI-friendly):**

1. `GET /health` must be 200.
2. `GET /workflows` → find `download_cfpb_all` (or `CCA_E2E_WORKFLOW_NAME`).
3. Ensure a MIO exists for linking (seeded catalog / first MIO from `GET /mios/status`).
4. Create a `requested` execution + ingest the same way start would (prefer live `POST .../start` when Airflow accepts; otherwise use in-process DAO helpers **only inside the smoke script** when `CCA_E2E_SIMULATE=1` / Airflow unavailable — never expose a new public API).
5. `POST` callback `started`, then `completed`, with `X-Callback-Secret` from env.
6. After each step, `GET /mios/status` and assert `latest_ingest.status` / execution `status` equal the **exact** strings just written (`started`, then `completed`) — fail if missing/null/wrong.
7. Exit non-zero on any inventable drift (empty status, unexpected enum, HTTP error without asserting detail).

**Optional full mode (`full`):** require Airflow up; `POST /start` must return 202; poll `/mios/status` until `started` then `completed`/`failed` within a timeout. Document that CI does **not** require this mode.

No new facades, routers, or portal chrome (D64 / YAGNI). Portal unit tests from #121 already cover error text; this smoke covers the DB-backed status round-trip.

### 3. Tests / verification

| Check | How |
|---|---|
| Smoke script unit-ish | Prefer a pytest that imports shared helpers **or** run the script against the existing TestClient/fixtures if wiring is cheap; otherwise document “API must be up” and gate npm script on `/health` |
| Portal / API lint | Unchanged; run `local:api:test` / `local:portal:admin:test` if any code shared |
| Manual | Follow the runbook once on SQLite |

### 4. Out of scope

- Postgres / Mongo DoD matrix (`#123`)
- New Middleware facades or portal features
- Inventing or mapping status enums in the UI
- Making live Airflow mandatory in GitHub Actions

## Acceptance mapping

| Acceptance | Deliverable |
|---|---|
| Documented steps | `docs/local-admin-e2e-happy-path.md` + README pointers |
| Status via callbacks | Smoke posts D60 callbacks; asserts `/mios/status` |
| Active DB (SQLite first) | Default D75 profile; runbook states SQLite first |

## Self-review

- No TBD placeholders; simulate path is explicit for CI without Airflow.
- Does not contradict D71/D72 (UI still read-only for status).
- Scope is docs + smoke + npm script only.
