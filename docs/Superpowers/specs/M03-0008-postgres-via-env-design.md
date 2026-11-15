# M03-0008 (#118) Postgres via .env: migrate and verify same APIs

Decisions: **D77** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (builds on D23, D33, D75, D76). Decided without the user present (unattended story #118); review and reverse if needed.

## Goal

With only `.env` pointing `CCA_DB_URL` at a local Postgres, migrations and the same admin APIs work. Prove start-workflow + callback writes are visible in Postgres. Keep `tests/test_postgres.py` green when `CCA_TEST_POSTGRES_URL` is set (CI already runs it).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Document the `.env` switch + optional `docker run` Postgres; harden `test_postgres.py` with HTTP start+callback smoke reading admin schema via SQL; no new compose (defer lite profiles to #120) | Matches acceptance; avoids colliding with #120 on package.json/docker |
| B | Add `CICD/Local/postgres` compose + npm scripts now | Overlaps #120; more surface than needed for this story |
| C | Separate Postgres-only DAO path | Violates D75/D64 |

## D77 — Postgres via `.env` contract

1. Set `CCA_DB_URL=postgresql+psycopg://…` (optional `CCA_OPERATIONAL_STORE=postgres`). Same SQLAlchemy DAOs and Alembic migrations as SQLite (D23, D75).
2. Optional local container (example): `docker run -d --name cca-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=cca -p 5432:5432 postgres:16` then set `CCA_DB_URL` accordingly; run `alembic upgrade head` / `run_app.sh start`.
3. Verification: `CCA_TEST_POSTGRES_URL=… uv run pytest tests/test_postgres.py` (CI sets this against a Postgres 16 service). Includes upgrade/downgrade and DAO coverage (D33).
4. Smoke: HTTP `POST /workflows/{id}/start` (Airflow mocked) + `POST /callbacks/.../status` leave rows readable in `consumer_comp_admin_db.app_workflows_exec_log` / `mios_ingest_log` on Postgres.
5. No new facade packages (D64). Mongo operational store remains #119. npm/docker lite profiles remain #120.

## Docs

- `.env.example` Profile 2 gains the `docker run` one-liner and the test command.
- ARCHITECTURE §6 / §8: optional Postgres container + `CCA_TEST_POSTGRES_URL` verification note.

## Out of scope

- Mongo (#119), lite npm/docker profiles (#120), Admin UI (#121/#122), DoD matrix (#123).

## Self-review

- No placeholders; compose deferred to #120 by name.
- Does not contradict D33/D75; adds the M03 `.env` path proof for Postgres.
