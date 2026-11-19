# Milestone M31 - README Airflow parallel Chroma pipeline

**Scope:** README.md only — Airflow parallel 14-CSV Chroma pipeline. No product code.

**Status: Closed.** Stories left to build: 0. Stories already done: 1 (#292).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #292 | M31-0001 | Story | README: Airflow parallel Chroma for 14 CSVs |

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
| #292 | 1 | `/ccaa-story-start 292` | Done | 2026-11-18 01:21 | 2026-11-18 01:21 |
| #292 | 2 | `/brainstorming Story #292` | Skipped (abbrev) | — | — |
| #292 | 3 | `/using-git-worktrees Story #292` | Skipped (abbrev) | — | — |
| #292 | 4 | `/writing-plans Story #292` | Skipped (abbrev) | — | — |
| #292 | 5 | `/test-driven-development Story #292` | Skipped (abbrev) | — | — |
| #292 | 6 | `/subagent-driven-development Story #292` | Skipped (abbrev) | — | — |
| #292 | 7 | `/ccaa-commit-push 292 (after each task)` | Skipped (abbrev) | — | — |
| #292 | 8 | `/verification-before-completion Story #292` | Skipped (abbrev) | — | — |
| #292 | 9 | `/requesting-code-review Story #292` | Skipped (abbrev) | — | — |
| #292 | 10 | `/ccaa-commit-push 292` | Skipped (abbrev) | — | — |
| #292 | 11 | `/finishing-a-development-branch Story #292` | Skipped (abbrev) | — | — |
| #292 | 12 | `/ccaa-story-complete 292` | Done | 2026-11-18 01:22 | 2026-11-18 01:22 |

**Note:** Rows marked `Skipped (abbrev)` record that this story was previously closed on a 4-step shortcut (story-start → implement → commit-push → story-complete) without `/brainstorming` / `/writing-plans` artifacts under `docs/Superpowers/`. New stories must use the full 12-step path.

