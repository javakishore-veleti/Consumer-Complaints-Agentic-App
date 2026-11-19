# Milestone M51 - Admin lakehouse workflows (UI → Middleware → Airflow → status)

**Type:** Working **product** milestone (not docs-only). See `docs/Project_Management/MILESTONE_POLICY.md`.

**Demoable outcome:** From Admin **Lakehouse**, start separate hydrate workflows; Middleware triggers Airflow; callbacks update status (same loop as Downloads).

**Status: Open.** Stories left to build: 1. Stories already done: 5.

**GitHub Milestone:** M51 - Admin lakehouse workflows (UI → Middleware → Airflow → status) (api id 52)

**Feature:** #340

## Design (control loop)

```text
Admin Lakehouse → POST /workflows/{id}/start (Middleware)
  → Airflow DAG (engine_workflow_id)
  → POST /callbacks/workflow-executions/{execution_id}/status
  → GET /mios/status (Admin Refresh)
```

Separate workflows (not one mega-DAG): Raw → Refined → Taxonomy Mode 2 → Curated → Chroma signatures.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 0 | #340 | M51-0000 | Feature | Admin-triggerable lakehouse hydrate workflows |
| 1 | #341 | M51-0001 | Story | Admin Lakehouse screen + register hydrate_raw_iceberg_3m |
| 2 | #342 | M51-0002 | Story | Airflow + Admin workflow hydrate_refined_iceberg_3m |
| 3 | #343 | M51-0003 | Story | Airflow + Admin workflow hydrate_taxonomy_mode2_3m |
| 4 | #344 | M51-0004 | Story | Airflow + Admin workflow hydrate_curated_iceberg_3m |
| 5 | #345 | M51-0005 | Story | Airflow + Admin workflow hydrate_chroma_signatures_3m |
| 6 | #349 | M51-0006 | Story | Fix CI seed expectations for hydrate_* workflows |

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
| #341 | 1 | `/ccaa-story-start 341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 2 | `/brainstorming Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 3 | `/using-git-worktrees Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 4 | `/writing-plans Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 5 | `/test-driven-development Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 6 | `/subagent-driven-development Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 7 | `/ccaa-commit-push 341 (after each task)` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 8 | `/verification-before-completion Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 9 | `/requesting-code-review Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 10 | `/ccaa-commit-push 341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 11 | `/finishing-a-development-branch Story #341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #341 | 12 | `/ccaa-story-complete 341` | Done | 2026-11-19 16:09 | 2026-11-19 16:09 |
| #342 | 1 | `/ccaa-story-start 342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 2 | `/brainstorming Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 3 | `/using-git-worktrees Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 4 | `/writing-plans Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 5 | `/test-driven-development Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 6 | `/subagent-driven-development Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 7 | `/ccaa-commit-push 342 (after each task)` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 8 | `/verification-before-completion Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 9 | `/requesting-code-review Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 10 | `/ccaa-commit-push 342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 11 | `/finishing-a-development-branch Story #342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #342 | 12 | `/ccaa-story-complete 342` | Done | 2026-11-19 16:11 | 2026-11-19 16:11 |
| #343 | 1 | `/ccaa-story-start 343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 2 | `/brainstorming Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 3 | `/using-git-worktrees Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 4 | `/writing-plans Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 5 | `/test-driven-development Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 6 | `/subagent-driven-development Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 7 | `/ccaa-commit-push 343 (after each task)` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 8 | `/verification-before-completion Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 9 | `/requesting-code-review Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 10 | `/ccaa-commit-push 343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 11 | `/finishing-a-development-branch Story #343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #343 | 12 | `/ccaa-story-complete 343` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 1 | `/ccaa-story-start 344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 2 | `/brainstorming Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 3 | `/using-git-worktrees Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 4 | `/writing-plans Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 5 | `/test-driven-development Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 6 | `/subagent-driven-development Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 7 | `/ccaa-commit-push 344 (after each task)` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 8 | `/verification-before-completion Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 9 | `/requesting-code-review Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 10 | `/ccaa-commit-push 344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 11 | `/finishing-a-development-branch Story #344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #344 | 12 | `/ccaa-story-complete 344` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 1 | `/ccaa-story-start 345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 2 | `/brainstorming Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 3 | `/using-git-worktrees Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 4 | `/writing-plans Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 5 | `/test-driven-development Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 6 | `/subagent-driven-development Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 7 | `/ccaa-commit-push 345 (after each task)` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 8 | `/verification-before-completion Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 9 | `/requesting-code-review Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 10 | `/ccaa-commit-push 345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 11 | `/finishing-a-development-branch Story #345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #345 | 12 | `/ccaa-story-complete 345` | Done | 2026-11-19 16:15 | 2026-11-19 16:15 |
| #349 | 1 | `/ccaa-story-start 349` | Done | 2026-11-19 16:20 | 2026-11-19 16:20 |
| #349 | 2 | `/brainstorming Story #349` | Done | 2026-11-19 16:20 | 2026-11-19 16:20 |
| #349 | 3 | `/using-git-worktrees Story #349` | Done | 2026-11-19 16:20 | 2026-11-19 16:20 |
| #349 | 4 | `/writing-plans Story #349` | Done | 2026-11-19 16:20 | 2026-11-19 16:20 |
| #349 | 5 | `/test-driven-development Story #349` | Done | 2026-11-19 16:20 | 2026-11-19 16:22 |
| #349 | 6 | `/subagent-driven-development Story #349` | Done | 2026-11-19 16:22 | 2026-11-19 16:22 |
| #349 | 7 | `/ccaa-commit-push 349 (after each task)` | In progress | 2026-11-19 16:22 | - |
| #349 | 8 | `/verification-before-completion Story #349` | Planned | - | - |
| #349 | 9 | `/requesting-code-review Story #349` | Planned | - | - |
| #349 | 10 | `/ccaa-commit-push 349` | Planned | - | - |
| #349 | 11 | `/finishing-a-development-branch Story #349` | Planned | - | - |
| #349 | 12 | `/ccaa-story-complete 349` | Planned | - | - |
