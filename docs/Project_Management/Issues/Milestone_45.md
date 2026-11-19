# Milestone M45 - Raw Iceberg ingest (Lift → raw.cfpb_complaints_*)

**Scope:** Implement Lift Zone → Apache Iceberg **Raw hydrate**. M40 (#310/#311) delivered Raw **docs** + Iceberg Spark **Docker** only — ingest was explicitly future. No Refined/Curated. No product/DAG code until each story is `/ccaa-story-start`.

**Status: Open.** Stories left to build: 4. Stories already done: 0.

**GitHub Milestone:** M45 - Raw Iceberg ingest (Lift → raw.cfpb_complaints_*) (api id 46)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #320 | M45-0001 | Story | Raw Iceberg: DDL + raw namespace table templates |
| 2 | #321 | M45-0002 | Story | Raw Iceberg: PySpark Lift→Raw hydrate for 3m |
| 3 | #322 | M45-0003 | Story | Raw Iceberg: Airflow DAG sensor/unzip/DQ/cleanup |
| 4 | #323 | M45-0004 | Story | Raw Iceberg: prove 3m count reconcile + SparkSQL |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #320 | 1 | story-start | Not started | — | — |
| #320 | 2 | worktree → implement | Not started | — | — |
| #320 | 3 | commit-push | Not started | — | — |
| #320 | 4 | story-complete | Not started | — | — |
| #321 | 1 | story-start | Not started | — | — |
| #321 | 2 | worktree → implement | Not started | — | — |
| #321 | 3 | commit-push | Not started | — | — |
| #321 | 4 | story-complete | Not started | — | — |
| #322 | 1 | story-start | Not started | — | — |
| #322 | 2 | worktree → implement | Not started | — | — |
| #322 | 3 | commit-push | Not started | — | — |
| #322 | 4 | story-complete | Not started | — | — |
| #323 | 1 | story-start | Not started | — | — |
| #323 | 2 | worktree → implement | Not started | — | — |
| #323 | 3 | commit-push | Not started | — | — |
| #323 | 4 | story-complete | Not started | — | — |

## 3. Status truth (do not skip)

| Layer | Status |
|---|---|
| Lift Zone zips | Operational |
| Raw architecture docs | Done (M40 #310) |
| Iceberg Spark Docker | Done (M40 #311) |
| Raw **ingest into Iceberg tables** | **Not done** — this milestone |
| Refined / Curated implement | Blocked until #323 proof |

## 4. Commands (skills)

- `/ccaa-story-start N` — required before any product/DAG work on story N
- worktree → implement (Superpowers)
- `/ccaa-commit-push N`
- `/ccaa-story-complete N`
- `/ccaa-milestone-log N` after each step
