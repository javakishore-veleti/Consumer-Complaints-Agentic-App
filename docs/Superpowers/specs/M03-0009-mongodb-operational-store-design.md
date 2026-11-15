# M03-0009 (#119) MongoDB operational store via .env (DAO/factory seam)

Decisions: **D79** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (builds on D45, D64, D75–D77). Decided without the user present (unattended story #119); review and reverse if needed.

## Goal

With only `.env` selecting MongoDB (`CCA_OPERATIONAL_STORE=mongodb` + `CCA_MONGO_OPERATIONAL_URL`), the Admin UI → API → Airflow → callback path works without SQLite or Postgres. `DaoObjectsFactory` (D45) registers Mongo DAO implementations for every admin DAO on that profile. Switching back to SQLite or Postgres remains an `.env`-only change.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | pymongo collections (one per admin table name); Mongo DAO classes under `dao/impl/mongo/`; factory branch on `operational_store`; bootstrap indexes + same fixed seed ids as Alembic; skip Alembic when store is mongodb | Matches D75 seam; no SQLAlchemy for this profile; clear `.env` switch |
| B | Mongo via SQLAlchemy dialect / ODM | Awkward; would still need separate seed/index story; fights D75 “not through create_engine” |
| C | New facade packages per backend | Violates D64 |

## D79 — Mongo operational store contract

1. **Select:** `CCA_OPERATIONAL_STORE=mongodb` and `CCA_MONGO_OPERATIONAL_URL=mongodb://…/db` (database name from the URI path). `CCA_DB_URL` is unused for the operational engine on this profile (D75).
2. **Factory:** `DaoObjectsFactory.init()` registers Mongo DAO impls for AppWf, AppWfExecLog, Dataset, DatasetLocation, Mio, MioDataset, MioIngestLog, and Transaction when store is `mongodb`; lazy-import so `pymongo` is only required for that profile.
3. **Documents:** one collection per admin table (`app_workflows`, `app_workflows_exec_log`, `datasets`, `datasets_location`, `mios`, `mios_datasets`, `mios_ingest_log`). Document field `id` (string UUID) is the business key; `_id` equals `id`. Timestamps stored as UTC datetimes.
4. **Indexes:** unique indexes mirror SQL unique constraints (workflow_name; dataset name/code; mio name; location composites; mios_datasets mio+dataset). Created by bootstrap, not Alembic.
5. **Seed:** bootstrap inserts the same fixed catalog + workflow rows as Alembic `0006`/`0008`/`0009` when the collections are empty (idempotent upsert by fixed id).
6. **Transactions (D39):** Mongo `TransactionDao` uses a process-local handle that applies writes immediately under a shared lock and keeps before-images for rollback. Works on a standalone local mongod (no replica-set requirement for DoD). Multi-document Mongo transactions remain a future hardening option.
7. **Startup:** `run_app.sh start` skips `alembic upgrade` when `CCA_OPERATIONAL_STORE=mongodb` and runs Mongo bootstrap instead. API start otherwise unchanged.
8. **Verification:** `tests/test_mongodb_operational_store.py` — always runs against an in-process mongomock (or equivalent) client; optional `CCA_TEST_MONGO_OPERATIONAL_URL` exercises a real Mongo. Smoke: HTTP start-workflow + callback leave docs readable in `app_workflows_exec_log` / `mios_ingest_log`.
9. **No new facade packages (D64).** SQLite/Postgres paths unchanged (D76/D77).

## Docs

- `.env.example` Profile 3: remove “until #119” note; add optional `docker compose` / URI example and test command.
- ARCHITECTURE §6: Mongo operational DAOs are implemented (D79).
- DESIGN.md: D78.

## Out of scope

- Lite npm/docker profiles (#120).
- DoD matrix (#123).
- Complaint-document Mongo (D10) — separate from operational profile.
- Changing Admin UI code.

## Self-review

- No placeholders; seed ids match Alembic.
- Does not contradict D75; replaces the fail-fast hook with real registration.
- Switch back to SQLite/Postgres is still env-only.
