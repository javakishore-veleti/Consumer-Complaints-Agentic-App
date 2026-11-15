# M03-0007 (#117) SQLite-first operational store for admin schema

Decisions: **D76** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (builds on D23, D33, D45, D48, D51, D75). Decided without the user present (unattended story #117); review and reverse if needed.

## Goal

Make the M02 admin schema (workflows, catalog, ingest/exec logs) **fully reliable on SQLite as the default** operational store: Alembic migrations, SQLAlchemy DAOs, and the start-workflow + status-callback path all work with **no Postgres container**. Prove persistence by reading the SQLite files on disk, not only through DAOs.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Keep the existing SQLAlchemy + Alembic path (D23/D33/D75); add **D76** reliability contract; harden test isolation; add one SQLite file-level persistence test that chains migrate → start → callback → raw `sqlite3` reads | Smallest change; reuses M02 DAOs; acceptance without a new backend |
| B | Fork SQLite-only migrations / schema files separate from Postgres | Dual schemas drift; violates “same migrations” (D23); more code for no gain |
| C | New facade or store package for “sqlite admin” | Violates D64; unnecessary with D45/D75 |

## Current state (before this story)

| Piece | Today |
|---|---|
| Default URL | D75 → `sqlite:///{CCA_DATA_DIR}/operational.sqlite` |
| Attach schemas | `database.py` ATTACH one `.sqlite` file per schema name |
| Alembic | `env.py` sets `render_as_batch=True` on SQLite; `0007` uses `batch_alter_table`; `upgrade head` succeeds |
| Admin tables at head | `app_workflows`, `app_workflows_exec_log`, `datasets`, `datasets_location`, `mios`, `mios_datasets`, `mios_ingest_log` in `consumer_comp_admin_db.sqlite` |
| API tests | `data_dir` fixture migrates SQLite; start-workflow and callback suites pass |
| Gap | No single test asserts start + callback **rows in the SQLite files**; `data_dir` does not clear `CCA_OPERATIONAL_STORE` / `CCA_MONGO_OPERATIONAL_URL` |

## D76 — SQLite-first reliability contract

1. **Default local path needs no Postgres.** With `CCA_OPERATIONAL_STORE` and `CCA_DB_URL` unset, `alembic upgrade head` and the API use SQLite under `CCA_DATA_DIR` only.
2. **Migrations stay portable.** Use Alembic Python ops (D23). Any SQLite-unsafe ALTER uses `op.batch_alter_table` (already enabled via `render_as_batch` in `alembic/env.py`).
3. **Admin schema at head** lives in attached `consumer_comp_admin_db` (D48): the seven tables above; retired `system_datasets` / `data_ingest_log` stay absent after `0010` (D74).
4. **Start-workflow + callback persist to SQLite.** `POST /workflows/{id}/start` creates `app_workflows_exec_log` (and optional `mios_ingest_log`); `POST /callbacks/workflow-executions/{id}/status` updates those rows. Rows must be readable from `consumer_comp_admin_db.sqlite` via `sqlite3` after the calls.
5. **No new facade packages** (D64). Callers stay on DAO interfaces; SQLAlchemy impls remain for `sqlite` and `postgres` (D75).
6. **Out of scope:** Postgres DoD path (#118), Mongo operational DAOs (#119), npm/docker lite profiles (#120), Admin UI (#121/#122), full DoD matrix (#123).

## Test plan (acceptance mapping)

| Acceptance | Proof |
|---|---|
| `alembic upgrade head` on default SQLite | Existing `data_dir` / `test_schema.py`; keep green; optional explicit head-table list in new test |
| Existing API tests against SQLite | `npm run local:api:test` (Postgres suite remains skipped without container) |
| Start-workflow + callback persist to SQLite | New `tests/test_sqlite_admin_store.py`: mock Airflow start → POST start → POST callback → assert statuses/ids in the admin `.sqlite` file |

## Hardening

- `tests/conftest.py` `data_dir`: also clear `CCA_OPERATIONAL_STORE` and `CCA_MONGO_OPERATIONAL_URL` so a developer shell cannot force Mongo/Postgres into the default fixture.
- DESIGN.md gains **D76**; ARCHITECTURE §6 notes SQLite-first is verified for the M02 admin schema; Milestone note next free decision **D77+**.

## Self-review

- No placeholders; Postgres/Mongo deferred to named stories.
- Does not contradict D23/D75; tightens the default path.
- Scope is reliability + proof, not a backend rewrite.
