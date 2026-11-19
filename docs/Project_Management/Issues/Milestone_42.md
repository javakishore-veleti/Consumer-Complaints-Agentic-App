# Milestone M42 - Project Charter refresh (DataArchitecture alignment)

**Scope:** Board docs only — refresh `PROJECT_CHARTER.md` to align with Mode 2 lakehouse architecture. No product code.

**Status: Closed (docs complete; product milestones are M45+).** Stories left to build: 1 (awaiting commit-push + story-complete). Stories already done: 0.

**GitHub Milestone:** M42 - Project Charter refresh (DataArchitecture alignment) (api id 43)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #317 | M42-0001 | Story | Docs: refresh Project Charter for DataArchitecture alignment |

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
| #317 | 1 | `/ccaa-story-start 317` | Board allow-list path (Project_Management) | 2026-11-18 20:04 | 2026-11-18 20:04 |
| #317 | 2 | `/brainstorming Story #317` | Not started | — | — |
| #317 | 3 | `/using-git-worktrees Story #317` | Not started | — | — |
| #317 | 4 | `/writing-plans Story #317` | Not started | — | — |
| #317 | 5 | `/test-driven-development Story #317` | Not started | — | — |
| #317 | 6 | `/subagent-driven-development Story #317` | Not started | — | — |
| #317 | 7 | `/ccaa-commit-push 317 (after each task)` | Not started | — | — |
| #317 | 8 | `/verification-before-completion Story #317` | Not started | — | — |
| #317 | 9 | `/requesting-code-review Story #317` | Not started | — | — |
| #317 | 10 | `/ccaa-commit-push 317` | Not started | — | — |
| #317 | 11 | `/finishing-a-development-branch Story #317` | Not started | — | — |
| #317 | 12 | `/ccaa-story-complete 317` | Not started | — | — |

## 3. Alignment notes captured in charter

- Empirical Mode 2 (1.97M / 19.17M; U_sig 2,924 / 8,438; cross-cutting &lt; 1%)
- Lift → Raw → Refined → Curated Iceberg; database-first taxonomy (no flat YAML/CSV)
- Compact vector catalogs (~17k); Curated Iceberg = fact SoR
- Portfolio links M40 (done) and M41 (DataArchitecture expansion)
