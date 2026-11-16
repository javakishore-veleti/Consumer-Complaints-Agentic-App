# Milestone M09 - Extra local vector backends + pgvector consolidate

**Scope:** After M08. (1) **Consolidate pgvector** onto the existing local ops Postgres — retire separate `cca-pgvector`. (2) Add **Chroma** as its **own** opt-in container + index path. (3) Add **Redis Stack** as its **own** opt-in container (vector search + cache in that one Redis) + index path. (4) Seed **distinct** AppEndpoints/workflows per backend. JSONL stays CI default. Cloud SaaS = M90.

**Status: planned.** 1 epic, 4 features, 6 stories.

## Contents

- [1. Build order](#1-build-order)
- [2. Grouped by epic/feature](#2-grouped-by-epicfeature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #195 | M09-0001 | Epic | Extra local vector backends + consolidate pgvector |
| 2 | #196 | M09-0002 | Feature | Consolidate pgvector onto existing local Postgres |
| 3 | #200 | M09-0006 | Story | Migrate pgvector onto ops Postgres; retire separate pgvector compose |
| 4 | #197 | M09-0003 | Feature | Local Chroma Storage Layer (separate container) |
| 5 | #201 | M09-0007 | Story | Local Chroma container profile + connection config |
| 6 | #202 | M09-0008 | Story | Chroma VectorStore adapter + index DAG |
| 7 | #198 | M09-0004 | Feature | Local Redis Stack Storage Layer (separate container) |
| 8 | #203 | M09-0009 | Story | Local Redis Stack container (vector + cache) + config |
| 9 | #204 | M09-0010 | Story | Redis vector adapter + index DAG |
| 10 | #199 | M09-0005 | Feature | Distinct index AppEndpoints for Chroma and Redis |
| 11 | #205 | M09-0011 | Story | Seed distinct AppEndpoints + workflows for Chroma and Redis |

## 2. Grouped by epic/feature

```
Epic #195  M09-0001  Extra local vector backends + consolidate pgvector
|
+-- Feature #196  M09-0002  Consolidate pgvector → ops Postgres
|     +-- #200  Migrate pgvector; retire CICD/Local/pgvector
|
+-- Feature #197  M09-0003  Chroma (separate container)
|     +-- #201  chroma compose/profile + CCA_CHROMA_URL
|     +-- #202  chroma adapter + index_cfpb_chroma
|
+-- Feature #198  M09-0004  Redis Stack (separate container)
|     +-- #203  redis compose/profile + CCA_REDIS_URL
|     +-- #204  redis adapter + index_cfpb_redis
|
+-- Feature #199  M09-0005  Distinct AppEndpoints
      +-- #205  Seed cfpb_index_mongo_to_chroma + …_to_redis
```

## 3. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #200 | 1 | `/ccaa-story-start 200` | Planned | | |

## 4. Notes

- Containers: **postgres** (ops + pgvector) · **chroma** (own) · **redis** (own Stack: vector + cache). All opt-in profiles except when you need that backend.
- Distinct endpoints: `cfpb_index_mongo_to_pgvector` / `_chroma` / `_redis` (+ existing JSONL `_vectors`).
- Next start: `/ccaa-story-start 200`. Cloud remains **M90**.
