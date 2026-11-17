# Milestone M17 - 3-month Admin path: ingest + runbook

**Scope:** End-to-end on **Customer complaints 3 months 2026** only — filter → Mongo ingest → vector indexes. Fix empty DB Ingest after filter; rewrite localhost 3m runbook with **no All-MIO detour**.

**Status: Open.** Stories left to build: 2. Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #245 | M17-0001 | Story | 3-month MIO: bind ingest+index; filter registers landed run; DB Ingest can start |
| 2 | #244 | M17-0002 | Story | Rewrite 3m localhost runbook: 3-month MIO only (filter → Mongo → indexes) |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #245 | 1 | `/ccaa-story-start 245` | Not started | |
| #245 | 2 | brainstorm → worktree → plan → TDD → implement | Not started | |
| #245 | 3 | `/ccaa-commit-push 245` | Not started | |
| #245 | 4 | `/ccaa-story-complete 245` | Not started | |
| #244 | 1 | `/ccaa-story-start 244` | Not started | |
| #244 | 2 | rewrite `docs/Runbooks/Localhost/3m-pgvector-chroma.md` (3m MIO only) | Not started | |
| #244 | 3 | `/ccaa-commit-push 244` | Not started | |
| #244 | 4 | `/ccaa-story-complete 244` | Not started | |

## 3. Notes

- Operator pain: filter completed; DB Ingest shows no import runs and empty ingest dropdown on the 3-month card (only `filter_cfpb_3_months` bound).
- M17-0001 must make the **3-month** card usable for ingest+index; M17-0002 documents that path only.
