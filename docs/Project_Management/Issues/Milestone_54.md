# Milestone M54 - Query AST zero-hit relaxation

**Type:** Working **product** milestone (not docs-only). See `docs/Project_Management/MILESTONE_POLICY.md`.

**Demoable outcome:** Narrow AST with `relax: true` broadens predicates and returns an explanation trail + usable SQL/count (k-anon ≥10).

**Status: Open.** Stories left to build: 3. Stories already done: 0.

**GitHub Milestone:** M54 - Query AST zero-hit relaxation (api id 55)

**Feature:** #365

## Design (control loop)

```text
Intellect AST form (relax ✓) → POST /intellect/query-ast {ast, execute, relax}
  → translate → optional execute
  → if empty / !k_anon_ok → ordered broaden steps → re-translate/execute
  → response.relaxation[] + sql/count
```

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 0 | #365 | M54-0000 | Feature | Query AST zero-hit relaxation |
| 1 | #366 | M54-0001 | Story | Middleware Query AST relaxation engine |
| 2 | #367 | M54-0002 | Story | Intellect portal show AST relaxation trail |
| 3 | #368 | M54-0003 | Story | Golden zero-hit relaxation cases |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #366 | 1 | `/ccaa-story-start 366` | Planned | - | - |
| #366 | 2 | `/brainstorming Story #366` | Planned | - | - |
| #366 | 3 | `/using-git-worktrees Story #366` | Planned | - | - |
| #366 | 4 | `/writing-plans Story #366` | Planned | - | - |
| #366 | 5 | `/test-driven-development Story #366` | Planned | - | - |
| #366 | 6 | `/subagent-driven-development Story #366` | Planned | - | - |
| #366 | 7 | `/ccaa-commit-push 366 (after each task)` | Planned | - | - |
| #366 | 8 | `/verification-before-completion Story #366` | Planned | - | - |
| #366 | 9 | `/requesting-code-review Story #366` | Planned | - | - |
| #366 | 10 | `/ccaa-commit-push 366` | Planned | - | - |
| #366 | 11 | `/finishing-a-development-branch Story #366` | Planned | - | - |
| #366 | 12 | `/ccaa-story-complete 366` | Planned | - | - |
| #367 | 1 | `/ccaa-story-start 367` | Planned | - | - |
| #367 | 2 | `/brainstorming Story #367` | Planned | - | - |
| #367 | 3 | `/using-git-worktrees Story #367` | Planned | - | - |
| #367 | 4 | `/writing-plans Story #367` | Planned | - | - |
| #367 | 5 | `/test-driven-development Story #367` | Planned | - | - |
| #367 | 6 | `/subagent-driven-development Story #367` | Planned | - | - |
| #367 | 7 | `/ccaa-commit-push 367 (after each task)` | Planned | - | - |
| #367 | 8 | `/verification-before-completion Story #367` | Planned | - | - |
| #367 | 9 | `/requesting-code-review Story #367` | Planned | - | - |
| #367 | 10 | `/ccaa-commit-push 367` | Planned | - | - |
| #367 | 11 | `/finishing-a-development-branch Story #367` | Planned | - | - |
| #367 | 12 | `/ccaa-story-complete 367` | Planned | - | - |
| #368 | 1 | `/ccaa-story-start 368` | Planned | - | - |
| #368 | 2 | `/brainstorming Story #368` | Planned | - | - |
| #368 | 3 | `/using-git-worktrees Story #368` | Planned | - | - |
| #368 | 4 | `/writing-plans Story #368` | Planned | - | - |
| #368 | 5 | `/test-driven-development Story #368` | Planned | - | - |
| #368 | 6 | `/subagent-driven-development Story #368` | Planned | - | - |
| #368 | 7 | `/ccaa-commit-push 368 (after each task)` | Planned | - | - |
| #368 | 8 | `/verification-before-completion Story #368` | Planned | - | - |
| #368 | 9 | `/requesting-code-review Story #368` | Planned | - | - |
| #368 | 10 | `/ccaa-commit-push 368` | Planned | - | - |
| #368 | 11 | `/finishing-a-development-branch Story #368` | Planned | - | - |
| #368 | 12 | `/ccaa-story-complete 368` | Planned | - | - |
