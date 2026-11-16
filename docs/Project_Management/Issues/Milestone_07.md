# Milestone M07 - Pluggable local vector Storage Layer

**Scope:** After M06 SoT path is usable. Diagram **STORAGE LAYER**: SoT → indexer → pluggable local vector backends. First real backend **pgvector** (5.25-aligned). Keep JSONL for CI. Plain Python batches first; PySpark-ready seam. Cloud vector SaaS = M90+.

**Status: done.** 1 epic, 3 features, 4 stories. 0 stories are left to build; 7 stories are already done (3 Phase 0 + 4).

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
| #179 | 1 | `/ccaa-story-start 179` | Done | 2026-11-16 15:00 | 2026-11-16 15:00 |
| #179 | 2 | `/brainstorming Story #179: D92 pluggable Storage Layer` | Done | 2026-11-16 15:00 | 2026-11-16 15:05 |
| #180 | 1 | `/ccaa-story-start 180` | Done | 2026-11-16 15:00 | 2026-11-16 15:00 |
| #181 | 1 | `/ccaa-story-start 181` | Done | 2026-11-16 15:00 | 2026-11-16 15:00 |
| #182 | 1 | `/ccaa-story-start 182` | Done | 2026-11-16 15:00 | 2026-11-16 15:00 |
| #179/#180/#181/#182 | 3–12 | worktree → plan → TDD → commit → PR → complete | Done | 2026-11-16 15:00 | 2026-11-16 15:07 |
| Feature #176 | 1 | `/ccaa-feature-complete 176` | Done | 2026-11-16 15:07 | 2026-11-16 15:07 |
| Feature #177 | 1 | `/ccaa-feature-complete 177` | Done | 2026-11-16 15:07 | 2026-11-16 15:07 |
| Feature #178 | 1 | `/ccaa-feature-complete 178` | Done | 2026-11-16 15:07 | 2026-11-16 15:07 |
| Epic #175 | 1 | `/ccaa-epic-complete 175` | Done | 2026-11-16 15:07 | 2026-11-16 15:07 |

## 4. Notes

- Spec: `docs/Superpowers/specs/M07-0005-pluggable-vector-storage-design.md` (D92)
- Env: `CCA_PGVECTOR_URL`; npm `local:containers:pgvector:*`; AppEndpoint `cfpb_index_mongo_to_pgvector`
- Next: **M08** retrieval ladder. Cloud remains **M90**.
