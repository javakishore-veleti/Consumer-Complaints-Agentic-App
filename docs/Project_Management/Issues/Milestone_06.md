# Milestone M06 - Split CFPB landing and complaint SoT batches

**Scope:** After M05. Local-only. Land **split** CFPB parts (`complaints_part_*.csv.zip` style) under catalog `LOCAL_DATA_PATH_*`, then batch-ingest into complaint **SoT** (Mongo primary). No hardcoded Downloads paths. No paid cloud.

**Status: planned.** 1 epic, 2 features, 3 stories.

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
| #172 | 1 | `/ccaa-story-start 172` | Planned | | |

## 4. Notes

- Product: `docs/PRODUCT_FEATURES.md` (split landing + SoT batches).
- Sample shape for understanding only: external `complaints_split` (never hardcode that path).
- Next: **M07** Storage Layer (pgvector / adapters). Cloud is **M90** (was M06).
