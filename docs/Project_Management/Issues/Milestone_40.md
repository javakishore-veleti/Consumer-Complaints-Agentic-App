# Milestone M40 - DataArchitecture Raw Zone + Iceberg Docker

**Scope:** Docs story #310 for DataArchitecture.md Raw Zone; Infra story #311 for Iceberg Spark Docker (planned until story-start). No product code under #310.

**Status: Closed.** Stories left to build: 0. Stories already done: 2 (#310, #311).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #310 | M40-0001 | Story | Docs: DataArchitecture.md Raw Data Zone (Iceberg Bronze) |
| 2 | #311 | M40-0002 | Story | Infra: Apache Iceberg Spark Docker container for Raw Zone |

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
| #310 | 1 | `/ccaa-story-start 310` | Done | 2026-11-18 15:37 | 2026-11-18 15:37 |
| #310 | 2 | `/brainstorming Story #310` | Skipped (abbrev) | — | — |
| #310 | 3 | `/using-git-worktrees Story #310` | Skipped (abbrev) | — | — |
| #310 | 4 | `/writing-plans Story #310` | Skipped (abbrev) | — | — |
| #310 | 5 | `/test-driven-development Story #310` | Skipped (abbrev) | — | — |
| #310 | 6 | `/subagent-driven-development Story #310` | Skipped (abbrev) | — | — |
| #310 | 7 | `/ccaa-commit-push 310 (after each task)` | Skipped (abbrev) | — | — |
| #310 | 8 | `/verification-before-completion Story #310` | Skipped (abbrev) | — | — |
| #310 | 9 | `/requesting-code-review Story #310` | Skipped (abbrev) | — | — |
| #310 | 10 | `/ccaa-commit-push 310` | Skipped (abbrev) | — | — |
| #310 | 11 | `/finishing-a-development-branch Story #310` | Skipped (abbrev) | — | — |
| #310 | 12 | `/ccaa-story-complete 310` | Done | 2026-11-18 15:38 | 2026-11-18 15:38 |
| #311 | 1 | `/ccaa-story-start 311` | Done | 2026-11-18 15:39 | 2026-11-18 15:39 |
| #311 | 2 | `/brainstorming Story #311` | Skipped (abbrev) | — | — |
| #311 | 3 | `/using-git-worktrees Story #311` | Skipped (abbrev) | — | — |
| #311 | 4 | `/writing-plans Story #311` | Skipped (abbrev) | — | — |
| #311 | 5 | `/test-driven-development Story #311` | Skipped (abbrev) | — | — |
| #311 | 6 | `/subagent-driven-development Story #311` | Skipped (abbrev) | — | — |
| #311 | 7 | `/ccaa-commit-push 311 (after each task)` | Skipped (abbrev) | — | — |
| #311 | 8 | `/verification-before-completion Story #311` | Skipped (abbrev) | — | — |
| #311 | 9 | `/requesting-code-review Story #311` | Skipped (abbrev) | — | — |
| #311 | 10 | `/ccaa-commit-push 311` | Skipped (abbrev) | — | — |
| #311 | 11 | `/finishing-a-development-branch Story #311` | Skipped (abbrev) | — | — |
| #311 | 12 | `/ccaa-story-complete 311` | Done | 2026-11-18 15:49 | 2026-11-18 15:49 |

**Note:** Rows marked `Skipped (abbrev)` record that this story was previously closed on a 4-step shortcut (story-start → implement → commit-push → story-complete) without `/brainstorming` / `/writing-plans` artifacts under `docs/Superpowers/`. New stories must use the full 12-step path.

## 3. Clarification (2026-11-19)

M40 **did not** finish Lift → Iceberg Raw **hydrate**. #310 = architecture docs; #311 = Spark/Iceberg Docker + Lift mount contract (explicitly no DAG). Raw table population is **M45**.
