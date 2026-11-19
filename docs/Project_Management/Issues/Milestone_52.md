# Milestone M52 - Intellect Query AST over curated lakehouse

**Type:** Working **product** milestone (not docs-only). See `docs/Project_Management/MILESTONE_POLICY.md`.

**Demoable outcome:** Intellect runs Query AST against curated 3m via Middleware API (not npm-only prove).

**Status: Open.** Stories left to build: 2. Stories already done: 1.

**GitHub Milestone:** M52 - Intellect Query AST over curated lakehouse (api id 53)

**Feature:** #351

## Design (control loop)

```text
Intellect portal → POST /intellect/query-ast (Middleware)
  → validate AST → SparkSQL (query_ast)
  → optional execute vs Iceberg curated.cfpb_complaints_3m
  → hits / count (k-anon ≥10)
```

Also: ladder `config` for Chroma `cfpb_semantic_signatures` (M49).

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 0 | #351 | M52-0000 | Feature | Intellect Query AST over curated lakehouse |
| 1 | #352 | M52-0001 | Story | Middleware POST /intellect/query-ast |
| 2 | #353 | M52-0002 | Story | Intellect portal Query AST mode |
| 3 | #354 | M52-0003 | Story | Chroma signatures retrieval config |

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
| #352 | 1 | `/ccaa-story-start 352` | Done | 2026-11-19 17:18 | 2026-11-19 17:18 |
| #352 | 2 | `/brainstorming Story #352` | Done | 2026-11-19 17:18 | 2026-11-19 17:18 |
| #352 | 3 | `/using-git-worktrees Story #352` | Done | 2026-11-19 17:18 | 2026-11-19 17:18 |
| #352 | 4 | `/writing-plans Story #352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 5 | `/test-driven-development Story #352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 6 | `/subagent-driven-development Story #352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 7 | `/ccaa-commit-push 352 (after each task)` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 8 | `/verification-before-completion Story #352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 9 | `/requesting-code-review Story #352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 10 | `/ccaa-commit-push 352` | Done | 2026-11-19 17:22 | 2026-11-19 17:22 |
| #352 | 11 | `/finishing-a-development-branch Story #352` | Done | 2026-11-19 17:24 | 2026-11-19 17:24 |
| #352 | 12 | `/ccaa-story-complete 352` | Done | 2026-11-19 17:24 | 2026-11-19 17:24 |
| #353 | 1 | `/ccaa-story-start 353` | Done | 2026-11-19 17:26 | 2026-11-19 17:26 |
| #353 | 2 | `/brainstorming Story #353` | Done | 2026-11-19 17:26 | 2026-11-19 17:26 |
| #353 | 3 | `/using-git-worktrees Story #353` | Done | 2026-11-19 17:26 | 2026-11-19 17:26 |
| #353 | 4 | `/writing-plans Story #353` | Done | 2026-11-19 17:26 | 2026-11-19 17:26 |
| #353 | 5 | `/test-driven-development Story #353` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 6 | `/subagent-driven-development Story #353` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 7 | `/ccaa-commit-push 353 (after each task)` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 8 | `/verification-before-completion Story #353` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 9 | `/requesting-code-review Story #353` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 10 | `/ccaa-commit-push 353` | Done | 2026-11-19 17:27 | 2026-11-19 17:27 |
| #353 | 11 | `/finishing-a-development-branch Story #353` | In progress | 2026-11-19 17:27 | - |
| #353 | 12 | `/ccaa-story-complete 353` | Planned | - | - |
| #354 | 1 | `/ccaa-story-start 354` | Planned | - | - |
| #354 | 2 | `/brainstorming Story #354` | Planned | - | - |
| #354 | 3 | `/using-git-worktrees Story #354` | Planned | - | - |
| #354 | 4 | `/writing-plans Story #354` | Planned | - | - |
| #354 | 5 | `/test-driven-development Story #354` | Planned | - | - |
| #354 | 6 | `/subagent-driven-development Story #354` | Planned | - | - |
| #354 | 7 | `/ccaa-commit-push 354 (after each task)` | Planned | - | - |
| #354 | 8 | `/verification-before-completion Story #354` | Planned | - | - |
| #354 | 9 | `/requesting-code-review Story #354` | Planned | - | - |
| #354 | 10 | `/ccaa-commit-push 354` | Planned | - | - |
| #354 | 11 | `/finishing-a-development-branch Story #354` | Planned | - | - |
| #354 | 12 | `/ccaa-story-complete 354` | Planned | - | - |
