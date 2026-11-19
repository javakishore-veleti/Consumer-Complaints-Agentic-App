# Milestone M44 - Future Requirements board doc (Nightwing gap closure track)

**Scope:** Board docs only — `docs/Project_Management/Future_Requirements.md`. No Middleware / Portals / DAG / `DataArchitecture.md` edits.

**Status: Closed (docs complete; product milestones are M45+).** Stories left to build: 0 after commit-push (story-complete pending). Stories already done: 0.

**GitHub Milestone:** M44 - Future Requirements board doc (Nightwing gap closure track) (api id 45)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #319 | M44-0001 | Story | Docs: Future_Requirements.md (cyber SOC AI / ATO gap track) |

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
| #319 | 1 | `/ccaa-story-start 319` | Board allow-list path (Project_Management) | 2026-11-18 20:59 | 2026-11-18 20:59 |
| #319 | 2 | `/brainstorming Story #319` | Not started | — | — |
| #319 | 3 | `/using-git-worktrees Story #319` | Not started | — | — |
| #319 | 4 | `/writing-plans Story #319` | Not started | — | — |
| #319 | 5 | `/test-driven-development Story #319` | Not started | — | — |
| #319 | 6 | `/subagent-driven-development Story #319` | Not started | — | — |
| #319 | 7 | `/ccaa-commit-push 319 (after each task)` | Not started | — | — |
| #319 | 8 | `/verification-before-completion Story #319` | Not started | — | — |
| #319 | 9 | `/requesting-code-review Story #319` | Not started | — | — |
| #319 | 10 | `/ccaa-commit-push 319` | Not started | — | — |
| #319 | 11 | `/finishing-a-development-branch Story #319` | Not started | — | — |
| #319 | 12 | `/ccaa-story-complete 319` | Not started | — | — |

