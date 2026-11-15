# M03-0009 (#119) MongoDB operational store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MongoDB-backed operational/admin store via `.env`, with DAO/factory swap-in so Admin UI → API → Airflow → callback works without SQLite/Postgres.

**Architecture:** pymongo collections under `dao/impl/mongo/`; `DaoObjectsFactory` registers Mongo impls when `operational_store=mongodb`; bootstrap indexes + Alembic-equivalent seeds; `run_app.sh` skips Alembic on this profile.

**Tech Stack:** Python 3.11+, pymongo, mongomock (dev/tests), FastAPI TestClient, pytest.

Spec: `docs/Superpowers/specs/M03-0009-mongodb-operational-store-design.md`. Decision: **D79**.

## Global Constraints

- Switching back to SQLite/Postgres must remain `.env`-only.
- No new facade packages (D64).
- Do not own lite npm/docker profiles (#120 may be parallel).
- Commit with `/ccaa-commit-push 119`. Author `javakishore-veleti`; strip AI trailers.
- Next free decision after D79 is **D80**.

## File Structure

| File | Responsibility |
|---|---|
| Spec + plan under `docs/Superpowers/` | Design / plan |
| `DESIGN.md` | D78 |
| `ARCHITECTURE.md` / `.env.example` | Profile 3 live |
| `pyproject.toml` | `pymongo`; `mongomock` in dev |
| `app/core/dao/impl/mongo/*` | Client, UoW, transaction, bootstrap, DAOs |
| `app/core/dao/objects_factory.py` | Register Mongo when profile=mongodb; `reset()` for tests |
| `run_app.sh` | Bootstrap instead of Alembic on mongodb |
| `tests/test_mongodb_operational_store.py` | Factory, DAO, start+callback smoke |
| `tests/test_operational_store_settings.py` | Replace reject-until-119 with registers-mongo |
| `Milestone_03.md` | Workflow; next decision D79+ |

---

### Task 1: Spec + D79 docs + deps

- [ ] Spec and plan committed on branch.
- [ ] Add D79; update ARCHITECTURE / `.env.example`; add pymongo (+ mongomock dev).
- [ ] Commit: `M03-0009 #119: document Mongo operational store (D79)`

### Task 2: Mongo client, UoW, TransactionDao, factory hook (TDD)

- [ ] Failing tests: factory registers Mongo DAOs; transaction rollback restores docs.
- [ ] Implement `mongo/client.py`, `unit_of_work.py`, `mongo_transaction_dao.py`, factory branch + `reset()`.
- [ ] Commit: `M03-0009 #119: register Mongo DAOs in factory`

### Task 3: Mongo admin DAOs + bootstrap (TDD)

- [ ] Implement Mongo DAOs for all seven admin tables; bootstrap indexes + seeds.
- [ ] Tests: create/get/list; start+callback smoke reading collections.
- [ ] `run_app.sh` mongodb bootstrap path.
- [ ] Commit: `M03-0009 #119: implement Mongo admin DAOs and bootstrap`

### Task 4: Verify and finish

- [ ] `npm run local:api:lint` / `npm run local:api:test`.
- [ ] PR → main, green CI, merge, `/ccaa-story-complete 119`, `/ccaa-feature-complete 112` if all four DB stories done.
