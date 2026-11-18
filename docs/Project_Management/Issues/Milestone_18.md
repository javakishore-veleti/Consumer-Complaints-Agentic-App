# Milestone M18 - Local Mongo Compass auth docs

**Scope:** Document MongoDB Compass connection (`root` / `changeme-local` / `authSource=admin`) in root README and the 3m localhost runbook so operators are not blocked by an empty Databases list after first-boot init.

**Status: Closed.** Stories left to build: 0. Stories already done: 1 (#266).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #266 | M18-0001 | Story | Document MongoDB Compass auth in README + 3m runbook |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #266 | 1 | `/ccaa-story-start 266` | Done | 2026-11-17 23:01 | 2026-11-17 23:01 |
| #266 | 2 | brainstorm → worktree → plan → TDD → implement (docs) | Done | 2026-11-17 23:02 | 2026-11-17 23:02 |
| #266 | 3 | `/ccaa-commit-push 266` | Done | 2026-11-17 23:02 | 2026-11-17 23:02 |
| #266 | 4 | `/ccaa-story-complete 266` | Done | 2026-11-17 23:02 | 2026-11-17 23:02 |

## 3. Notes

- First-boot init (#259) already creates `consumer_comp_db.complaints`; Compass without auth looks empty.
- Docs-only story; no Middleware / Portals / DAG changes.
