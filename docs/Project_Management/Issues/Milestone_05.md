# Milestone M05 - Intellect and MIO ACL (local)

**Scope:** After M04 (C–E) is Done. Product order **F → G**. Local-only; no paid cloud/LLM until explicitly approved.

**Status: planned.** 1 epic, 2 features, 2 stories (0 done). Depends on M04 vectors (#149).

## Contents

- [1. Build order](#1-build-order)
- [2. Grouped by epic/feature](#2-grouped-by-epicfeature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #150 | M05-0001 | Epic | Intellect app and MIO ACL (local) |
| 2 | #151 | M05-0002 | Feature | MIO access control (ACL) (F) |
| 3 | #165 | M05-0004 | Story | MIO ACL model and enforce on start |
| 4 | #152 | M05-0003 | Feature | Intellect app local RAG/agentic (G) |
| 5 | #166 | M05-0005 | Story | Intellect MVP query local indexed complaints |

## 2. Grouped by epic/feature

```
Epic #150  M05-0001  Intellect and MIO ACL (local)
|
+-- Feature #151  M05-0002  MIO ACL (F)
|     +-- #165  MIO ACL model and enforce on start
|
+-- Feature #152  M05-0003  Intellect app (G)
      +-- #166  Intellect MVP query local indexed complaints
```

## 3. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #165 | 1 | `/ccaa-story-start 165` | Planned | - | - |
| #165 | 12 | `/ccaa-story-complete 165` | Planned | - | - |
| Feature #151 | 1 | `/ccaa-feature-complete 151` | Planned | - | - |
| #166 | 1 | `/ccaa-story-start 166` | Planned | - | - |
| #166 | 12 | `/ccaa-story-complete 166` | Planned | - | - |
| Feature #152 | 1 | `/ccaa-feature-complete 152` | Planned | - | - |
| Epic #150 | 1 | `/ccaa-epic-complete 150` | Planned | - | - |

*(Expand full command rows when each story starts.)*

## 4. Notes

- Product features: `docs/PRODUCT_FEATURES.md` F15–F16.
- Do not start until M04 epic #144 is Done (especially vectors #149).
