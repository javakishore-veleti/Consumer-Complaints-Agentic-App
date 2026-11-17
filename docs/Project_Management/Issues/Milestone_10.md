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
| 12 | #219 | M10-0012 | Story | Sync secrets: optional unset upsert names must not 422 |
| 13 | #220 | M10-0013 | Story | Runbook: Airflow Variables check URL + redacted screenshot |
| 14 | #221 | M10-0014 | Story | Local Airflow: DAGs unpaused by default |
| 15 | #222 | M10-0015 | Story | Runbook: drop GitHub issue jargon for operators |
| 16 | #223 | M10-0016 | Story | Runbook 3m: reframe full download as filter prerequisite only |
| 17 | #224 | M10-0017 | Story | Runbook 3m: stage split folder, not monolith zip + filter |
| 18 | #225 | M10-0018 | Story | Runbook 0.1: stop containers before start |
| 19 | #226 | M10-0019 | Story | Fix middleware-ci: unpaused DAG test + upsert parse signature |
| 20 | #227 | M10-0020 | Story | Runbook 0.1: copy-paste safe commands (no shell comments) |
| 21 | #228 | M10-0021 | Story | Default CCA_CFPB_SPLIT_SOURCE_PATH to Downloads/temp/complaints_split |
| 22 | #237 | M10-0022 | Story | Rewrite 3m runbook around Customer complaints 3 months 2026 |
| 23 | #238 | M10-0023 | Story | filter_cfpb_3_months: folder or single file input |

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
| #219 | 1 | `/ccaa-story-start 219` | Done | 2026-11-16 20:41 |
| #219 | 2 | design spec (D96 / `# optional` → `skipped`) | Done | 2026-11-16 20:41 |
| #219 | 3 | TDD + implement optional upsert + runbook §0.4 | Done | 2026-11-16 20:41 |
| #219 | 4 | `/ccaa-commit-push 219` | Done | 2026-11-16 20:42 |
| #219 | 5 | `/ccaa-story-complete 219` | Done | 2026-11-16 20:42 |
| #220 | 1–4 | Variables URL + redacted screenshot in runbook §0.4 | Done | 2026-11-16 20:48 |
| #221 | 1–4 | `DAGS_ARE_PAUSED_AT_CREATION=false` + runbook §0.5 | Done | 2026-11-16 20:48 |
| #222 | 1–4 | runbook plain language + npm stop/start (no `#221` / raw docker) | Done | 2026-11-17 09:22 |
| #223 | 1–4 | §1 = prerequisite source zip; Imports accordion path (no MIO nav) | Done | 2026-11-17 09:28 |
| #224 | 1–4 | split-folder stage path + widen Airflow datasets mount | Done | 2026-11-17 09:31 |
| #225 | 1–4 | §0.1 stop then start (npm scripts) | Done | 2026-11-17 09:33 |
| #226 | 1–4 | CI: compose-only unpaused assert; D37 upsert parse inline | Done | 2026-11-17 09:37 |
| #227 | 1–4 | §0.1 npm lines without trailing # / parentheses | Done | 2026-11-17 09:40 |
| #228 | 1–4 | default split path Downloads/temp/complaints_split + mount + re-Sync docs | Done | 2026-11-17 09:44 |
| #237 | 1–4 | 3m runbook centered on Customer complaints 3 months 2026 | Done | 2026-11-17 13:20 |
| #238 | 1 | `/ccaa-story-start 238` | Done | 2026-11-17 14:41 |
| #238 | 2 | brainstorming / design (folder or file) | In progress | 2026-11-17 14:41 |
| #238 | 3 | `/using-git-worktrees` | Planned | - |
| #238 | 4 | `/writing-plans` | Planned | - |
| #238 | 5 | TDD + implement filter folder-or-file | Planned | - |
| #238 | 6 | `/ccaa-commit-push` after tasks | Planned | - |
| #238 | 7 | `/ccaa-story-complete 238` | Planned | - |

## 3. Notes

- Chroma host default **8100** → container 8000; Middleware stays **8000**.
- Runbook: `docs/Runbooks/Localhost/3m-pgvector-chroma.md`.
- CFPB imports: `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` (D95 / #212).
- Local embeddings: `hash_embedding` in `Middleware/Airflow-dags/ccaa/vector_index.py` (dim 32; no neural model).
- Sync secrets (D96 / #219): `# optional` in upsert list → empty env is `skipped` (not 422); `CCA_DB_URL` + `CCA_CFPB_SPLIT_SOURCE_PATH` optional on localhost.
- Runbook §0.4 (#220): check http://127.0.0.1:8080/variables + redacted screenshot asset.
- Local Airflow (#221): `DAGS_ARE_PAUSED_AT_CREATION=false` — DAGs enabled on fresh stack.
- 3m runbook (#224): primary path is split-folder stage via `CCA_CFPB_SPLIT_SOURCE_PATH` (not monolith + filter); Airflow mounts whole `complains_datasets` tree.
