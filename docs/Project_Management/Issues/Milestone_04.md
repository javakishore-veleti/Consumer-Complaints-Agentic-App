# Milestone M04 - Local ops hardening (secrets → endpoints → ingest → locations → vectors)

**Scope:** Local-only after M03. Product order **C → D → A → B → E**. No paid cloud resources. Cloud remains **M06**. Intellect/ACL are **M05**.

**Status: done.** 1 epic, 5 features, 12 stories (C→D→A→B→E complete; next is M05).

How to read this file:
- `#144` is the GitHub issue number. The `M04-00NN` key is the sequence tag at the start of the issue title.
- Section 1 is build order. Section 2 groups by epic/feature. Section 3 is the Superpowers command table (filled when stories start).

## Contents

- [1. Table of contents (build order)](#1-table-of-contents-build-order)
- [2. The same issues grouped by epic and feature](#2-the-same-issues-grouped-by-epic-and-feature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Notes](#4-notes)

## 1. Table of contents (build order)

### Phase 1 - (C) System secrets sync

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 1 | #144 | M04-0001 | Epic | Local ops hardening | Parent |
| 2 | #145 | M04-0002 | Feature | System secrets sync (Admin → Airflow) | C first |
| 3 | #153 | M04-0007 | Story | Admin Sync secrets to Airflow button | UI on existing D42 API |
| 4 | #154 | M04-0008 | Story | Align fixed system secret inventory docs | Docs/inventory |

### Phase 2 - (D) AppEndpoints

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 5 | #146 | M04-0003 | Feature | AppEndpoints catalog (local-first) | D after C |
| 6 | #155 | M04-0009 | Story | AppEndpoints table, DAO, and local seed | Schema |
| 7 | #156 | M04-0010 | Story | AppEndpoints list/read API | API |
| 8 | #157 | M04-0011 | Story | Admin AppEndpoints thin UI for Imports | UI |

### Phase 3 - (A) DB Ingest

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 9 | #147 | M04-0004 | Feature | DB Ingest to local MongoDB | A after D |
| 10 | #158 | M04-0012 | Story | Local Mongo ingest DAG + callbacks | DAG |
| 11 | #159 | M04-0013 | Story | Register ingest workflow and MIO binding | Catalog |
| 12 | #160 | M04-0014 | Story | Admin DB Ingest screen start/refresh | UI |

### Phase 4 - (B) Locations

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 13 | #148 | M04-0005 | Feature | Dataset locations expansion (local-first) | B after A |
| 14 | #161 | M04-0015 | Story | DAGs resolve from/to via catalog and AppEndpoints | Wire-through |
| 15 | #162 | M04-0016 | Story | Admin location vs endpoint clarity | UX/docs |

### Phase 5 - (E) Local vectors

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 16 | #149 | M04-0006 | Feature | Local vector indexing | E last in M04 |
| 17 | #163 | M04-0017 | Story | Local vector store + index DAG | Infra+DAG |
| 18 | #164 | M04-0018 | Story | Register index workflow and Admin start | Catalog+UI |

## 2. The same issues grouped by epic and feature

```
Epic #144  M04-0001  Local ops hardening
|
+-- Feature #145  M04-0002  System secrets sync (C)
|     +-- #153  Admin Sync secrets to Airflow button
|     +-- #154  Align fixed system secret inventory docs
|
+-- Feature #146  M04-0003  AppEndpoints (D)
|     +-- #155  AppEndpoints table, DAO, and local seed
|     +-- #156  AppEndpoints list/read API
|     +-- #157  Admin AppEndpoints thin UI for Imports
|
+-- Feature #147  M04-0004  DB Ingest local Mongo (A)
|     +-- #158  Local Mongo ingest DAG + callbacks
|     +-- #159  Register ingest workflow and MIO binding
|     +-- #160  Admin DB Ingest screen start/refresh
|
+-- Feature #148  M04-0005  Dataset locations local-first (B)
|     +-- #161  DAGs resolve from/to via catalog and AppEndpoints
|     +-- #162  Admin location vs endpoint clarity
|
+-- Feature #149  M04-0006  Local vector indexing (E)
      +-- #163  Local vector store + index DAG
      +-- #164  Register index workflow and Admin start
```

## 3. Superpowers workflow

Every command has its own row with **Status** (`Planned`, `In progress` or `Done`), **Started**, **Completed**.

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #153 | 1 | `/ccaa-story-start 153` | Done | 2026-11-15 13:51 | 2026-11-15 13:51 |
| #153 | 2 | `/brainstorming Story #153: Admin Sync secrets button → POST upsert-secrets; never show values` | Done | 2026-11-15 13:51 | 2026-11-15 13:54 |
| #153 | 3 | `/using-git-worktrees Story #153: branch m04-0007-admin-sync-secrets` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 4 | `/writing-plans Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 5 | `/test-driven-development Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 6 | `/subagent-driven-development Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 7 | `/ccaa-commit-push 153` after every task (repeat) | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 8 | `/verification-before-completion Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 9 | `/requesting-code-review Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 10 | `/ccaa-commit-push 153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 11 | `/finishing-a-development-branch Story #153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| #153 | 12 | `/ccaa-story-complete 153` | Done | 2026-11-15 13:54 | 2026-11-15 13:54 |
| Feature #145 | 1 | `/ccaa-feature-complete 145` | Done | 2026-11-15 13:56 | 2026-11-15 13:56 |
| #154 | 1 | `/ccaa-story-start 154` | Done | 2026-11-15 13:55 | 2026-11-15 13:56 |
| #154 | 12 | `/ccaa-story-complete 154` | Done | 2026-11-15 13:56 | 2026-11-15 13:56 |
| Epic #144 | 1 | `/ccaa-epic-complete 144` | Planned | - | - |

| #155 | 1 | `/ccaa-story-start 155` | Done | 2026-11-15 14:08 | 2026-11-15 14:08 |
| #155 | 12 | `/ccaa-story-complete 155` | Done | 2026-11-15 14:13 | 2026-11-15 14:13 |
| #156 | 1 | `/ccaa-story-start 156` | Done | 2026-11-15 14:14 | 2026-11-15 14:14 |
| #156 | 12 | `/ccaa-story-complete 156` | Done | 2026-11-15 14:17 | 2026-11-15 14:17 |
| #157 | 1 | `/ccaa-story-start 157` | Done | 2026-11-15 14:17 | 2026-11-15 14:17 |
| #157 | 2 | `/brainstorming Story #157: Admin AppEndpoints thin UI on Imports; GET /app-endpoints; never show secret values` | Done | 2026-11-15 19:43 | 2026-11-15 19:44 |
| #157 | 3 | `/using-git-worktrees Story #157: branch m04-0011-admin-app-endpoints-ui` | Done | 2026-11-15 19:43 | 2026-11-15 19:43 |
| #157 | 4 | `/writing-plans Story #157` | Done | 2026-11-15 19:44 | 2026-11-15 19:44 |
| #157 | 5 | `/test-driven-development Story #157` | Done | 2026-11-15 19:44 | 2026-11-15 19:45 |
| #157 | 6 | `/subagent-driven-development Story #157` | Done | 2026-11-15 19:45 | 2026-11-15 19:45 |
| #157 | 7 | `/ccaa-commit-push 157` after every task (repeat) | Done | 2026-11-15 19:45 | 2026-11-15 19:46 |
| #157 | 8 | `/verification-before-completion Story #157` | Done | 2026-11-15 19:45 | 2026-11-15 19:45 |
| #157 | 9 | `/requesting-code-review Story #157` | Done | 2026-11-15 19:45 | 2026-11-15 19:45 |
| #157 | 10 | `/ccaa-commit-push 157` | Done | 2026-11-15 19:46 | 2026-11-15 19:46 |
| #157 | 11 | `/finishing-a-development-branch Story #157` | Done | 2026-11-15 19:46 | 2026-11-15 19:46 |
| #157 | 12 | `/ccaa-story-complete 157` | Done | 2026-11-15 19:46 | 2026-11-15 19:46 |

| #158 | 1 | `/ccaa-story-start 158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 2 | `/brainstorming Story #158: ingest_cfpb_all + CCA_MONGO_COMPLAINTS_URL (D86)` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 3 | `/using-git-worktrees Story #158: branch m04-0012-local-mongo-ingest-dag` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 4 | `/writing-plans Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 5 | `/test-driven-development Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 6 | `/subagent-driven-development Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 7 | `/ccaa-commit-push 158` after every task (repeat) | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 8 | `/verification-before-completion Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 9 | `/requesting-code-review Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 10 | `/ccaa-commit-push 158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 11 | `/finishing-a-development-branch Story #158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #158 | 12 | `/ccaa-story-complete 158` | Done | 2026-11-15 19:52 | 2026-11-15 19:52 |
| #159 | 1 | `/ccaa-story-start 159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 2 | `/brainstorming Story #159: seed ingest_cfpb_all + All MIO bind` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 3 | `/using-git-worktrees Story #159: branch m04-0013-register-ingest-workflow` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 4 | `/writing-plans Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 5 | `/test-driven-development Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 6 | `/subagent-driven-development Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 7 | `/ccaa-commit-push 159 after every task (repeat)` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 8 | `/verification-before-completion Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 9 | `/requesting-code-review Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 10 | `/ccaa-commit-push 159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 11 | `/finishing-a-development-branch Story #159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #159 | 12 | `/ccaa-story-complete 159` | Done | 2026-11-15 19:55 | 2026-11-15 19:55 |
| #160 | 1 | `/ccaa-story-start 160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 2 | `/brainstorming Story #160: DB Ingest screen + ingest_* filter` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 3 | `/using-git-worktrees Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 4 | `/writing-plans Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 5 | `/test-driven-development Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 6 | `/subagent-driven-development Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 7 | `/ccaa-commit-push 160 after every task (repeat)` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 8 | `/verification-before-completion Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 9 | `/requesting-code-review Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 10 | `/ccaa-commit-push 160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 11 | `/finishing-a-development-branch Story #160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #160 | 12 | `/ccaa-story-complete 160` | Done | 2026-11-15 19:57 | 2026-11-15 19:57 |
| #161 | 1 | `/ccaa-step 161.1` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 2 | `/ccaa-step 161.2` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 3 | `/ccaa-step 161.3` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 4 | `/ccaa-step 161.4` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 5 | `/ccaa-step 161.5` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 6 | `/ccaa-step 161.6` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 7 | `/ccaa-step 161.7` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 8 | `/ccaa-step 161.8` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 9 | `/ccaa-step 161.9` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 10 | `/ccaa-step 161.10` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 11 | `/ccaa-step 161.11` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #161 | 12 | `/ccaa-step 161.12` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 1 | `/ccaa-step 162.1` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 2 | `/ccaa-step 162.2` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 3 | `/ccaa-step 162.3` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 4 | `/ccaa-step 162.4` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 5 | `/ccaa-step 162.5` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 6 | `/ccaa-step 162.6` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 7 | `/ccaa-step 162.7` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 8 | `/ccaa-step 162.8` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 9 | `/ccaa-step 162.9` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 10 | `/ccaa-step 162.10` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 11 | `/ccaa-step 162.11` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #162 | 12 | `/ccaa-step 162.12` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| Feature #148 | 1 | `/ccaa-feature-complete 148` | Done | 2026-11-15 21:11 | 2026-11-15 21:11 |
| #163 | 1 | `/ccaa-story-start 163` | Done | 2026-11-15 21:20 | 2026-11-15 21:20 |
| #163 | 2 | `/brainstorming Story #163: D88 local JSONL vectors + index_cfpb_all` | Done | 2026-11-15 21:20 | 2026-11-16 12:04 |
| #163 | 3 | `/using-git-worktrees Story #163: branch m04-0017-local-vector-index` | Done | 2026-11-15 21:20 | 2026-11-15 21:20 |
| #163 | 4 | `/writing-plans Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 5 | `/test-driven-development Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 6 | `/subagent-driven-development Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 7 | `/ccaa-commit-push 163 after every task (repeat)` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 8 | `/verification-before-completion Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 9 | `/requesting-code-review Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 10 | `/ccaa-commit-push 163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 11 | `/finishing-a-development-branch Story #163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #163 | 12 | `/ccaa-story-complete 163` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 1 | `/ccaa-story-start 164` | Done | 2026-11-15 21:20 | 2026-11-15 21:20 |
| #164 | 2 | `/brainstorming Story #164: seed index + Admin Index page` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 3 | `/using-git-worktrees Story #164` | Done | 2026-11-15 21:20 | 2026-11-15 21:20 |
| #164 | 4 | `/writing-plans Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 5 | `/test-driven-development Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 6 | `/subagent-driven-development Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 7 | `/ccaa-commit-push 164 after every task (repeat)` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 8 | `/verification-before-completion Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 9 | `/requesting-code-review Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 10 | `/ccaa-commit-push 164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 11 | `/finishing-a-development-branch Story #164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| #164 | 12 | `/ccaa-story-complete 164` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| Feature #149 | 1 | `/ccaa-feature-complete 149` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |
| Epic #144 | 1 | `/ccaa-epic-complete 144` | Done | 2026-11-16 12:04 | 2026-11-16 12:04 |




## 4. Notes

- **Local only.** No AWS/Azure/GCP spend in this milestone.
- Upsert secrets **API** already shipped in M02 (#77 / D42); M04 adds Admin UI + inventory clarity.
- Product features: `docs/PRODUCT_FEATURES.md` F4–F8.
- Next milestone: **M05** Intellect + MIO ACL (`Milestone_05.md`).
