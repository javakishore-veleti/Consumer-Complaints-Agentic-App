# M03-0008 (#118) Postgres via .env Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Document and verify Postgres as the operational store via `.env` only — migrations, same APIs, start+callback smoke; CI/`test_postgres.py` remain the verification path.

**Architecture:** Same SQLAlchemy DAOs + Alembic (D75). **D77** locks the `.env` + optional container + test URL contract. Add HTTP start+callback smoke in `test_postgres.py`.

**Tech Stack:** Python, pytest, Postgres 16, psycopg, Alembic, FastAPI TestClient.

Spec: `docs/Superpowers/specs/M03-0008-postgres-via-env-design.md`. Decision: **D77**.

## Global Constraints

- Do not edit package.json / CICD lite profiles (#120).
- Do not implement Mongo (#119).
- No new facade packages (D64).
- Commit with `/ccaa-commit-push 118`. Author `javakishore-veleti`; strip AI trailers.
- Next free decision **D78+**.

## File Structure

| File | Responsibility |
|---|---|
| Spec + plan under `docs/Superpowers/` | Design / plan |
| `DESIGN.md` | D77 |
| `ARCHITECTURE.md` | Optional Postgres container + verification |
| `.env.example` | docker run + test command under Profile 2 |
| `tests/test_postgres.py` | HTTP start+callback smoke; fixture sets `CCA_OPERATIONAL_STORE=postgres` |
| `Milestone_03.md` | Workflow; next decision D78+ |

---

### Task 1: Docs + D77

- [ ] Add D77 after D76; update `.env.example` Profile 2; ARCHITECTURE note; Milestone D78+.
- [ ] Commit: `M03-0008 #118: document Postgres via .env (D77)`

### Task 2: Postgres HTTP smoke (TDD)

- [ ] In `postgres` fixture: `monkeypatch.setenv("CCA_OPERATIONAL_STORE", "postgres")`.
- [ ] Add `test_start_workflow_and_callback_persist_on_postgres` (mock Airflow, HTTP start + callback, assert statuses via SQL on admin schema).
- [ ] Run with `CCA_TEST_POSTGRES_URL` if a local Postgres is available; otherwise rely on CI.
- [ ] Commit: `M03-0008 #118: smoke start+callback on Postgres`

### Task 3: Verify and finish

- [ ] `npm run local:api:lint` / `npm run local:api:test` (Postgres tests skip without URL).
- [ ] PR → main, green CI (must exercise Postgres service), merge, `/ccaa-story-complete 118`.
