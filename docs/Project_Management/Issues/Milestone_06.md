# Milestone M06 - Split CFPB landing and complaint SoT batches

**Scope:** After M05. Local-only. Land **split** CFPB parts (`complaints_part_*.csv.zip` style) under catalog `LOCAL_DATA_PATH_*`, then batch-ingest into complaint **SoT** (Mongo primary). No hardcoded Downloads paths. No paid cloud.

**Status: done.** 1 epic, 2 features, 3 stories (all done). Decision **D91**.

## Contents

- [1. Build order](#1-build-order)
- [2. Grouped by epic/feature](#2-grouped-by-epicfeature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #169 | M06-0001 | Epic | Split CFPB landing and complaint SoT batches |
| 2 | #170 | M06-0002 | Feature | Land CFPB split parts under LOCAL_DATA_PATH |
| 3 | #172 | M06-0004 | Story | Catalog and DAG config for split-part CFPB landing |
| 4 | #173 | M06-0005 | Story | Download or stage CFPB split parts to local landing |
| 5 | #171 | M06-0003 | Feature | Batch ingest split parts into complaint SoT (Mongo) |
| 6 | #174 | M06-0006 | Story | Ingest DAG reads split parts into Mongo SoT in batches |

## 2. Grouped by epic/feature

```
Epic #169  M06-0001  Split CFPB landing and complaint SoT batches
|
+-- Feature #170  M06-0002  Land split parts
|     +-- #172  Catalog and DAG config for split-part landing
|     +-- #173  Download or stage split parts to local landing
|
+-- Feature #171  M06-0003  Batch SoT ingest (Mongo)
      +-- #174  Ingest DAG reads split parts into Mongo in batches
```

## 3. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #172 | 1 | `/ccaa-story-start 172` | Done | 2026-11-16 14:57 | 2026-11-16 14:57 |
| #172 | 2 | `/brainstorming Story #172: D91 split landing` | Done | 2026-11-16 14:57 | 2026-11-16 15:05 |
| #173 | 1 | `/ccaa-story-start 173` | Done | 2026-11-16 14:57 | 2026-11-16 14:57 |
| #174 | 1 | `/ccaa-story-start 174` | Done | 2026-11-16 14:57 | 2026-11-16 14:57 |
| #172/#173/#174 | 3–12 | worktree → plan → TDD → commit → PR → complete | Done | 2026-11-16 14:57 | 2026-11-16 15:10 |
| Feature #170 | 1 | `/ccaa-feature-complete 170` | Done | 2026-11-16 15:10 | 2026-11-16 15:10 |
| Feature #171 | 1 | `/ccaa-feature-complete 171` | Done | 2026-11-16 15:10 | 2026-11-16 15:10 |
| Epic #169 | 1 | `/ccaa-epic-complete 169` | Done | 2026-11-16 15:10 | 2026-11-16 15:10 |

## 4. Notes

- Spec: `docs/Superpowers/specs/M06-0004-split-cfpb-landing-sot-design.md`
- Env: `CCA_CFPB_SPLIT_SOURCE_PATH` → stage into `LOCAL_DATA_PATH_CFPB`; AppEndpoint `cfpb_stage_split_to_local`
- Next: **M07** Storage Layer (pgvector). Cloud remains **M90**.
