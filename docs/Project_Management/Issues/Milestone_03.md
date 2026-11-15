# Milestone M03 - Local Admin UI E2E integration

**Scope:** Prove the local path **User → Admin UI → APIs → Apache Airflow → callback APIs → operational DB → Admin UI refresh**, with a pluggable local DB. Default is **SQLite** (fewest containers). Before the epic is Done, the same path must also pass after switching only `.env` to **Postgres**, then to **MongoDB**. Cloud deploy is **M06**. Vector/RAG ingest is **M04+**.

**Status: in progress.** 1 epic, 4 features and 8 stories. 7 stories are already done; 4 stories are left to build.

How to read this file:
- `#116` is the GitHub issue number. The `M03-00NN` key is the sequence tag at the start of the issue title. Keys are not always build order.
- Section 1 is build order. Section 2 groups by epic/feature. Section 3 is the Superpowers command table. Section 4 is project skills.

## Contents

- [1. Table of contents (build order)](#1-table-of-contents-build-order)
  - [Phase 1 - Pluggable operational DB](#phase-1---pluggable-operational-db)
  - [Phase 2 - Lite local runtime](#phase-2---lite-local-runtime)
  - [Phase 3 - Admin UI integration](#phase-3---admin-ui-integration)
  - [Phase 4 - DoD matrix](#phase-4---dod-matrix)
- [2. The same issues grouped by epic and feature](#2-the-same-issues-grouped-by-epic-and-feature)
- [3. Superpowers workflow](#3-superpowers-workflow)
- [4. Project skills](#4-project-skills-ccaa---consumer-complaints-agentic-app)
- [5. Notes](#5-notes)

## 1. Table of contents (build order)

Phases 1–3 can run **in parallel tracks** after #116 (decision). Phase 4 waits until SQLite, Postgres, and MongoDB paths each pass once.

### Phase 1 - Pluggable operational DB

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 1 | #111 | M03-0001 | Epic | Local Admin UI E2E integration | Parent of all M03 work |
| 2 | #112 | M03-0002 | Feature | Pluggable local operational DB (SQLite / Postgres / MongoDB) | Parent of DB stories |
| 3 | #116 | M03-0006 | Story | Decide and document pluggable DB seam (SQLite / Postgres / MongoDB) | Decision first (next D##) |
| 4 | #117 | M03-0007 | Story | SQLite-first operational store for admin schema | Default local backend |
| 5 | #118 | M03-0008 | Story | Postgres via .env: migrate and verify same APIs | Second DoD backend |
| 6 | #119 | M03-0009 | Story | MongoDB operational store via .env (DAO/factory seam) | Third DoD backend |

### Phase 2 - Lite local runtime

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 7 | #113 | M03-0003 | Feature | Lite local runtime profiles | Parent |
| 8 | #120 | M03-0010 | Story | npm/docker profiles: SQLite-lite default; Postgres and Mongo opt-in | Fewer containers by default |

### Phase 3 - Admin UI integration

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 9 | #114 | M03-0004 | Feature | Admin UI ↔ API local integration | Parent |
| 10 | #121 | M03-0011 | Story | Admin Imports: live API list/start/refresh hardening | Live Middleware, no mocks |
| 11 | #122 | M03-0012 | Story | E2E happy path: UI → API → Airflow → callback → UI | Full path on active DB |

### Phase 4 - DoD matrix

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 12 | #115 | M03-0005 | Feature | M03 DoD verification (SQLite → Postgres → MongoDB) | Parent |
| 13 | #123 | M03-0013 | Story | DoD matrix: prove path on SQLite, Postgres, and MongoDB | Epic not Done until all three pass |

## 2. The same issues grouped by epic and feature

```
Epic #111  M03-0001  Local Admin UI E2E integration
|
+-- Feature #112  M03-0002  Pluggable local operational DB (SQLite / Postgres / MongoDB)
|     +-- #116  Decide and document pluggable DB seam
|     +-- #117  SQLite-first operational store for admin schema
|     +-- #118  Postgres via .env: migrate and verify same APIs
|     +-- #119  MongoDB operational store via .env (DAO/factory seam)
|
+-- Feature #113  M03-0003  Lite local runtime profiles
|     +-- #120  npm/docker profiles: SQLite-lite default; Postgres and Mongo opt-in
|
+-- Feature #114  M03-0004  Admin UI ↔ API local integration
|     +-- #121  Admin Imports: live API list/start/refresh hardening
|     +-- #122  E2E happy path: UI → API → Airflow → callback → UI
|
+-- Feature #115  M03-0005  M03 DoD verification (SQLite → Postgres → MongoDB)
      +-- #123  DoD matrix: prove path on SQLite, Postgres, and MongoDB
```

## 3. Superpowers workflow

One chat per story (or one parallel agent per independent story). Run the commands of a story from top to bottom. `/ccaa-*` are the project skills (section 4); the others come from the Superpowers plugin.

Every command has its own row with a **Status** (`Planned`, `In progress` or `Done`), a **Started** date and a **Completed** date (`-` until set). The step that is `In progress` is the one to run next. You do not edit the table: when a step finishes, `/ccaa-milestone-log N` marks it `Done` with today's date and starts the next step. `/ccaa-story-start` and `/ccaa-story-complete` log their own step. The change is saved in the next `/ccaa-commit-push`.

Standard code story, with `N` as the issue number:

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Marks the issue in progress and refreshes the feature and epic |
| 2 | `/brainstorming Story #N ...` | Confirms the design against the issue and `DESIGN.md` |
| 3 | `/using-git-worktrees Story #N: branch ...` | Creates an isolated workspace on a new branch for the story |
| 4 | `/writing-plans Story #N` | Breaks the story into small tasks with exact files and verification steps |
| 5 | `/test-driven-development Story #N` | Loads RED-GREEN-REFACTOR for step 6 |
| 6 | `/subagent-driven-development Story #N` | Builds each task with a fresh subagent (or `/executing-plans`) |
| 7 | `/ccaa-commit-push N` | After every task of step 6 (repeat) |
| 8 | `/verification-before-completion Story #N` | Lint, tests, acceptance |
| 9 | `/requesting-code-review Story #N` | Review against the plan |
| 10 | `/ccaa-commit-push N` | Review fixes |
| 11 | `/finishing-a-development-branch Story #N` | PR → main when CI green (preferred); merge only green |
| 12 | `/ccaa-story-complete N` | Tick acceptance, close story, refresh feature |

If a test fails and you do not know why, run `/systematic-debugging Story #N` before changing code.

**Parallel tracks (after #116):** Track A `#117` then `#118` then `#119`; Track B `#120`; Track C `#121` then `#122`; Track D `#123` last.

### Phase 1 - Pluggable operational DB

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #116 | 1 | `/ccaa-story-start 116` | Done | 2026-11-15 01:13 | 2026-11-15 01:13 |
| #116 | 2 | `/brainstorming Story #116: decide SQLite default, Postgres via CCA_DB_URL, MongoDB via .env for operational/admin store; record DESIGN.md decision(s); update .env.example and ARCHITECTURE.md` | Done | 2026-11-15 01:13 | 2026-11-15 01:16 |
| #116 | 3 | `/using-git-worktrees Story #116: branch m03-0006-pluggable-db-seam` | Done | 2026-11-15 01:16 | 2026-11-15 01:16 |
| #116 | 4 | `/writing-plans Story #116` | Done | 2026-11-15 01:16 | 2026-11-15 01:16 |
| #116 | 5 | `/test-driven-development Story #116` | Done | 2026-11-15 01:16 | 2026-11-15 01:16 |
| #116 | 6 | `/subagent-driven-development Story #116` | Done | 2026-11-15 01:16 | 2026-11-15 01:19 |
| #116 | 7 | `/ccaa-commit-push 116` after every task (repeat) | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #116 | 8 | `/verification-before-completion Story #116` | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #116 | 9 | `/requesting-code-review Story #116` | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #116 | 10 | `/ccaa-commit-push 116` | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #116 | 11 | `/finishing-a-development-branch Story #116` | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #116 | 12 | `/ccaa-story-complete 116` | Done | 2026-11-15 01:19 | 2026-11-15 01:19 |
| #117 | 1 | `/ccaa-story-start 117` | Done | 2026-11-15 01:21 | 2026-11-15 01:21 |
| #117 | 2 | `/brainstorming Story #117: SQLite-first operational store for admin schema (workflows, catalog, ingest/exec logs); migrations and APIs without Postgres container` | Done | 2026-11-15 01:21 | 2026-11-15 01:24 |
| #117 | 3 | `/using-git-worktrees Story #117: branch m03-0007-sqlite-first-admin-store` | Done | 2026-11-15 01:22 | 2026-11-15 01:22 |
| #117 | 4 | `/writing-plans Story #117` | Done | 2026-11-15 01:23 | 2026-11-15 01:23 |
| #117 | 5 | `/test-driven-development Story #117` | Done | 2026-11-15 01:24 | 2026-11-15 01:24 |
| #117 | 6 | `/subagent-driven-development Story #117` | Done | 2026-11-15 01:24 | 2026-11-15 01:24 |
| #117 | 7 | `/ccaa-commit-push 117` after every task (repeat) | Done | 2026-11-15 01:24 | 2026-11-15 01:24 |
| #117 | 8 | `/verification-before-completion Story #117` | Done | 2026-11-15 01:24 | 2026-11-15 01:25 |
| #117 | 9 | `/requesting-code-review Story #117` | Done | 2026-11-15 01:25 | 2026-11-15 01:25 |
| #117 | 10 | `/ccaa-commit-push 117` | Done | 2026-11-15 01:25 | 2026-11-15 01:27 |
| #117 | 11 | `/finishing-a-development-branch Story #117` | Done | 2026-11-15 01:27 | 2026-11-15 01:27 |
| #117 | 12 | `/ccaa-story-complete 117` | Done | 2026-11-15 01:27 | 2026-11-15 01:27 |
| #118 | 1 | `/ccaa-story-start 118` | Done | 2026-11-15 01:28 | 2026-11-15 01:28 |
| #118 | 2 | `/brainstorming Story #118: Postgres via .env only; migrate and verify same APIs and callback path` | Done | 2026-11-15 01:28 | 2026-11-15 01:30 |
| #118 | 3 | `/using-git-worktrees Story #118: branch m03-0008-postgres-via-env` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 4 | `/writing-plans Story #118` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 5 | `/test-driven-development Story #118` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 6 | `/subagent-driven-development Story #118` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 7 | `/ccaa-commit-push 118` after every task (repeat) | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 8 | `/verification-before-completion Story #118` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 9 | `/requesting-code-review Story #118` | Done | 2026-11-15 01:30 | 2026-11-15 01:30 |
| #118 | 10 | `/ccaa-commit-push 118` | In progress | 2026-11-15 01:30 | - |
| #118 | 11 | `/finishing-a-development-branch Story #118` | Planned | - | - |
| #118 | 12 | `/ccaa-story-complete 118` | Planned | - | - |
| #119 | 1 | `/ccaa-story-start 119` | Done | 2026-11-15 01:35 | 2026-11-15 01:35 |
| #119 | 2 | `/brainstorming Story #119: MongoDB operational store via .env; DAO/factory seam (D45); same Admin UI → API → Airflow → callback path` | In progress | 2026-11-15 01:35 | - |
| #119 | 3 | `/using-git-worktrees Story #119: branch m03-0009-mongodb-operational-store` | Planned | - | - |
| #119 | 4 | `/writing-plans Story #119` | Planned | - | - |
| #119 | 5 | `/test-driven-development Story #119` | Planned | - | - |
| #119 | 6 | `/subagent-driven-development Story #119` | Planned | - | - |
| #119 | 7 | `/ccaa-commit-push 119` after every task (repeat) | Planned | - | - |
| #119 | 8 | `/verification-before-completion Story #119` | Planned | - | - |
| #119 | 9 | `/requesting-code-review Story #119` | Planned | - | - |
| #119 | 10 | `/ccaa-commit-push 119` | Planned | - | - |
| #119 | 11 | `/finishing-a-development-branch Story #119` | Planned | - | - |
| #119 | 12 | `/ccaa-story-complete 119` | Planned | - | - |
| Feature #112 | 1 | `/ccaa-feature-complete 112` | In progress | 2026-11-15 01:13 | - |

### Phase 2 - Lite local runtime

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #120 | 1 | `/ccaa-story-start 120` | Planned | - | - |
| #120 | 2 | `/brainstorming Story #120: npm/docker profiles — SQLite-lite default; Postgres and Mongo opt-in; document container sets` | Planned | - | - |
| #120 | 3 | `/using-git-worktrees Story #120: branch m03-0010-local-runtime-profiles` | Planned | - | - |
| #120 | 4 | `/writing-plans Story #120` | Planned | - | - |
| #120 | 5 | `/test-driven-development Story #120` | Planned | - | - |
| #120 | 6 | `/subagent-driven-development Story #120` | Planned | - | - |
| #120 | 7 | `/ccaa-commit-push 120` after every task (repeat) | Planned | - | - |
| #120 | 8 | `/verification-before-completion Story #120` | Planned | - | - |
| #120 | 9 | `/requesting-code-review Story #120` | Planned | - | - |
| #120 | 10 | `/ccaa-commit-push 120` | Planned | - | - |
| #120 | 11 | `/finishing-a-development-branch Story #120` | Planned | - | - |
| #120 | 12 | `/ccaa-story-complete 120` | Planned | - | - |
| Feature #113 | 1 | `/ccaa-feature-complete 113` | Planned | - | - |

### Phase 3 - Admin UI integration

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #121 | 1 | `/ccaa-story-start 121` | Done | 2026-11-15 01:12 | 2026-11-15 01:12 |
| #121 | 2 | `/brainstorming Story #121: Admin Imports live API list/start/refresh hardening; no mock status; proxy/apiBaseUrl for local portal` | Done | 2026-11-15 01:12 | 2026-11-15 01:16 |
| #121 | 3 | `/using-git-worktrees Story #121: branch m03-0011-admin-imports-live-api` | Done | 2026-11-15 01:16 | 2026-11-15 01:16 |
| #121 | 4 | `/writing-plans Story #121` | Done | 2026-11-15 01:16 | 2026-11-15 01:16 |
| #121 | 5 | `/test-driven-development Story #121` | Done | 2026-11-15 01:16 | 2026-11-15 01:18 |
| #121 | 6 | `/subagent-driven-development Story #121` | Done | 2026-11-15 01:18 | 2026-11-15 01:18 |
| #121 | 7 | `/ccaa-commit-push 121` after every task (repeat) | Done | 2026-11-15 01:18 | 2026-11-15 01:18 |
| #121 | 8 | `/verification-before-completion Story #121` | Done | 2026-11-15 01:18 | 2026-11-15 01:18 |
| #121 | 9 | `/requesting-code-review Story #121` | Done | 2026-11-15 01:18 | 2026-11-15 01:18 |
| #121 | 10 | `/ccaa-commit-push 121` | Done | 2026-11-15 01:18 | 2026-11-15 01:18 |
| #121 | 11 | `/finishing-a-development-branch Story #121` | Done | 2026-11-15 01:18 | 2026-11-15 01:22 |
| #121 | 12 | `/ccaa-story-complete 121` | Done | 2026-11-15 01:22 | 2026-11-15 01:22 |
| #122 | 1 | `/ccaa-story-start 122` | Done | 2026-11-15 01:24 | 2026-11-15 01:24 |
| #122 | 2 | `/brainstorming Story #122: E2E happy path UI → API → Airflow → callback → UI on active DB profile` | Done | 2026-11-15 01:24 | 2026-11-15 01:26 |
| #122 | 3 | `/using-git-worktrees Story #122: branch m03-0012-e2e-happy-path` | Done | 2026-11-15 01:26 | 2026-11-15 01:26 |
| #122 | 4 | `/writing-plans Story #122` | Done | 2026-11-15 01:26 | 2026-11-15 01:26 |
| #122 | 5 | `/test-driven-development Story #122` | Done | 2026-11-15 01:26 | 2026-11-15 01:28 |
| #122 | 6 | `/subagent-driven-development Story #122` | Done | 2026-11-15 01:28 | 2026-11-15 01:28 |
| #122 | 7 | `/ccaa-commit-push 122` after every task (repeat) | Done | 2026-11-15 01:28 | 2026-11-15 01:28 |
| #122 | 8 | `/verification-before-completion Story #122` | Done | 2026-11-15 01:28 | 2026-11-15 01:29 |
| #122 | 9 | `/requesting-code-review Story #122` | Done | 2026-11-15 01:29 | 2026-11-15 01:29 |
| #122 | 10 | `/ccaa-commit-push 122` | Done | 2026-11-15 01:29 | 2026-11-15 01:29 |
| #122 | 11 | `/finishing-a-development-branch Story #122` | Done | 2026-11-15 01:29 | 2026-11-15 01:31 |
| #122 | 12 | `/ccaa-story-complete 122` | Done | 2026-11-15 01:31 | 2026-11-15 01:31 |
| Feature #114 | 1 | `/ccaa-feature-complete 114` | Done | 2026-11-15 01:12 | 2026-11-15 01:31 |

### Phase 4 - DoD matrix

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #123 | 1 | `/ccaa-story-start 123` | Planned | - | - |
| #123 | 2 | `/brainstorming Story #123: DoD matrix checklist/script — prove path on SQLite, Postgres, and MongoDB; epic Done only after all three` | Planned | - | - |
| #123 | 3 | `/using-git-worktrees Story #123: branch m03-0013-dod-matrix` | Planned | - | - |
| #123 | 4 | `/writing-plans Story #123` | Planned | - | - |
| #123 | 5 | `/test-driven-development Story #123` | Planned | - | - |
| #123 | 6 | `/subagent-driven-development Story #123` | Planned | - | - |
| #123 | 7 | `/ccaa-commit-push 123` after every task (repeat) | Planned | - | - |
| #123 | 8 | `/verification-before-completion Story #123` | Planned | - | - |
| #123 | 9 | `/requesting-code-review Story #123` | Planned | - | - |
| #123 | 10 | `/ccaa-commit-push 123` | Planned | - | - |
| #123 | 11 | `/finishing-a-development-branch Story #123` | Planned | - | - |
| #123 | 12 | `/ccaa-story-complete 123` | Planned | - | - |
| Feature #115 | 1 | `/ccaa-feature-complete 115` | Planned | - | - |
| Epic #111 | 1 | `/ccaa-epic-complete 111` | In progress | 2026-11-15 01:12 | - |

## 4. Project skills (`ccaa-` = Consumer Complaints Agentic App)

The skills live in `.cursor/skills/`. Each takes a GitHub issue number.

| Command | When | What it does |
|---|---|---|
| `/ccaa-story-start N` | Before the first Superpowers command of a story | Sets the story to `status: in-progress`, writes the status line, moves the parent feature and epic to in progress |
| `/ccaa-story-complete N` | After review and the final commit | Checks acceptance, closes the story, refreshes the feature |
| `/ccaa-feature-complete N` | When every story of the feature is done | Marks the feature done and closes it, refreshes the epic |
| `/ccaa-epic-complete N` | When every feature of the epic is done | Marks the epic done and closes it, and marks this file complete |
| `/ccaa-milestone-log N` | After each workflow step finishes | Marks the `In progress` step for issue N as `Done`, starts the next step |
| `/ccaa-commit-push N` | After every task, and at the end of each story | Lint/tests, commit as repository owner, push |
| `/ccaa-progress-sync N` | Used by the skills above | Rebuilds feature/epic checklist from child state |

## 5. Notes

- **DoD:** SQLite path first; then Postgres via `.env`; then MongoDB via `.env` — all locally. No major code changes between backends (DAO/factory seam).
- **Cloud** issues formerly titled M03 are now **M06** (#73 epic and children). Do not build them in this milestone.
- **Specs/plans** under `docs/Superpowers/` appear when a story runs `/brainstorming` and `/writing-plans` (e.g. `M03-0006-*-design.md`). They do not exist until a story starts.
- **Where the details are:** decisions go in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Next free decision is **D78+** (D75 = pluggable operational DB seam #116; D76 = SQLite-first #117; D77 = Postgres via `.env` #118).
- **PR → main**, merge only when CI is green. Git author must be `javakishore-veleti <6062900+javakishore-veleti@users.noreply.github.com>`; strip AI trailers.
- **D64:** new facades only when needed; prefer extending existing packages.
