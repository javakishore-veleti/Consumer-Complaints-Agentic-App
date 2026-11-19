# Milestone M43 - AI Capabilities & Solutions board doc

**Scope:** Board docs only — `docs/Project_Management/AI_Capabilities_Solutions.md` (Platform / Internal / B2B / Consumer AI). No Middleware / Portals / DAG / `DataArchitecture.md` edits.

**Status: Closed (docs complete; product milestones are M45+).** Stories left to build: 1 (awaiting commit-push + story-complete). Stories already done: 0.

**GitHub Milestone:** M43 - AI Capabilities & Solutions board doc (api id 44)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #318 | M43-0001 | Story | Docs: AI Capabilities & Solutions (Platform/Internal/B2B/Consumer) |

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
| #318 | 1 | `/ccaa-story-start 318` | Board allow-list path (Project_Management) | 2026-11-18 20:27 | 2026-11-18 20:27 |
| #318 | 2 | `/brainstorming Story #318` | Not started | — | — |
| #318 | 3 | `/using-git-worktrees Story #318` | Not started | — | — |
| #318 | 4 | `/writing-plans Story #318` | Not started | — | — |
| #318 | 5 | `/test-driven-development Story #318` | Not started | — | — |
| #318 | 6 | `/subagent-driven-development Story #318` | Not started | — | — |
| #318 | 7 | `/ccaa-commit-push 318 (after each task)` | Not started | — | — |
| #318 | 8 | `/verification-before-completion Story #318` | Not started | — | — |
| #318 | 9 | `/requesting-code-review Story #318` | Not started | — | — |
| #318 | 10 | `/ccaa-commit-push 318` | Not started | — | — |
| #318 | 11 | `/finishing-a-development-branch Story #318` | Not started | — | — |
| #318 | 12 | `/ccaa-story-complete 318` | Not started | — | — |

