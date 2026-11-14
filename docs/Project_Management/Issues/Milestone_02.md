# Milestone M02 - Downloads Management

**Scope (decision D38 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`):** download the free CFPB dataset on demand from the admin portal, asynchronously through Airflow, through registered workflows (D43), and always show whether it has been downloaded. Everything runs locally. Cloud work is M03.

**Status: in progress.** 1 epic, 5 features and 24 stories. 4 stories (and 1 feature) are already done, 20 stories are left to build.

How to read this file:
- `#42` is the GitHub issue number in this repository. The `M02-00NN` key is the sequence tag at the start of the issue title. Keys are not in build order.
- Section 1 is the table of contents in the order the work should be built. Section 2 groups the same issues as epic, feature and story.
- Section 3 has the Superpowers commands to run for each story, one after the other. Section 4 explains the project skills (`ccaa-`) those commands use.

## Contents

- [1. Table of contents (build order)](#1-table-of-contents-build-order)
  - [Phase 0 - Dataset status, already built (commit `eec398d`)](#phase-0---dataset-status-already-built-commit-eec398d)
  - [Phase 1 - Workflow registry](#phase-1---workflow-registry-nothing-else-can-list-start-or-log-a-workflow-without-it)
  - [Phase 2 - Download API, the status and listing side](#phase-2---download-api-the-status-and-listing-side)
  - [Phase 3 - Airflow download DAG](#phase-3---airflow-download-dag)
  - [Phase 4 - Start a workflow (closes the Download API feature)](#phase-4---start-a-workflow-closes-the-download-api-feature)
  - [Phase 5 - Admin portal](#phase-5---admin-portal)
- [2. The same issues grouped by epic and feature](#2-the-same-issues-grouped-by-epic-and-feature)
- [3. Superpowers workflow](#3-superpowers-workflow)
  - [Phase 1 - Workflow registry](#phase-1---workflow-registry)
  - [Phase 2 - Download API, the status and listing side](#phase-2---download-api-the-status-and-listing-side-1)
  - [Phase 3 - Airflow download DAG](#phase-3---airflow-download-dag-1)
  - [Phase 4 - Start a workflow (closes the Download API feature)](#phase-4---start-a-workflow-closes-the-download-api-feature-1)
  - [Phase 5 - Admin portal](#phase-5---admin-portal-1)
- [4. Project skills](#4-project-skills-ccaa---consumer-complaints-agentic-app)
- [5. Notes](#5-notes)

## 1. Table of contents (build order)

### Phase 0 - Dataset status, already built (commit `eec398d`)

| # | Issue | Key | Type | Title | Status |
|---|---|---|---|---|---|
| 1 | #29 | M02-0001 | Epic | Downloads Management | In progress |
| 2 | #37 | M02-0002 | Feature | Dataset status (system_datasets) | Done |
| 3 | #38 | M02-0003 | Story | system_datasets table and migration | Done |
| 4 | #39 | M02-0004 | Story | system_datasets DAO | Done |
| 5 | #40 | M02-0005 | Story | Record outcome in one transaction | Done |

### Phase 1 - Workflow registry (nothing else can list, start or log a workflow without it)

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 6 | #78 | M02-0028 | Feature | Workflow registry | Parent of the stories below |
| 7 | #79 | M02-0029 | Story | Decide how usecases map to workflows, the admin schema name and the fate of the old log tables | Decision first: the tables and the stories after it depend on the answers |
| 8 | #80 | M02-0030 | Story | Object factory init() and bean registry (D45) | Every class added after it registers itself this way (D45) |
| 9 | #81 | M02-0031 | Story | Admin schema and app_workflows table with its DAO | The registry the portal lists from |
| 10 | #82 | M02-0032 | Story | app_workflows_exec_log table with its DAO | Every run is logged here |

### Phase 2 - Download API, the status and listing side

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 11 | #41 | M02-0006 | Feature | Download API | Parent of the stories below (it finishes in Phase 4) |
| 12 | #44 | M02-0009 | Story | Shared-secret authentication for callbacks | The callback endpoint must be protected from day one |
| 13 | #43 | M02-0008 | Story | Airflow status callback endpoint | Uses #44 and the built `system_datasets` service |
| 14 | #45 | M02-0010 | Story | Read dataset status endpoint | Reads the Phase 0 table; the portal needs it |
| 15 | #83 | M02-0033 | Story | Workflow engine interface and lookup | The Airflow engine (#60) implements it |
| 16 | #84 | M02-0034 | Story | List workflows endpoint | Reads the registry of #81; the portal needs it |

### Phase 3 - Airflow download DAG

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 17 | #56 | M02-0017 | Feature | Airflow download DAG | Parent of the stories below |
| 18 | #55 | M02-0016 | Story | Decide where the location and credentials are stored | Done: decision D42 (values in `.env`, copied into Airflow Variables); #77 builds it |
| 19 | #85 | M02-0035 | Story | Move the DAGs to Middleware/Airflow-dags and mount them by relative path | The DAGs must live in the mounted folder before any is written (D44) |
| 20 | #77 | M02-0027 | Story | Push .env values to Airflow Variables (upsert-secrets endpoint) | Decision D42. Uses the #44 secret; the DAG reads the Variables it creates |
| 21 | #57 | M02-0018 | Story | Download DAG for the All dataset | Reads its own source from the Variables of #77 and is registered in the registry (#81) |
| 22 | #58 | M02-0019 | Story | 3 months dataset: filter the All file by Date received | Derived from the All file, so it follows #57 |
| 23 | #59 | M02-0020 | Story | Report started, completed and failed to the API, even when a task crashes | Calls the Phase 2 callback and uses its secret |
| 24 | #60 | M02-0021 | Story | Airflow engine: start a DAG run asynchronously | Implements the engine interface of #83; the DAG must exist before it can be started |

### Phase 4 - Start a workflow (closes the Download API feature)

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 25 | #42 | M02-0007 | Story | Start-workflow endpoint (one endpoint, any registered workflow) | Starts a registered workflow through the engine of #60 and the lookup of #83 |

### Phase 5 - Admin portal

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 26 | #61 | M02-0022 | Feature | Admin portal: DataSets and Imports | Parent of the stories below |
| 27 | #62 | M02-0023 | Story | Angular app scaffold (consumer-complaints-admin) | Everything in the portal builds on it |
| 28 | #63 | M02-0024 | Story | DataSets top menu and Imports left navigation | Shell for the accordions |
| 29 | #64 | M02-0025 | Story | Two accordions: 3 months and All, with status from the API | Reads the Phase 2 status endpoint (#45) |
| 30 | #65 | M02-0026 | Story | Start download button and status refresh | Calls the Phase 4 endpoint (#42) |

## 2. The same issues grouped by epic and feature

```
Epic #29  M02-0001  Downloads Management
|
+-- Feature #37  M02-0002  Dataset status (system_datasets)            [done]
|     +-- #38  system_datasets table and migration                     [done]
|     +-- #39  system_datasets DAO                                     [done]
|     +-- #40  Record outcome in one transaction                       [done]
|
+-- Feature #78  M02-0028  Workflow registry
|     +-- #79  Decide how usecases map to workflows, the admin schema name and the fate of the old log tables
|     +-- #80  Object factory init() and bean registry (D45)
|     +-- #81  Admin schema and app_workflows table with its DAO
|     +-- #82  app_workflows_exec_log table with its DAO
|
+-- Feature #41  M02-0006  Download API
|     +-- #44  Shared-secret authentication for callbacks
|     +-- #43  Airflow status callback endpoint
|     +-- #45  Read dataset status endpoint
|     +-- #83  Workflow engine interface and lookup
|     +-- #84  List workflows endpoint
|     +-- #42  Start-workflow endpoint (one endpoint, any registered workflow)   (built in Phase 4)
|
+-- Feature #56  M02-0017  Airflow download DAG
|     +-- #55  Decide where the location and credentials are stored    [done]
|     +-- #85  Move the DAGs to Middleware/Airflow-dags and mount them by relative path
|     +-- #77  Push .env values to Airflow Variables (upsert-secrets endpoint)
|     +-- #57  Download DAG for the All dataset
|     +-- #58  3 months dataset: filter the All file by Date received
|     +-- #59  Report started, completed and failed to the API, even when a task crashes
|     +-- #60  Airflow engine: start a DAG run asynchronously
|
+-- Feature #61  M02-0022  Admin portal: DataSets and Imports
      +-- #62  Angular app scaffold (consumer-complaints-admin)
      +-- #63  DataSets top menu and Imports left navigation
      +-- #64  Two accordions: 3 months and All, with status from the API
      +-- #65  Start download button and status refresh

Superseded by D43 and closed as not planned (no source-location types in the API):
  Feature #46 M02-0011 Configurable source location
    #47 Source location interface and factory   #48 Source: local path
    #49 Source: plain HTTP(S) URL   #50 Source: GitHub repo URL or path
```

## 3. Superpowers workflow

One chat per story. Run the commands of a story from top to bottom. `/ccaa-*` are the project skills (section 4); the others come from the Superpowers plugin.

Every command has its own row with a **Status** (`Planned`, `In progress` or `Done`), a **Started** date and a **Completed** date (`-` until set). The step that is `In progress` is the one to run next. You do not edit the table: when a step finishes, `/ccaa-milestone-log N` marks it `Done` with today's date and starts the next step. `/ccaa-story-start` and `/ccaa-story-complete` log their own step. The change is saved in the next `/ccaa-commit-push`.

Standard code story, with `N` as the issue number:

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Marks the issue in progress and refreshes the feature and epic |
| 2 | `/brainstorming Story #N ...` | Confirms the design against the issue and `DESIGN.md` |
| 3 | `/using-git-worktrees Story #N: branch ...` | Creates an isolated workspace on a new branch for the story, runs project setup, checks the test baseline is clean |
| 4 | `/writing-plans Story #N` | Breaks the story into small tasks with exact files and verification steps |
| 5 | `/test-driven-development Story #N` | Loads the RED-GREEN-REFACTOR rules so every task in step 6 starts with a failing test |
| 6 | `/subagent-driven-development Story #N` | Builds each task with a fresh subagent and a review after each (or `/executing-plans Story #N` to build inline with one review at the end) |
| 7 | `/ccaa-commit-push N` | After every task of step 6 (repeat for each task) |
| 8 | `/verification-before-completion Story #N` | Runs lint and tests and checks every acceptance item |
| 9 | `/requesting-code-review Story #N` | Reviews the story against the plan and reports issues by severity |
| 10 | `/ccaa-commit-push N` | Commits the review fixes |
| 11 | `/finishing-a-development-branch Story #N` | Verifies tests, then offers merge, pull request, keep or discard, and cleans up the worktree |
| 12 | `/ccaa-story-complete N` | Ticks the acceptance list, closes the issue, refreshes the feature |

If a test fails and you do not know why, run `/systematic-debugging Story #N` before changing code.

Every command carries its issue number (`Story #N` or `N`), so a chat history or a commit log always shows which story a command was run for.

### Phase 1 - Workflow registry

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #79 (decision only, no code) | 1 | `/ccaa-story-start 79` | Planned | - | - |
| #79 | 2 | `/brainstorming Story #79: decide the admin schema name, how a usecase maps to a workflow, the fate of data_ingest_log and system_datasets, how a workflow reads its config, the other columns and engine types, and the first engines. Record each as a decision in Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | Planned | - | - |
| #79 | 3 | `/verification-before-completion Story #79` | Planned | - | - |
| #79 | 4 | `/ccaa-commit-push 79` | Planned | - | - |
| #79 | 5 | `/ccaa-story-complete 79` | Planned | - | - |
| #80 | 1 | `/ccaa-story-start 80` | Planned | - | - |
| #80 | 2 | `/brainstorming Story #80: a shared registry and init() on the object factories, called from main (D45); one implementation returns the instance, several return a list in a fixed order` | Planned | - | - |
| #80 | 3 | `/using-git-worktrees Story #80: branch m02-0030-object-factory-init-and-bean-registry` | Planned | - | - |
| #80 | 4 | `/writing-plans Story #80` | Planned | - | - |
| #80 | 5 | `/test-driven-development Story #80` | Planned | - | - |
| #80 | 6 | `/subagent-driven-development Story #80` | Planned | - | - |
| #80 | 7 | `/ccaa-commit-push 80` after every task (repeat) | Planned | - | - |
| #80 | 8 | `/verification-before-completion Story #80` | Planned | - | - |
| #80 | 9 | `/requesting-code-review Story #80` | Planned | - | - |
| #80 | 10 | `/ccaa-commit-push 80` | Planned | - | - |
| #80 | 11 | `/finishing-a-development-branch Story #80` | Planned | - | - |
| #80 | 12 | `/ccaa-story-complete 80` | Planned | - | - |
| #81 | 1 | `/ccaa-story-start 81` | Planned | - | - |
| #81 | 2 | `/brainstorming Story #81: admin schema and app_workflows table (name up to 100 characters, engine type, engine workflow id, JSON config) with its DAO; use the schema name decided in #79` | Planned | - | - |
| #81 | 3 | `/using-git-worktrees Story #81: branch m02-0031-admin-schema-and-app-workflows-table` | Planned | - | - |
| #81 | 4 | `/writing-plans Story #81` | Planned | - | - |
| #81 | 5 | `/test-driven-development Story #81` | Planned | - | - |
| #81 | 6 | `/subagent-driven-development Story #81` | Planned | - | - |
| #81 | 7 | `/ccaa-commit-push 81` after every task (repeat) | Planned | - | - |
| #81 | 8 | `/verification-before-completion Story #81` | Planned | - | - |
| #81 | 9 | `/requesting-code-review Story #81` | Planned | - | - |
| #81 | 10 | `/ccaa-commit-push 81` | Planned | - | - |
| #81 | 11 | `/finishing-a-development-branch Story #81` | Planned | - | - |
| #81 | 12 | `/ccaa-story-complete 81` | Planned | - | - |
| #82 | 1 | `/ccaa-story-start 82` | Planned | - | - |
| #82 | 2 | `/brainstorming Story #82: app_workflows_exec_log table and DAO; keeps the workflow's information as it was at execution time; status rules of D30` | Planned | - | - |
| #82 | 3 | `/using-git-worktrees Story #82: branch m02-0032-app-workflows-exec-log-table-with-its` | Planned | - | - |
| #82 | 4 | `/writing-plans Story #82` | Planned | - | - |
| #82 | 5 | `/test-driven-development Story #82` | Planned | - | - |
| #82 | 6 | `/subagent-driven-development Story #82` | Planned | - | - |
| #82 | 7 | `/ccaa-commit-push 82` after every task (repeat) | Planned | - | - |
| #82 | 8 | `/verification-before-completion Story #82` | Planned | - | - |
| #82 | 9 | `/requesting-code-review Story #82` | Planned | - | - |
| #82 | 10 | `/ccaa-commit-push 82` | Planned | - | - |
| #82 | 11 | `/finishing-a-development-branch Story #82` | Planned | - | - |
| #82 | 12 | `/ccaa-story-complete 82` | Planned | - | - |
| Feature #78 | 1 | `/ccaa-feature-complete 78` | Planned | - | - |

### Phase 2 - Download API, the status and listing side

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #44 | 1 | `/ccaa-story-start 44` | Planned | - | - |
| #44 | 2 | `/brainstorming Story #44: shared-secret authentication for callbacks; missing or wrong secret returns 401; secret is configuration, never in the repo` | Planned | - | - |
| #44 | 3 | `/using-git-worktrees Story #44: branch m02-0009-shared-secret-authentication-for` | Planned | - | - |
| #44 | 4 | `/writing-plans Story #44` | Planned | - | - |
| #44 | 5 | `/test-driven-development Story #44` | Planned | - | - |
| #44 | 6 | `/subagent-driven-development Story #44` | Planned | - | - |
| #44 | 7 | `/ccaa-commit-push 44` after every task (repeat) | Planned | - | - |
| #44 | 8 | `/verification-before-completion Story #44` | Planned | - | - |
| #44 | 9 | `/requesting-code-review Story #44` | Planned | - | - |
| #44 | 10 | `/ccaa-commit-push 44` | Planned | - | - |
| #44 | 11 | `/finishing-a-development-branch Story #44` | Planned | - | - |
| #44 | 12 | `/ccaa-story-complete 44` | Planned | - | - |
| #43 | 1 | `/ccaa-story-start 43` | Planned | - | - |
| #43 | 2 | `/brainstorming Story #43: Airflow status callback (usecase, status started/completed/failed, optional run_id and message); duplicate and out-of-order calls are harmless; updates the log and system_datasets; uses the #44 secret` | Planned | - | - |
| #43 | 3 | `/using-git-worktrees Story #43: branch m02-0008-airflow-status-callback-endpoint` | Planned | - | - |
| #43 | 4 | `/writing-plans Story #43` | Planned | - | - |
| #43 | 5 | `/test-driven-development Story #43` | Planned | - | - |
| #43 | 6 | `/subagent-driven-development Story #43` | Planned | - | - |
| #43 | 7 | `/ccaa-commit-push 43` after every task (repeat) | Planned | - | - |
| #43 | 8 | `/verification-before-completion Story #43` | Planned | - | - |
| #43 | 9 | `/requesting-code-review Story #43` | Planned | - | - |
| #43 | 10 | `/ccaa-commit-push 43` | Planned | - | - |
| #43 | 11 | `/finishing-a-development-branch Story #43` | Planned | - | - |
| #43 | 12 | `/ccaa-story-complete 43` | Planned | - | - |
| #45 | 1 | `/ccaa-story-start 45` | Planned | - | - |
| #45 | 2 | `/brainstorming Story #45: read dataset status endpoint; one call returns all dataset rows` | Planned | - | - |
| #45 | 3 | `/using-git-worktrees Story #45: branch m02-0010-read-dataset-status-endpoint` | Planned | - | - |
| #45 | 4 | `/writing-plans Story #45` | Planned | - | - |
| #45 | 5 | `/test-driven-development Story #45` | Planned | - | - |
| #45 | 6 | `/subagent-driven-development Story #45` | Planned | - | - |
| #45 | 7 | `/ccaa-commit-push 45` after every task (repeat) | Planned | - | - |
| #45 | 8 | `/verification-before-completion Story #45` | Planned | - | - |
| #45 | 9 | `/requesting-code-review Story #45` | Planned | - | - |
| #45 | 10 | `/ccaa-commit-push 45` | Planned | - | - |
| #45 | 11 | `/finishing-a-development-branch Story #45` | Planned | - | - |
| #45 | 12 | `/ccaa-story-complete 45` | Planned | - | - |
| #83 | 1 | `/ccaa-story-start 83` | Planned | - | - |
| #83 | 2 | `/brainstorming Story #83: workflow engine interface in services, one implementation per engine type, looked up through the factory (D45); unknown engine type returns INVALID_INPUT` | Planned | - | - |
| #83 | 3 | `/using-git-worktrees Story #83: branch m02-0033-workflow-engine-interface-and-lookup` | Planned | - | - |
| #83 | 4 | `/writing-plans Story #83` | Planned | - | - |
| #83 | 5 | `/test-driven-development Story #83` | Planned | - | - |
| #83 | 6 | `/subagent-driven-development Story #83` | Planned | - | - |
| #83 | 7 | `/ccaa-commit-push 83` after every task (repeat) | Planned | - | - |
| #83 | 8 | `/verification-before-completion Story #83` | Planned | - | - |
| #83 | 9 | `/requesting-code-review Story #83` | Planned | - | - |
| #83 | 10 | `/ccaa-commit-push 83` | Planned | - | - |
| #83 | 11 | `/finishing-a-development-branch Story #83` | Planned | - | - |
| #83 | 12 | `/ccaa-story-complete 83` | Planned | - | - |
| #84 | 1 | `/ccaa-story-start 84` | Planned | - | - |
| #84 | 2 | `/brainstorming Story #84: list workflows endpoint for the portal; no secret or config value in the response` | Planned | - | - |
| #84 | 3 | `/using-git-worktrees Story #84: branch m02-0034-list-workflows-endpoint` | Planned | - | - |
| #84 | 4 | `/writing-plans Story #84` | Planned | - | - |
| #84 | 5 | `/test-driven-development Story #84` | Planned | - | - |
| #84 | 6 | `/subagent-driven-development Story #84` | Planned | - | - |
| #84 | 7 | `/ccaa-commit-push 84` after every task (repeat) | Planned | - | - |
| #84 | 8 | `/verification-before-completion Story #84` | Planned | - | - |
| #84 | 9 | `/requesting-code-review Story #84` | Planned | - | - |
| #84 | 10 | `/ccaa-commit-push 84` | Planned | - | - |
| #84 | 11 | `/finishing-a-development-branch Story #84` | Planned | - | - |
| #84 | 12 | `/ccaa-story-complete 84` | Planned | - | - |

### Phase 3 - Airflow download DAG

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #55 (decision only, no code) | 1 | `/ccaa-story-start 55` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 2 | `/brainstorming Story #55: where the source location and credentials live (database, config file or Airflow connection; never in the repo). Record the decision as D42 in Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 3 | `/verification-before-completion Story #55` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 4 | `/ccaa-commit-push 55` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 5 | `/ccaa-story-complete 55` | Done | 2026-11-14 | 2026-11-14 |
| #85 | 1 | `/ccaa-story-start 85` | Planned | - | - |
| #85 | 2 | `/brainstorming Story #85: move the DAGs to Middleware/Airflow-dags (D44), mounted by relative path so a new DAG appears without restarting Airflow; short refresh interval for local use` | Planned | - | - |
| #85 | 3 | `/using-git-worktrees Story #85: branch m02-0035-move-the-dags-to-middleware-airflow` | Planned | - | - |
| #85 | 4 | `/writing-plans Story #85` | Planned | - | - |
| #85 | 5 | `/test-driven-development Story #85` | Planned | - | - |
| #85 | 6 | `/subagent-driven-development Story #85` | Planned | - | - |
| #85 | 7 | `/ccaa-commit-push 85` after every task (repeat) | Planned | - | - |
| #85 | 8 | `/verification-before-completion Story #85` | Planned | - | - |
| #85 | 9 | `/requesting-code-review Story #85` | Planned | - | - |
| #85 | 10 | `/ccaa-commit-push 85` | Planned | - | - |
| #85 | 11 | `/finishing-a-development-branch Story #85` | Planned | - | - |
| #85 | 12 | `/ccaa-story-complete 85` | Planned | - | - |
| #77 | 1 | `/ccaa-story-start 77` | Planned | - | - |
| #77 | 2 | `/brainstorming Story #77: POST /management/airflow/upsert-secrets copies the names listed in CICD/Local/airflow/Airflow_Variables_Upsert.txt from .env into Airflow Variables through Airflow's REST API (D42); result per name, never a value; missing name reported and return code is a failure; protected by the #44 shared secret; .env.example lists the names` | Planned | - | - |
| #77 | 3 | `/using-git-worktrees Story #77: branch m02-0027-push-env-values-to-airflow-variables` | Planned | - | - |
| #77 | 4 | `/writing-plans Story #77` | Planned | - | - |
| #77 | 5 | `/test-driven-development Story #77` | Planned | - | - |
| #77 | 6 | `/subagent-driven-development Story #77` | Planned | - | - |
| #77 | 7 | `/ccaa-commit-push 77` after every task (repeat) | Planned | - | - |
| #77 | 8 | `/verification-before-completion Story #77` | Planned | - | - |
| #77 | 9 | `/requesting-code-review Story #77` | Planned | - | - |
| #77 | 10 | `/ccaa-commit-push 77` | Planned | - | - |
| #77 | 11 | `/finishing-a-development-branch Story #77` | Planned | - | - |
| #77 | 12 | `/ccaa-story-complete 77` | Planned | - | - |
| #57 | 1 | `/ccaa-story-start 57` | Planned | - | - |
| #57 | 2 | `/brainstorming Story #57: download DAG for the All dataset; the DAG reads its own source from its config and the Airflow Variables of #77 (D42, D43); registered in app_workflows; file lands in the agreed place` | Planned | - | - |
| #57 | 3 | `/using-git-worktrees Story #57: branch m02-0018-download-dag-for-the-all-dataset` | Planned | - | - |
| #57 | 4 | `/writing-plans Story #57` | Planned | - | - |
| #57 | 5 | `/test-driven-development Story #57` | Planned | - | - |
| #57 | 6 | `/subagent-driven-development Story #57` | Planned | - | - |
| #57 | 7 | `/ccaa-commit-push 57` after every task (repeat) | Planned | - | - |
| #57 | 8 | `/verification-before-completion Story #57` | Planned | - | - |
| #57 | 9 | `/requesting-code-review Story #57` | Planned | - | - |
| #57 | 10 | `/ccaa-commit-push 57` | Planned | - | - |
| #57 | 11 | `/finishing-a-development-branch Story #57` | Planned | - | - |
| #57 | 12 | `/ccaa-story-complete 57` | Planned | - | - |
| #58 | 1 | `/ccaa-story-start 58` | Planned | - | - |
| #58 | 2 | `/brainstorming Story #58: derive the 3 months dataset by filtering the All file on Date received; the file is not date-sorted so read it all; check the row count against the site figure` | Planned | - | - |
| #58 | 3 | `/using-git-worktrees Story #58: branch m02-0019-3-months-dataset-filter-the-all-file-by` | Planned | - | - |
| #58 | 4 | `/writing-plans Story #58` | Planned | - | - |
| #58 | 5 | `/test-driven-development Story #58` | Planned | - | - |
| #58 | 6 | `/subagent-driven-development Story #58` | Planned | - | - |
| #58 | 7 | `/ccaa-commit-push 58` after every task (repeat) | Planned | - | - |
| #58 | 8 | `/verification-before-completion Story #58` | Planned | - | - |
| #58 | 9 | `/requesting-code-review Story #58` | Planned | - | - |
| #58 | 10 | `/ccaa-commit-push 58` | Planned | - | - |
| #58 | 11 | `/finishing-a-development-branch Story #58` | Planned | - | - |
| #58 | 12 | `/ccaa-story-complete 58` | Planned | - | - |
| #59 | 1 | `/ccaa-story-start 59` | Planned | - | - |
| #59 | 2 | `/brainstorming Story #59: report started, completed and failed to the API from the DAG; a final task always runs so a crashed run never stays running; callbacks reach the API from the container (host.docker.internal)` | Planned | - | - |
| #59 | 3 | `/using-git-worktrees Story #59: branch m02-0020-report-started-completed-and-failed-to` | Planned | - | - |
| #59 | 4 | `/writing-plans Story #59` | Planned | - | - |
| #59 | 5 | `/test-driven-development Story #59` | Planned | - | - |
| #59 | 6 | `/subagent-driven-development Story #59` | Planned | - | - |
| #59 | 7 | `/ccaa-commit-push 59` after every task (repeat) | Planned | - | - |
| #59 | 8 | `/verification-before-completion Story #59` | Planned | - | - |
| #59 | 9 | `/requesting-code-review Story #59` | Planned | - | - |
| #59 | 10 | `/ccaa-commit-push 59` | Planned | - | - |
| #59 | 11 | `/finishing-a-development-branch Story #59` | Planned | - | - |
| #59 | 12 | `/ccaa-story-complete 59` | Planned | - | - |
| #60 | 1 | `/ccaa-story-start 60` | Planned | - | - |
| #60 | 2 | `/brainstorming Story #60: the Airflow implementation of the workflow engine interface (#83); starts a DAG run through Airflow's REST API, stores the run id on the exec log row, registers itself in the factory (D45)` | Planned | - | - |
| #60 | 3 | `/using-git-worktrees Story #60: branch m02-0021-airflow-engine-start-a-dag-run` | Planned | - | - |
| #60 | 4 | `/writing-plans Story #60` | Planned | - | - |
| #60 | 5 | `/test-driven-development Story #60` | Planned | - | - |
| #60 | 6 | `/subagent-driven-development Story #60` | Planned | - | - |
| #60 | 7 | `/ccaa-commit-push 60` after every task (repeat) | Planned | - | - |
| #60 | 8 | `/verification-before-completion Story #60` | Planned | - | - |
| #60 | 9 | `/requesting-code-review Story #60` | Planned | - | - |
| #60 | 10 | `/ccaa-commit-push 60` | Planned | - | - |
| #60 | 11 | `/finishing-a-development-branch Story #60` | Planned | - | - |
| #60 | 12 | `/ccaa-story-complete 60` | Planned | - | - |
| Feature #56 | 1 | `/ccaa-feature-complete 56` | Planned | - | - |

### Phase 4 - Start a workflow (closes the Download API feature)

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #42 | 1 | `/ccaa-story-start 42` | Planned | - | - |
| #42 | 2 | `/brainstorming Story #42: start-workflow endpoint taking a registered workflow; writes the exec log row, starts it through the engine lookup (#83), returns accepted without waiting; unknown workflow returns 422` | Planned | - | - |
| #42 | 3 | `/using-git-worktrees Story #42: branch m02-0007-start-workflow-endpoint-one-endpoint` | Planned | - | - |
| #42 | 4 | `/writing-plans Story #42` | Planned | - | - |
| #42 | 5 | `/test-driven-development Story #42` | Planned | - | - |
| #42 | 6 | `/subagent-driven-development Story #42` | Planned | - | - |
| #42 | 7 | `/ccaa-commit-push 42` after every task (repeat) | Planned | - | - |
| #42 | 8 | `/verification-before-completion Story #42` | Planned | - | - |
| #42 | 9 | `/requesting-code-review Story #42` | Planned | - | - |
| #42 | 10 | `/ccaa-commit-push 42` | Planned | - | - |
| #42 | 11 | `/finishing-a-development-branch Story #42` | Planned | - | - |
| #42 | 12 | `/ccaa-story-complete 42` | Planned | - | - |
| Feature #41 | 1 | `/ccaa-feature-complete 41` | Planned | - | - |

### Phase 5 - Admin portal

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #62 | 1 | `/ccaa-story-start 62` | Planned | - | - |
| #62 | 2 | `/brainstorming Story #62: Angular app scaffold consumer-complaints-admin under Portals/; app builds and serves` | Planned | - | - |
| #62 | 3 | `/using-git-worktrees Story #62: branch m02-0023-angular-app-scaffold-consumer` | Planned | - | - |
| #62 | 4 | `/writing-plans Story #62` | Planned | - | - |
| #62 | 5 | `/test-driven-development Story #62` | Planned | - | - |
| #62 | 6 | `/subagent-driven-development Story #62` | Planned | - | - |
| #62 | 7 | `/ccaa-commit-push 62` after every task (repeat) | Planned | - | - |
| #62 | 8 | `/verification-before-completion Story #62` | Planned | - | - |
| #62 | 9 | `/requesting-code-review Story #62` | Planned | - | - |
| #62 | 10 | `/ccaa-commit-push 62` | Planned | - | - |
| #62 | 11 | `/finishing-a-development-branch Story #62` | Planned | - | - |
| #62 | 12 | `/ccaa-story-complete 62` | Planned | - | - |
| #63 | 1 | `/ccaa-story-start 63` | Planned | - | - |
| #63 | 2 | `/brainstorming Story #63: DataSets top menu and Imports left navigation (DB Ingest comes later); navigation works` | Planned | - | - |
| #63 | 3 | `/using-git-worktrees Story #63: branch m02-0024-datasets-top-menu-and-imports-left` | Planned | - | - |
| #63 | 4 | `/writing-plans Story #63` | Planned | - | - |
| #63 | 5 | `/test-driven-development Story #63` | Planned | - | - |
| #63 | 6 | `/subagent-driven-development Story #63` | Planned | - | - |
| #63 | 7 | `/ccaa-commit-push 63` after every task (repeat) | Planned | - | - |
| #63 | 8 | `/verification-before-completion Story #63` | Planned | - | - |
| #63 | 9 | `/requesting-code-review Story #63` | Planned | - | - |
| #63 | 10 | `/ccaa-commit-push 63` | Planned | - | - |
| #63 | 11 | `/finishing-a-development-branch Story #63` | Planned | - | - |
| #63 | 12 | `/ccaa-story-complete 63` | Planned | - | - |
| #64 | 1 | `/ccaa-story-start 64` | Planned | - | - |
| #64 | 2 | `/brainstorming Story #64: two accordions, 3 months and All; each shows downloaded or not, when, and the failure reason from the #45 endpoint; status is never guessed in the UI` | Planned | - | - |
| #64 | 3 | `/using-git-worktrees Story #64: branch m02-0025-two-accordions-3-months-and-all-with` | Planned | - | - |
| #64 | 4 | `/writing-plans Story #64` | Planned | - | - |
| #64 | 5 | `/test-driven-development Story #64` | Planned | - | - |
| #64 | 6 | `/subagent-driven-development Story #64` | Planned | - | - |
| #64 | 7 | `/ccaa-commit-push 64` after every task (repeat) | Planned | - | - |
| #64 | 8 | `/verification-before-completion Story #64` | Planned | - | - |
| #64 | 9 | `/requesting-code-review Story #64` | Planned | - | - |
| #64 | 10 | `/ccaa-commit-push 64` | Planned | - | - |
| #64 | 11 | `/finishing-a-development-branch Story #64` | Planned | - | - |
| #64 | 12 | `/ccaa-story-complete 64` | Planned | - | - |
| #65 | 1 | `/ccaa-story-start 65` | Planned | - | - |
| #65 | 2 | `/brainstorming Story #65: start download button calling the #42 endpoint, then show progress (poll or refresh: decide); button disabled while running` | Planned | - | - |
| #65 | 3 | `/using-git-worktrees Story #65: branch m02-0026-start-download-button-and-status-refresh` | Planned | - | - |
| #65 | 4 | `/writing-plans Story #65` | Planned | - | - |
| #65 | 5 | `/test-driven-development Story #65` | Planned | - | - |
| #65 | 6 | `/subagent-driven-development Story #65` | Planned | - | - |
| #65 | 7 | `/ccaa-commit-push 65` after every task (repeat) | Planned | - | - |
| #65 | 8 | `/verification-before-completion Story #65` | Planned | - | - |
| #65 | 9 | `/requesting-code-review Story #65` | Planned | - | - |
| #65 | 10 | `/ccaa-commit-push 65` | Planned | - | - |
| #65 | 11 | `/finishing-a-development-branch Story #65` | Planned | - | - |
| #65 | 12 | `/ccaa-story-complete 65` | Planned | - | - |
| Feature #61 | 1 | `/ccaa-feature-complete 61` | Planned | - | - |
| Epic #29 | 1 | `/ccaa-epic-complete 29` | In progress | 2026-11-14 | - |

## 4. Project skills (`ccaa-` = Consumer Complaints Agentic App)

The skills live in `.cursor/skills/`. Each takes a GitHub issue number.

| Command | When | What it does |
|---|---|---|
| `/ccaa-story-start N` | Before the first Superpowers command of a story | Sets the story to `status: in-progress`, writes the status line, moves the parent feature and epic to in progress |
| `/ccaa-story-complete N` | After review and the final commit | Checks the acceptance items and the push, ticks them, writes the commits into the status line, sets `status: done`, closes the story, refreshes the feature |
| `/ccaa-feature-complete N` | When every story of the feature is done | Checks all stories are closed, marks the feature done and closes it, refreshes the epic |
| `/ccaa-epic-complete N` | When every feature of the epic is done | Marks the epic done and closes it, and marks this file complete |
| `/ccaa-milestone-log N` | After each workflow step finishes (the story skills call it for their own step) | Marks the step that is `In progress` for issue N as `Done` with today's date, starts the next step, and refreshes the story count at the top. Does not commit |
| `/ccaa-commit-push N` | After every task, and at the end of each story | Runs lint and tests, commits one logical change as the repository owner with the story number in the message, pushes to `main`. Without `N` it uses the story of the chat, or asks |
| `/ccaa-progress-sync N` | Used by the skills above | Rebuilds a feature or epic checklist and its progress line from the real state of its children |

## 5. Notes

- **One branch and worktree per story.** `/using-git-worktrees` creates the story branch in `.worktrees/` (git-ignored) and `/ccaa-commit-push` pushes that branch. `/finishing-a-development-branch` then merges it into `main` (option 1) or opens a pull request (option 2). Run `/ccaa-story-complete` from the main checkout once the branch is merged into `main` and pushed. `/ccaa-story-start`, the feature and epic commands, and decision-only stories such as #55 work on `main`.
- **Superseded by D43 and closed as not planned:** feature #46 (Configurable source location) and stories #47 (interface and factory), #48 (local path), #49 (plain HTTP(S) URL) and #50 (GitHub). Downloads are now workflows registered in `app_workflows`; each workflow knows its own source and the API has no source-location types. Their rows were removed from sections 1 to 3. Story #47's brainstorming had started and produced the design that became D43 to D45.
- **Added with D43 to D45:** feature #78 (Workflow registry) with stories #79 to #82, stories #83 (engine interface) and #84 (list workflows) under #41, and story #85 (move the DAGs to `Middleware/Airflow-dags`) under #56. Stories #42 and #60 were retitled (start-workflow endpoint, Airflow engine). Stories that add classes carry the acceptance line "registered as singletons in the package's `objects_factory` (D45)".
- **Run #79 first.** It settles the admin schema name, how a usecase maps to a workflow, and what happens to `data_ingest_log` and `system_datasets`. The stories after it, and the portal stories of Phase 5 (accordions per dataset), may change with the answers.
- **Open questions on the issues:** #65 (poll or refresh). The #55 question is decided in D42 (revised by D43): credentials in `.env`, copied into Airflow Variables by story #77.
- **Story #77 was added** while deciding #55 (D42). It is under feature #56 and is built first in Phase 3, because the DAG reads the Variables it creates.
- **Moved to M03 - Cloud Deployment:** #51 S3, #52 Azure Blob, #53 GCP Cloud Storage, #54 Google Drive, and the cloud migration workflow #24. They are not part of this milestone. #51 to #54 were written as source types, so under D43 they need rewriting as cloud workflows before M03 starts (they are still open).
- **Where the details are:** every decision behind these issues is in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. The next decision number is D46.
