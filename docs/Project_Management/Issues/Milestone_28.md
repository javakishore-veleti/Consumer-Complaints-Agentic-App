# Milestone M28 - README embedding validation 15 min

**Scope:** README.md only — How to Validate Your Choice in 15 Minutes. No product code.

**Status: Closed.** Stories left to build: 0. Stories already done: 1 (#286).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #286 | M28-0001 | Story | README: validate embedding choice in 15 minutes |

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
| #286 | 1 | `/ccaa-story-start 286` | Done | 2026-11-18 01:16 | 2026-11-18 01:16 |
| #286 | 2 | `/brainstorming Story #286` | Skipped (abbrev) | — | — |
| #286 | 3 | `/using-git-worktrees Story #286` | Skipped (abbrev) | — | — |
| #286 | 4 | `/writing-plans Story #286` | Skipped (abbrev) | — | — |
| #286 | 5 | `/test-driven-development Story #286` | Skipped (abbrev) | — | — |
| #286 | 6 | `/subagent-driven-development Story #286` | Skipped (abbrev) | — | — |
| #286 | 7 | `/ccaa-commit-push 286 (after each task)` | Skipped (abbrev) | — | — |
| #286 | 8 | `/verification-before-completion Story #286` | Skipped (abbrev) | — | — |
| #286 | 9 | `/requesting-code-review Story #286` | Skipped (abbrev) | — | — |
| #286 | 10 | `/ccaa-commit-push 286` | Skipped (abbrev) | — | — |
| #286 | 11 | `/finishing-a-development-branch Story #286` | Skipped (abbrev) | — | — |
| #286 | 12 | `/ccaa-story-complete 286` | Done | 2026-11-18 01:17 | 2026-11-18 01:17 |

**Note:** Rows marked `Skipped (abbrev)` record that this story was previously closed on a 4-step shortcut (story-start → implement → commit-push → story-complete) without `/brainstorming` / `/writing-plans` artifacts under `docs/Superpowers/`. New stories must use the full 12-step path.

