# Milestone M19 - Mongo ingest index name alignment

**Scope:** Align `ingest_cfpb_all` / `mongo_ingest` unique index name with first-boot `uniq_complaint_id` so ingest does not fail `IndexOptionsConflict` after Mongo init (#259).

**Status: Open.** Stories left to build: 1 (#268). Stories already done: 0.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #268 | M19-0001 | Story | Align ingest Complaint ID index name with uniq_complaint_id |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #268 | 1 | `/ccaa-story-start 268` | Planned | - | - |
| #268 | 2 | brainstorm → worktree → plan → TDD → implement | Planned | - | - |
| #268 | 3 | `/ccaa-commit-push 268` | Planned | - | - |
| #268 | 4 | `/ccaa-story-complete 268` | Planned | - | - |

## 3. Notes

- Init: `CICD/Local/mongodb/docker-entrypoint-initdb.d/01-init-complaints.js` names the index `uniq_complaint_id`.
- Ingest previously called `create_index(..., unique=True)` without `name=`, which defaults to `Complaint ID_1`.
