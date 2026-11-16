# Milestone M07 - Pluggable local vector Storage Layer

**Scope:** After M06 SoT path is usable. Diagram **STORAGE LAYER**: SoT → indexer → pluggable local vector backends. First real backend **pgvector** (5.25-aligned). Keep JSONL for CI. Plain Python batches first; PySpark-ready seam. Cloud vector SaaS = M90+.

**Status: planned.** 1 epic, 3 features, 4 stories.

## Contents

- [1. Build order](#1-build-order)
- [2. Grouped by epic/feature](#2-grouped-by-epicfeature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #175 | M07-0001 | Epic | Pluggable local vector Storage Layer |
| 2 | #176 | M07-0002 | Feature | Vector store adapter seam (JSONL retained for CI) |
| 3 | #179 | M07-0005 | Story | VectorStore adapter interface + JSONL adapter |
| 4 | #177 | M07-0003 | Feature | Local pgvector Storage Layer + index path |
| 5 | #180 | M07-0006 | Story | Local pgvector container profile and connection config |
| 6 | #181 | M07-0007 | Story | Index DAG writes SoT complaints into pgvector in batches |
| 7 | #178 | M07-0004 | Feature | Multi-target index catalog (AppEndpoints / mios_rags direction) |
| 8 | #182 | M07-0008 | Story | Seed multi-target index AppEndpoints (JSONL + pgvector) |

## 2. Grouped by epic/feature

```
Epic #175  M07-0001  Pluggable local vector Storage Layer
|
+-- Feature #176  M07-0002  Adapter seam + JSONL
|     +-- #179  VectorStore adapter + JSONL
|
+-- Feature #177  M07-0003  Local pgvector
|     +-- #180  pgvector container/profile + config
|     +-- #181  Index DAG SoT → pgvector batches
|
+-- Feature #178  M07-0004  Multi-target catalog
      +-- #182  Seed JSONL + pgvector AppEndpoints
```

## 3. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #179 | 1 | `/ccaa-story-start 179` | Planned | | |

## 4. Notes

- Refs: D53 `mios_rags`, D88 JSONL MVP, ScratchPad `5.25_advanced_rag_pipeline.ipynb` STORAGE LAYER.
- Retrieval ladder is **M08**, not this milestone.
