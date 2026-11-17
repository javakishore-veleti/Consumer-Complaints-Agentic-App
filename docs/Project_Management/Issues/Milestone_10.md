# Milestone M10 - Local stack polish

**Scope:** Local DX after M09 — compose port conflicts, smoke path, and localhost runbook clarity. Cloud = M90.

**Status: in progress.**

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
| 8 | #215 | M10-0008 | Story | Runbook: functional ingest heading + why Mongo |
| 9 | #216 | M10-0009 | Story | Runbook: functional index headings + local embedding how-to |
| 10 | #217 | M10-0010 | Story | Runbook: functional Definition of Done checklist |
| 11 | #218 | M10-0011 | Story | Runbook: say localhost not “this machine” (GitHub-readable) |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Completed |
|---|---|---|---|---|
| #208 | 1–4 | Chroma host `:8100` | Done | 2026-11-16 |
| #209 | 1–4 | local `.env` bootstrap | Done | 2026-11-16 |
| #210 | 1–4 | runbook created under `docs/Runbooks/Localhost/` | Done | 2026-11-16 |
| #211 | 1–4 | fixed `CCA_CALLBACK_SECRET` | Done | 2026-11-16 |
| #212 | 1 | `/ccaa-story-start 212` | Done | 2026-11-16 |
| #212 | 2 | design spec (D95) | Done | 2026-11-16 |
| #212 | 3 | TDD compose mount + implement | Done | 2026-11-16 |
| #212 | 4 | `/ccaa-commit-push 212` | Done | 2026-11-16 |
| #213 | 1–4 | Sync secrets subsection + objective | Done | 2026-11-16 |
| #214 | 1–4 | functional headings (MIO language) | Done | 2026-11-16 |
| #215 | 1–4 | ingest why Mongo / what happens | Done | 2026-11-16 |
| #216 | 1–4 | index headings + `hash_embedding` how/where | Done | 2026-11-16 |
| #217 | 1–4 | functional Definition of Done | Done | 2026-11-16 |
| #218 | 1–4 | localhost wording (not “this machine”) | Done | 2026-11-16 |

## 3. Notes

- Chroma host default **8100** → container 8000; Middleware stays **8000**.
- Runbook: `docs/Runbooks/Localhost/3m-pgvector-chroma.md`.
- CFPB imports: `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` (D95 / #212).
- Local embeddings: `hash_embedding` in `Middleware/Airflow-dags/ccaa/vector_index.py` (dim 32; no neural model).
