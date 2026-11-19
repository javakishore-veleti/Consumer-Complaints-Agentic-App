# Milestone M53 - Internal Systemic Risk Radar MVP

**Type:** Working **product** milestone (not docs-only). See `docs/Project_Management/MILESTONE_POLICY.md`.

**Demoable outcome:** Intellect Risk Radar alert feed from Middleware; click alert → Query AST drill-down (k-anon ≥10). Fixture path works without warehouse.

**Status: Open.** Stories left to build: 3. Stories already done: 0.

**GitHub Milestone:** M53 - Internal Systemic Risk Radar MVP (api id 54)

**Feature:** #358

## Design (control loop)

```text
Intellect Risk Radar panel → GET/POST /intellect/risk-radar (Middleware)
  → fixture alerts (CI) or warehouse cohort velocity
  → alert.drilldown_ast → POST /intellect/query-ast
  → SQL / count (k-anon ≥10)
```

Charter P6 crawl: Systemic Risk Radar (minimal viable). No LLM required for MVP.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 0 | #358 | M53-0000 | Feature | Internal Systemic Risk Radar MVP |
| 1 | #359 | M53-0001 | Story | Middleware GET/POST /intellect/risk-radar |
| 2 | #360 | M53-0002 | Story | Intellect portal Risk Radar alert feed |
| 3 | #361 | M53-0003 | Story | Alert → Query AST drill-down |

## 2. Superpowers workflow

One chat per story. Full **12-step** path (M02 standard). Do **not** abbreviate.

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Start story |
| 2 | `/brainstorming Story #N` | Design → Superpowers spec |
| 3 | `/using-git-worktrees Story #N` | Worktree/branch |
| 4 | `/writing-plans Story #N` | Plan → Superpowers plans |
| 5 | `/test-driven-development Story #N` | TDD |
| 6 | `/subagent-driven-development Story #N` | Implement |
| 7 | `/ccaa-commit-push N` | After each task |
| 8 | `/verification-before-completion Story #N` | Prove Done-when |
| 9 | `/requesting-code-review Story #N` | Review |
| 10 | `/ccaa-commit-push N` | Review fixes |
| 11 | `/finishing-a-development-branch Story #N` | Merge/PR |
| 12 | `/ccaa-story-complete N` | Close story |

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #359 | 1 | `/ccaa-story-start 359` | Done | 2026-11-19 17:40 | 2026-11-19 17:40 |
| #359 | 2 | `/brainstorming Story #359` | In progress | 2026-11-19 17:40 | - |
| #359 | 3 | `/using-git-worktrees Story #359` | Planned | - | - |
| #359 | 4 | `/writing-plans Story #359` | Planned | - | - |
| #359 | 5 | `/test-driven-development Story #359` | Planned | - | - |
| #359 | 6 | `/subagent-driven-development Story #359` | Planned | - | - |
| #359 | 7 | `/ccaa-commit-push 359 (after each task)` | Planned | - | - |
| #359 | 8 | `/verification-before-completion Story #359` | Planned | - | - |
| #359 | 9 | `/requesting-code-review Story #359` | Planned | - | - |
| #359 | 10 | `/ccaa-commit-push 359` | Planned | - | - |
| #359 | 11 | `/finishing-a-development-branch Story #359` | Planned | - | - |
| #359 | 12 | `/ccaa-story-complete 359` | Planned | - | - |
| #360 | 1 | `/ccaa-story-start 360` | Planned | - | - |
| #360 | 2 | `/brainstorming Story #360` | Planned | - | - |
| #360 | 3 | `/using-git-worktrees Story #360` | Planned | - | - |
| #360 | 4 | `/writing-plans Story #360` | Planned | - | - |
| #360 | 5 | `/test-driven-development Story #360` | Planned | - | - |
| #360 | 6 | `/subagent-driven-development Story #360` | Planned | - | - |
| #360 | 7 | `/ccaa-commit-push 360 (after each task)` | Planned | - | - |
| #360 | 8 | `/verification-before-completion Story #360` | Planned | - | - |
| #360 | 9 | `/requesting-code-review Story #360` | Planned | - | - |
| #360 | 10 | `/ccaa-commit-push 360` | Planned | - | - |
| #360 | 11 | `/finishing-a-development-branch Story #360` | Planned | - | - |
| #360 | 12 | `/ccaa-story-complete 360` | Planned | - | - |
| #361 | 1 | `/ccaa-story-start 361` | Planned | - | - |
| #361 | 2 | `/brainstorming Story #361` | Planned | - | - |
| #361 | 3 | `/using-git-worktrees Story #361` | Planned | - | - |
| #361 | 4 | `/writing-plans Story #361` | Planned | - | - |
| #361 | 5 | `/test-driven-development Story #361` | Planned | - | - |
| #361 | 6 | `/subagent-driven-development Story #361` | Planned | - | - |
| #361 | 7 | `/ccaa-commit-push 361 (after each task)` | Planned | - | - |
| #361 | 8 | `/verification-before-completion Story #361` | Planned | - | - |
| #361 | 9 | `/requesting-code-review Story #361` | Planned | - | - |
| #361 | 10 | `/ccaa-commit-push 361` | Planned | - | - |
| #361 | 11 | `/finishing-a-development-branch Story #361` | Planned | - | - |
| #361 | 12 | `/ccaa-story-complete 361` | Planned | - | - |
