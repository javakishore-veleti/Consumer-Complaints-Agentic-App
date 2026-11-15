# Local Admin E2E DoD matrix (M03-0013 / #123)

Epic **#111** is not Done until the Admin happy path is proven on **SQLite**, **Postgres**, and **MongoDB**. Change only `.env` / profile between backends (D75–D79). Do **not** invent UI status — only values from `GET /mios/status` (D30 / #122).

## Automated matrix (CI / local, no Airflow)

From the repository root:

```bash
npm run local:e2e:dod-matrix:smoke
```

| Profile | npm target | What runs | When |
|---|---|---|---|
| SQLite | `local:e2e:dod-matrix:sqlite` | Happy-path start → callbacks → `/mios/status` (`test_e2e_happy_path_smoke`) | Always |
| Postgres | `local:e2e:dod-matrix:postgres` | Start → callback persist (`test_start_workflow_and_callback_persist_on_postgres`) | When `CCA_TEST_POSTGRES_URL` is set (CI); else **SKIP** unless `CCA_DOD_REQUIRE_POSTGRES=1` |
| MongoDB | `local:e2e:dod-matrix:mongodb` | Start → callback on mongomock (`test_start_workflow_and_callback_persist_on_mongo`) | Always |

CI already runs the full Middleware pytest suite with Postgres (`middleware-ci.yml`), so the Postgres cell is covered there. Locally without Postgres, the matrix exits 0 with Postgres **SKIP**.

Per-profile aliases:

```bash
npm run local:e2e:dod-matrix:sqlite
npm run local:e2e:dod-matrix:postgres   # needs CCA_TEST_POSTGRES_URL
npm run local:e2e:dod-matrix:mongodb
```

Live API probe (Middleware already up; any active profile):

```bash
npm run local:e2e:happy-path:probe
```

## Live checklist (optional Airflow + Admin UI)

For each profile below: set `.env`, start containers, migrate/bootstrap, then follow [local-admin-e2e-happy-path.md](./local-admin-e2e-happy-path.md). Record a row in the evidence table.

### SQLite (default)

1. Leave `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` unset (or `sqlite`).
2. `npm run local:containers:sqlite:start`
3. `npm run local:api:migrate`
4. `npm run local:portal:admin:with-api` → exercise Imports start/refresh.
5. Expect statuses `requested` → `started` → `completed`|`failed` from the API only.

### Postgres

1. `.env`: `CCA_OPERATIONAL_STORE=postgres` and `CCA_DB_URL=postgresql+psycopg://…` (see `.env.example`).
2. `npm run local:containers:postgres:start`
3. `npm run local:api:migrate`
4. Same UI path as SQLite.
5. Optional: `CCA_TEST_POSTGRES_URL=… npm run local:e2e:dod-matrix:postgres`

### MongoDB

1. `.env`: `CCA_OPERATIONAL_STORE=mongodb` and `CCA_MONGO_OPERATIONAL_URL=mongodb://…`
2. `npm run local:containers:mongodb:start`
3. Start API (`run_app.sh` bootstraps Mongo; skips Alembic).
4. Same UI path as SQLite.
5. CI-friendly without live Mongo: `npm run local:e2e:dod-matrix:mongodb` (mongomock).

## Evidence

| Date | Profile | Command / step | Result | Notes |
|---|---|---|---|---|
| 2026-11-15 | sqlite | `npm run local:e2e:dod-matrix:sqlite` | PASS | Mocked Airflow; `/mios/status` literals |
| 2026-11-15 | postgres | `npm run local:e2e:dod-matrix:smoke` (no URL) | SKIP | Covered in CI via `CCA_TEST_POSTGRES_URL` + `test_postgres` start+callback |
| 2026-11-15 | mongodb | `npm run local:e2e:dod-matrix:mongodb` | PASS | mongomock operational store |
| 2026-11-15 | matrix | `npm run local:e2e:dod-matrix:smoke` | PASS | sqlite PASS, postgres SKIP, mongodb PASS |

Live Airflow+UI rows may be added when a developer runs the optional checklist; they are not required for the CI gate.

## Related

- Spec: `docs/Superpowers/specs/M03-0013-dod-matrix-design.md`
- Happy path (active profile): `docs/local-admin-e2e-happy-path.md`
- Profiles (D78): `npm run local:containers:{sqlite,postgres,mongodb}:*`
- Epic #111 · Feature #115 · Story #123
