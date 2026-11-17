# Milestone M10 - Local stack polish

**Scope:** Local DX after M09 — compose port conflicts and smoke-path friction. Cloud = M90.

**Status: in progress** (#208/#209 done; #210 closing with runbook).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #208 | M10-0001 | Story | Chroma host port default must not collide with Middleware :8000 |
| 2 | #209 | M10-0002 | Story | Bootstrap local Middleware .env for live smoke |
| 3 | #210 | M10-0003 | Story | Localhost runbook: 3-month CFPB → pgvector + Chroma |
| 4 | #211 | M10-0004 | Story | Document fixed localhost CCA_CALLBACK_SECRET |
| 5 | #212 | M10-0005 | Story | Fix localhost LOCAL_DATA_PATH_CFPB + mount into Airflow |
| 6 | #213 | M10-0006 | Story | Runbook: elevate Sync secrets to titled step with objective |
| 7 | #214 | M10-0007 | Story | Runbook: functional headings for operator steps |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #208 | implement + ship | Chroma host `:8100` | Done | 2026-11-16 |
| #209 | local `.env` bootstrap | git-ignored `.env` on machine | Done | 2026-11-16 |
| #210 | 1 | `/ccaa-story-start 210` | Done | 2026-11-16 |
| #210 | 2 | writing-plans (runbook outline) | Done | 2026-11-16 |
| #210 | 3 | implement `docs/Runbooks/Localhost/3m-pgvector-chroma.md` | Done | 2026-11-16 |
| #210 | 4 | `/ccaa-commit-push 210` | Done | 2026-11-16 |
| #211 | 1–4 | fixed local callback secret docs + .env.example | Done | 2026-11-16 |
| #212 | 1 | `/ccaa-story-start 212` | Done | 2026-11-16 |
| #212 | 2 | brainstorming / design spec | Done | 2026-11-16 |
| #212 | 3 | TDD (compose mount test) + implement | Done | 2026-11-16 |
| #212 | 4 | `/ccaa-commit-push 212` | Done | 2026-11-16 |
| #213 | 1–4 | runbook Sync secrets subsection + objective | Done | 2026-11-16 |
| #214 | 1–4 | functional Consumer Complaint Datasets headings | Done | 2026-11-16 |

## 3. Notes

- Chroma host default **8100** → container 8000; Middleware stays **8000**.
- Runbook: `docs/Runbooks/Localhost/3m-pgvector-chroma.md`.
- CFPB imports: `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` (D95 / #212).
