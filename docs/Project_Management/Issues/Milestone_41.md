# Milestone M41 - DataArchitecture full lakehouse (Refined/Curated/Taxonomy/Vectors)

**Scope:** Docs only — expand `docs/DataArchitecture.md` with Refined/Curated zones, database-first Taxonomy Control Plane (Postgres/Mongo; zero flat files), Mode 2 classification, Vector DB Store (Chroma + multi-cloud), Airflow DAG plane, and Query AST Gateway. No Middleware/Portals/DAG product code until each story is started.

**Status: Open.** Stories left to build: 2. Stories already done: 1.

**Product policy (2026-11-19):** Documentation-only milestones are discontinued. Prefer shipping architecture sections as Superpowers brainstorming/plan artifacts inside **product** milestones (M45+). M41 docs may proceed later but **must not block** Raw hydrate (M45) or subsequent working-product milestones.

**GitHub Milestone:** M41 - DataArchitecture full lakehouse (Refined/Curated/Taxonomy/Vectors) (api id 42)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #314 | M41-0001 | Story | Docs: DataArchitecture Refined + Curated Iceberg zones |
| 2 | #315 | M41-0002 | Story | Docs: DataArchitecture Database Taxonomy Control Plane |
| 3 | #316 | M41-0003 | Story | Docs: DataArchitecture Vector Store + Mode 2 + orchestration |

## 2. Superpowers workflow

One chat per story. Run the commands of a story from top to bottom. `/ccaa-*` are the project skills; the others come from the Superpowers plugin.

Every command has its own row with a **Status** (`Planned` / `Not started`, `In progress`, `Done`, or `Skipped (abbrev)`), a **Started** date and a **Completed** date (`—` until set). The step that is `In progress` is the one to run next. When a step finishes, `/ccaa-milestone-log N` marks it `Done` and starts the next step. `/ccaa-story-start` and `/ccaa-story-complete` log their own step. Changes ship with the next `/ccaa-commit-push`.

**Standard code/docs story (N = issue number) — do not abbreviate:**

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Marks the issue in progress and refreshes the feature and epic |
| 2 | `/brainstorming Story #N ...` | Confirms design; writes/updates `docs/Superpowers/specs/…-design.md` when applicable |
| 3 | `/using-git-worktrees Story #N: branch ...` | Isolated workspace on a new branch |
| 4 | `/writing-plans Story #N` | Task plan → `docs/Superpowers/plans/…-plan.md` |
| 5 | `/test-driven-development Story #N` | RED-GREEN-REFACTOR rules (adapt for docs-only stories) |
| 6 | `/subagent-driven-development Story #N` | Build each task (or `/executing-plans Story #N`) |
| 7 | `/ccaa-commit-push N` | After every task of step 6 (repeat) |
| 8 | `/verification-before-completion Story #N` | Lint/tests/acceptance check |
| 9 | `/requesting-code-review Story #N` | Review against the plan |
| 10 | `/ccaa-commit-push N` | Review fixes |
| 11 | `/finishing-a-development-branch Story #N` | Merge/PR/cleanup worktree |
| 12 | `/ccaa-story-complete N` | Tick acceptance, close story |

If a test fails and you do not know why, run `/systematic-debugging Story #N` before changing code.

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #314 | 1 | `/ccaa-story-start 314` | Done | 2026-11-19 17:46 | 2026-11-19 17:48 |
| #314 | 2 | `/brainstorming Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 3 | `/using-git-worktrees Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 4 | `/writing-plans Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 5 | `/test-driven-development Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 6 | `/subagent-driven-development Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 7 | `/ccaa-commit-push 314 (after each task)` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 8 | `/verification-before-completion Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 9 | `/requesting-code-review Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 10 | `/ccaa-commit-push 314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
| #314 | 11 | `/finishing-a-development-branch Story #314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
<<<<<<< HEAD
| #314 | 12 | `/ccaa-story-complete 314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
=======
| #314 | 12 | `/ccaa-story-complete 314` | Done | 2026-11-19 17:48 | 2026-11-19 17:48 |
>>>>>>> e275cf2 (M41-0001 #314: complete story)
| #315 | 1 | `/ccaa-story-start 315` | Not started | — | — |
| #315 | 2 | `/brainstorming Story #315` | Not started | — | — |
| #315 | 3 | `/using-git-worktrees Story #315` | Not started | — | — |
| #315 | 4 | `/writing-plans Story #315` | Not started | — | — |
| #315 | 5 | `/test-driven-development Story #315` | Not started | — | — |
| #315 | 6 | `/subagent-driven-development Story #315` | Not started | — | — |
| #315 | 7 | `/ccaa-commit-push 315 (after each task)` | Not started | — | — |
| #315 | 8 | `/verification-before-completion Story #315` | Not started | — | — |
| #315 | 9 | `/requesting-code-review Story #315` | Not started | — | — |
| #315 | 10 | `/ccaa-commit-push 315` | Not started | — | — |
| #315 | 11 | `/finishing-a-development-branch Story #315` | Not started | — | — |
| #315 | 12 | `/ccaa-story-complete 315` | Not started | — | — |
| #316 | 1 | `/ccaa-story-start 316` | Not started | — | — |
| #316 | 2 | `/brainstorming Story #316` | Not started | — | — |
| #316 | 3 | `/using-git-worktrees Story #316` | Not started | — | — |
| #316 | 4 | `/writing-plans Story #316` | Not started | — | — |
| #316 | 5 | `/test-driven-development Story #316` | Not started | — | — |
| #316 | 6 | `/subagent-driven-development Story #316` | Not started | — | — |
| #316 | 7 | `/ccaa-commit-push 316 (after each task)` | Not started | — | — |
| #316 | 8 | `/verification-before-completion Story #316` | Not started | — | — |
| #316 | 9 | `/requesting-code-review Story #316` | Not started | — | — |
| #316 | 10 | `/ccaa-commit-push 316` | Not started | — | — |
| #316 | 11 | `/finishing-a-development-branch Story #316` | Not started | — | — |
| #316 | 12 | `/ccaa-story-complete 316` | Not started | — | — |

## 3. Empirical calibration (for doc content)

| Slice | N | U_prod | U_sig | % Cross-Cutting |
|---|---:|---:|---:|---:|
| 3-month | 1,970,702 | 55 | 2,924 | 0.345% |
| Full archive | 19,170,856 | 127 | 8,438 | 0.764% |

Mode snap: **Mode 2** (Semantic Signature Registry + Hybrid Rules/NLI).
