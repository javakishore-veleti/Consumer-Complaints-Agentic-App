# Milestone M45 - Raw Iceberg ingest (Lift → raw.cfpb_complaints_*)

**Type:** Working **product** milestone (not docs-only).

**Demoable outcome:** Operator can `SELECT COUNT(*) FROM raw.cfpb_complaints_3m` after Lift→Iceberg hydrate and reconcile to ~1.97M.

**Scope:** Implement Lift Zone → Apache Iceberg **Raw hydrate**. M40 (#310/#311) delivered Raw **docs** + Iceberg Spark **Docker** only — ingest was explicitly future. No Refined/Curated. No product/DAG code until each story is `/ccaa-story-start`.

**Status: Open.** Stories left to build: 1 (closing #323). Stories already done: 3.

**GitHub Milestone:** M45 - Raw Iceberg ingest (Lift → raw.cfpb_complaints_*) (api id 46)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #320 | M45-0001 | Story | Raw Iceberg: DDL + raw namespace table templates |
| 2 | #321 | M45-0002 | Story | Raw Iceberg: PySpark Lift→Raw hydrate for 3m |
| 3 | #322 | M45-0003 | Story | Raw Iceberg: Airflow DAG sensor/unzip/DQ/cleanup |
| 4 | #323 | M45-0004 | Story | Raw Iceberg: prove 3m count reconcile + SparkSQL |

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
| #320 | 1 | `/ccaa-story-start 320` | Done | 2026-11-19 12:24 | 2026-11-19 12:25 |
| #320 | 2 | `/brainstorming Story #320` | Done | 2026-11-19 12:25 | 2026-11-19 12:25 |
| #320 | 3 | `/using-git-worktrees Story #320` | Done | 2026-11-19 12:25 | 2026-11-19 12:25 |
| #320 | 4 | `/writing-plans Story #320` | Done | 2026-11-19 12:25 | 2026-11-19 12:25 |
| #320 | 5 | `/test-driven-development Story #320` | Done | 2026-11-19 12:25 | 2026-11-19 12:26 |
| #320 | 6 | `/subagent-driven-development Story #320` | Done | 2026-11-19 12:26 | 2026-11-19 12:26 |
| #320 | 7 | `/ccaa-commit-push 320 (after each task)` | Done | 2026-11-19 12:26 | 2026-11-19 12:26 |
| #320 | 8 | `/verification-before-completion Story #320` | Done | 2026-11-19 12:26 | 2026-11-19 12:26 |
| #320 | 9 | `/requesting-code-review Story #320` | Done | 2026-11-19 12:26 | 2026-11-19 12:26 |
| #320 | 10 | `/ccaa-commit-push 320` | Done | 2026-11-19 12:26 | 2026-11-19 12:26 |
| #320 | 11 | `/finishing-a-development-branch Story #320` | Done | 2026-11-19 12:26 | 2026-11-19 12:27 |
| #320 | 12 | `/ccaa-story-complete 320` | Done | 2026-11-19 12:27 | 2026-11-19 12:27 |
| #321 | 1 | `/ccaa-story-start 321` | Not started | — | — |
| #321 | 2 | `/brainstorming Story #321` | Done | 2026-11-19 12:27 | 2026-11-19 12:30 |
| #321 | 3 | `/using-git-worktrees Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 4 | `/writing-plans Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 5 | `/test-driven-development Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 6 | `/subagent-driven-development Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 7 | `/ccaa-commit-push 321 (after each task)` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 8 | `/verification-before-completion Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 9 | `/requesting-code-review Story #321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 10 | `/ccaa-commit-push 321` | Done | 2026-11-19 12:30 | 2026-11-19 12:30 |
| #321 | 11 | `/finishing-a-development-branch Story #321` | Done | 2026-11-19 12:31 | 2026-11-19 12:31 |
| #321 | 12 | `/ccaa-story-complete 321` | Done | 2026-11-19 12:31 | 2026-11-19 12:31 |
| #322 | 1 | `/ccaa-story-start 322` | Not started | — | — |
| #322 | 2 | `/brainstorming Story #322` | Done | 2026-11-19 12:33 | 2026-11-19 12:34 |
| #322 | 3 | `/using-git-worktrees Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 4 | `/writing-plans Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 5 | `/test-driven-development Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 6 | `/subagent-driven-development Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 7 | `/ccaa-commit-push 322 (after each task)` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 8 | `/verification-before-completion Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 9 | `/requesting-code-review Story #322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 10 | `/ccaa-commit-push 322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #322 | 11 | `/finishing-a-development-branch Story #322` | Done | 2026-11-19 12:35 | 2026-11-19 12:34 |
| #322 | 12 | `/ccaa-story-complete 322` | Done | 2026-11-19 12:34 | 2026-11-19 12:34 |
| #323 | 1 | `/ccaa-story-start 323` | Not started | — | — |
| #323 | 2 | `/brainstorming Story #323` | Done | 2026-11-19 12:35 | 2026-11-19 12:36 |
| #323 | 3 | `/using-git-worktrees Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 4 | `/writing-plans Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 5 | `/test-driven-development Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 6 | `/subagent-driven-development Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 7 | `/ccaa-commit-push 323 (after each task)` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 8 | `/verification-before-completion Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 9 | `/requesting-code-review Story #323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 10 | `/ccaa-commit-push 323` | Done | 2026-11-19 12:36 | 2026-11-19 12:36 |
| #323 | 11 | `/finishing-a-development-branch Story #323` | In progress | 2026-11-19 12:36 | — |
| #323 | 12 | `/ccaa-story-complete 323` | Not started | — | — |

## 3. Status truth (do not skip)

| Layer | Status |
|---|---|
| Lift Zone zips | Operational |
| Raw architecture docs | Done (M40 #310) |
| Iceberg Spark Docker | Done (M40 #311) |
| Raw **ingest into Iceberg tables** | **Done for 3m** — #320–#323 (COUNT=1,970,702) |
| Refined / Curated implement | Unblocked for milestoned stories (M46+) |

## 4. Commands (skills)

- `/ccaa-story-start N` — required before any product/DAG work on story N
- worktree → implement (Superpowers)
- `/ccaa-commit-push N`
- `/ccaa-story-complete N`
- `/ccaa-milestone-log N` after each step
