# Milestone M17 - 3-month Admin path: ingest + runbook

**Scope:** End-to-end on **Customer complaints 3 months 2026** only — filter → Mongo ingest → vector indexes. Fix empty DB Ingest after filter; rewrite localhost 3m runbook with **no All-MIO detour**.

**Status: Open.** Stories left to build: 4. Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #245 | M17-0001 | Story | 3-month MIO: bind ingest+index; filter registers landed run; DB Ingest can start |
| 2 | #244 | M17-0002 | Story | Rewrite 3m localhost runbook: 3-month MIO only (filter → Mongo → indexes) |
| 3 | #246 | M17-0003 | Story | Rename Admin UI brand from CC Admin to Consumer Complaints Administration |
| 4 | #247 | M17-0004 | Story | Dataset tags table (SQL-filterable, ≥5000 tags) + optional comment |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #245 | 1 | `/ccaa-story-start 245` | Done | 2026-11-17 19:39 |
| #245 | 2 | brainstorm → worktree → plan → TDD → implement | In progress | 2026-11-17 19:39 |
| #245 | 3 | `/ccaa-commit-push 245` | Not started | |
| #245 | 4 | `/ccaa-story-complete 245` | Not started | |
| #244 | 1 | `/ccaa-story-start 244` | Not started | |
| #244 | 2 | rewrite `docs/Runbooks/Localhost/3m-pgvector-chroma.md` (3m MIO only) | Not started | |
| #244 | 3 | `/ccaa-commit-push 244` | Not started | |
| #244 | 4 | `/ccaa-story-complete 244` | Not started | |
| #246 | 1 | `/ccaa-story-start 246` | Not started | |
| #246 | 2 | replace CC Admin chrome/titles with Consumer Complaints Administration | Not started | |
| #246 | 3 | `/ccaa-commit-push 246` | Not started | |
| #246 | 4 | `/ccaa-story-complete 246` | Not started | |

## 3. Notes

- Operator pain: filter completed; DB Ingest shows no import runs and empty ingest dropdown on the 3-month card (only `filter_cfpb_3_months` bound).
- M17-0001 must make the **3-month** card usable for ingest+index; M17-0002 documents that path only.
- Operator rule: every Imports **lander** (filter, download, …) → own `YYYY-MM-DD-HH-MM-SS` + DB row so a 3-month run stays distinct from a 1-year run.
