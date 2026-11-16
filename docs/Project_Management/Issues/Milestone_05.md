# Milestone M05 - Intellect and MIO ACL (local)

**Scope:** After M04 (C–E) is Done. Product order **F → G**. Local-only; no paid cloud/LLM until explicitly approved.

**Status: done.** 1 epic, 2 features, 2 stories (all done).

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
| #165 | 1 | `/ccaa-story-start 165` | Done | 2026-11-16 12:43 | 2026-11-16 12:43 |
| #165 | 2 | `/brainstorming Story #165: D89 mios_acl + X-CCA-Audience` | Done | 2026-11-16 12:43 | 2026-11-16 13:10 |
| #165 | 3 | `/using-git-worktrees Story #165: branch m05-0004-mio-acl` | Done | 2026-11-16 12:43 | 2026-11-16 12:43 |
| #165 | 4–12 | plan → TDD → commit → finish → complete | Done | 2026-11-16 13:10 | 2026-11-16 13:10 |
| Feature #151 | 1 | `/ccaa-feature-complete 151` | Done | 2026-11-16 13:10 | 2026-11-16 13:10 |
| #166 | 1 | `/ccaa-story-start 166` | Done | 2026-11-16 12:43 | 2026-11-16 12:43 |
| #166 | 2 | `/brainstorming Story #166: D90 intellect query + portal` | Done | 2026-11-16 12:43 | 2026-11-16 13:10 |
| #166 | 3–12 | plan → TDD → commit → finish → complete | Done | 2026-11-16 13:10 | 2026-11-16 13:10 |
| Feature #152 | 1 | `/ccaa-feature-complete 152` | Done | 2026-11-16 13:10 | 2026-11-16 13:10 |
| Epic #150 | 1 | `/ccaa-epic-complete 150` | Done | 2026-11-16 13:10 | 2026-11-16 13:10 |

## 4. Notes

- Product features: `docs/PRODUCT_FEATURES.md` F15–F16.
- Decisions D89 / D90.
- Next product milestones: **M06** split SoT (`Milestone_06.md` / #169) → **M07** Storage Layer (#175) → **M08** retrieval/eval (#183). Cloud parked as **M90** (`Milestone_90.md` / #73).
