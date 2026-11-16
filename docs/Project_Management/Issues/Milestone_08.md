# Milestone M08 - Advanced Intellect retrieval and evaluation

**Scope:** After M07 Storage Layer is queryable. Diagram **RETRIEVAL LAYER** + right-side **EVALUATION** ladder from 5.25 / Qi1FcoRWEiw: baseline → +hybrid → +self-query → +decomposition → +reranker → everything. Local-first; paid LLM only if a story brainstorm explicitly approves.

**Status: planned.** 1 epic, 3 features, 3 stories.

## Contents

- [1. Build order](#1-build-order)
- [2. Grouped by epic/feature](#2-grouped-by-epicfeature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #183 | M08-0001 | Epic | Advanced Intellect retrieval and evaluation |
| 2 | #184 | M08-0002 | Feature | Hybrid retrieval (vector + BM25 + RRF) |
| 3 | #187 | M08-0005 | Story | BM25 index + RRF hybrid search API path |
| 4 | #185 | M08-0003 | Feature | Flagged retrieval ladder through +reranker |
| 5 | #188 | M08-0006 | Story | Retrieval Config flags: self-query, decompose, rerank |
| 6 | #186 | M08-0004 | Feature | EVALUATION scorecard for retrieval configs |
| 7 | #189 | M08-0007 | Story | Golden-set EVALUATION harness for ladder configs |

## 2. Grouped by epic/feature

```
Epic #183  M08-0001  Advanced Intellect retrieval and evaluation
|
+-- Feature #184  M08-0002  Hybrid (vector + BM25 + RRF)
|     +-- #187  BM25 + RRF hybrid search API path
|
+-- Feature #185  M08-0003  Ladder through +reranker
|     +-- #188  Config flags: self-query, decompose, rerank
|
+-- Feature #186  M08-0004  EVALUATION scorecard
      +-- #189  Golden-set harness for ladder configs
```

## 3. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #187 | 1 | `/ccaa-story-start 187` | Planned | | |

## 4. Notes

- Ship bias from 5.25: **+reranker**, not necessarily **everything**.
- Cloud remains **M90**.
