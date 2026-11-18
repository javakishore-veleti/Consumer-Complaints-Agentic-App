# Milestone M17 - 3-month Admin path: ingest + runbook

**Scope:** End-to-end on **Customer complaints 3 months 2026** only — filter → Mongo ingest → vector indexes. Fix empty DB Ingest after filter; rewrite localhost 3m runbook with **no All-MIO detour**.

**Status: Closed.** Stories left to build: 0. Stories already done: 11 (Phase 0 baseline 3 + #245 + #255 + #257 + #260 + #259 + #244 + #246 + #247).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #245 | M17-0001 | Story | 3-month MIO: bind ingest+index; filter registers landed run; DB Ingest can start |
| 2 | #248 | M17-0005 | Story | Per-MIO default split source folders (3/6/9/12/all months) |
| 3 | #251 | M17-0006 | Story | CI Postgres bindings count (12) |
| 4 | #253 | M17-0007 | Story | Fix IndentationError in index_cfpb_* DAGs |
| 5 | #255 | M17-0008 | Story | DB Ingest UX: clarify import-run selection; scale past large run lists |
| 6 | #257 | M17-0009 | Story | Airflow image: install pymongo for Mongo ingest DAGs |
| 7 | #260 | M17-0011 | Story | Wrapper finalize reports failed (state=None) after successful ingest |
| 8 | #259 | M17-0010 | Story | Mongo init: create consumer_comp_db + complaints on first boot |
| 9 | #244 | M17-0002 | Story | Rewrite 3m localhost runbook: 3-month MIO only (filter → Mongo → indexes) |
| 10 | #246 | M17-0003 | Story | Rename Admin UI brand from CC Admin to Consumer Complaints Administration |
| 11 | #247 | M17-0004 | Story | Dataset tags table (SQL-filterable, ≥5000 tags) + optional comment |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #245 | 1 | `/ccaa-story-start 245` | Done | 2026-11-17 19:47 | 2026-11-17 19:47 |
| #245 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 19:47 | 2026-11-17 19:47 |
| #245 | 3 | `/ccaa-commit-push 245` | Done | 2026-11-17 19:47 | 2026-11-17 19:47 |
| #245 | 4 | `/ccaa-story-complete 245` | Done | 2026-11-17 19:47 | 2026-11-17 19:47 |
| #255 | 1 | `/ccaa-story-start 255` | Done | 2026-11-17 20:18 | 2026-11-17 20:18 |
| #255 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 20:18 | 2026-11-17 20:22 |
| #255 | 3 | `/ccaa-commit-push 255` | Done | 2026-11-17 20:22 | 2026-11-17 20:23 |
| #255 | 4 | `/ccaa-story-complete 255` | Done | 2026-11-17 20:23 | 2026-11-17 20:23 |
| #257 | 1 | `/ccaa-story-start 257` | Done | 2026-11-17 20:46 | 2026-11-17 20:46 |
| #257 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 20:46 | 2026-11-17 20:48 |
| #257 | 3 | `/ccaa-commit-push 257` | Done | 2026-11-17 20:48 | 2026-11-17 20:49 |
| #257 | 4 | `/ccaa-story-complete 257` | Done | 2026-11-17 20:49 | 2026-11-17 20:49 |
| #260 | 1 | `/ccaa-story-start 260` | Done | 2026-11-17 21:51 | 2026-11-17 21:51 |
| #260 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 21:51 | 2026-11-17 21:55 |
| #260 | 3 | `/ccaa-commit-push 260` | Done | 2026-11-17 21:55 | 2026-11-17 21:54 |
| #260 | 4 | `/ccaa-story-complete 260` | Done | 2026-11-17 21:54 | 2026-11-17 21:54 |
| #259 | 1 | `/ccaa-story-start 259` | Done | 2026-11-17 21:54 | 2026-11-17 21:54 |
| #259 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 21:54 | 2026-11-17 21:56 |
| #259 | 3 | `/ccaa-commit-push 259` | Done | 2026-11-17 21:56 | 2026-11-17 21:56 |
| #259 | 4 | `/ccaa-story-complete 259` | Done | 2026-11-17 21:56 | 2026-11-17 21:56 |
| #244 | 1 | `/ccaa-story-start 244` | Done | 2026-11-17 21:56 | 2026-11-17 21:56 |
| #244 | 2 | rewrite `docs/Runbooks/Localhost/3m-pgvector-chroma.md` (3m MIO only) | Done | 2026-11-17 21:56 | 2026-11-17 21:58 |
| #244 | 3 | `/ccaa-commit-push 244` | Done | 2026-11-17 21:58 | 2026-11-17 21:58 |
| #244 | 4 | `/ccaa-story-complete 244` | Done | 2026-11-17 21:58 | 2026-11-17 21:58 |
| #246 | 1 | `/ccaa-story-start 246` | Done | 2026-11-17 21:56 | 2026-11-17 21:56 |
| #246 | 2 | replace CC Admin chrome/titles with Consumer Complaints Administration | Done | 2026-11-17 21:58 | 2026-11-17 21:59 |
| #246 | 3 | `/ccaa-commit-push 246` | Done | 2026-11-17 21:59 | 2026-11-17 21:59 |
| #246 | 4 | `/ccaa-story-complete 246` | Done | 2026-11-17 21:59 | 2026-11-17 21:59 |
| #247 | 1 | `/ccaa-story-start 247` | Done | 2026-11-17 22:00 | 2026-11-17 22:00 |
| #247 | 2 | brainstorm → worktree → plan → TDD → implement | Done | 2026-11-17 22:00 | 2026-11-17 22:15 |
| #247 | 3 | `/ccaa-commit-push 247` | Done | 2026-11-17 22:15 | 2026-11-17 22:15 |
| #247 | 4 | `/ccaa-story-complete 247` | Done | 2026-11-17 22:15 | 2026-11-17 22:15 |

## 3. Notes

- Operator pain: filter completed; DB Ingest shows no import runs and empty ingest dropdown on the 3-month card (only `filter_cfpb_3_months` bound).
- M17-0001 must make the **3-month** card usable for ingest+index; M17-0002 documents that path only.
- Operator rule: every Imports **lander** (filter, download, …) → own `YYYY-MM-DD-HH-MM-SS` + DB row so a 3-month run stays distinct from a 1-year run.
- Per-MIO default folders (#248): e.g. `Downloads/temp/complaints_split_3_months_data` (and 6/9/12/all).
