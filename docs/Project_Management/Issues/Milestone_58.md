# Milestone M58 - Admin Schemas foundational data-plane DDL

**Type:** Working **product** milestone.

**Demoable outcome:** Admin **Schemas** starts one Iceberg foundational-schema workflow that applies Raw → Refined → Taxonomy → Curated DDL via Middleware → Airflow → status callback. Postgres app migrate stays on npm. Operator data-plane schema work is UI/DAG, not `npm run local:iceberg:apply-*`.

**Status: Open.** Stories left to build: 1. Stories already done: 0.

**GitHub Milestone:** M58 - Admin Schemas foundational data-plane DDL (api id 59)

## Design notes

- Foundational = data-plane stores (Iceberg now; Mongo/S3/Cosmos later). **Not** CCA operational Postgres.
- One WF per store; Iceberg WF does **all zones** in one run.
- Hydrate stays on **Lakehouse**.

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #400 | M58-0001 | Story | Admin Schemas + Iceberg foundational schema DAG |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #400 | 1 | `/ccaa-story-start 400` | Done | 2026-11-20 10:53 | 2026-11-20 10:53 |
| #400 | 2 | `/brainstorming Story #400` | In progress | 2026-11-20 10:53 | - |
| #400 | 3 | `/using-git-worktrees Story #400` | Planned | - | - |
| #400 | 4 | `/writing-plans Story #400` | Planned | - | - |
| #400 | 5 | `/test-driven-development Story #400` | Planned | - | - |
| #400 | 6 | `/subagent-driven-development Story #400` | Planned | - | - |
| #400 | 7 | `/ccaa-commit-push 400 (after each task)` | Planned | - | - |
| #400 | 8 | `/verification-before-completion Story #400` | Planned | - | - |
| #400 | 9 | `/requesting-code-review Story #400` | Planned | - | - |
| #400 | 10 | `/ccaa-commit-push 400` | Planned | - | - |
| #400 | 11 | `/finishing-a-development-branch Story #400` | Planned | - | - |
| #400 | 12 | `/ccaa-story-complete 400` | Planned | - | - |
