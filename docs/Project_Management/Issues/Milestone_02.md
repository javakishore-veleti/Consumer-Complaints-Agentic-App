# Milestone M02 - Downloads Management

**Scope (decision D38 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`):** download the free CFPB dataset on demand from the admin portal, asynchronously through Airflow, from a configured source location, and always show whether it has been downloaded. Everything runs locally. Cloud work is M03.

**Status: in progress.** 1 epic, 5 features and 21 stories. 3 stories (and 1 feature) are already done, 18 stories are left to build.

How to read this file:
- `#42` is the GitHub issue number in this repository. The `M02-00NN` key is the sequence tag at the start of the issue title. Keys are not in build order.
- Section 1 is the table of contents in the order the work should be built. Section 2 groups the same issues as epic, feature and story.
- Section 3 has the Superpowers commands to run for each story, one after the other. Section 4 explains the project skills (`ccaa-`) those commands use.

## Contents

- [1. Table of contents (build order)](#1-table-of-contents-build-order)
  - [Phase 0 - Dataset status, already built](#phase-0---dataset-status-already-built-commit-eec398d)
  - [Phase 1 - Configurable source location](#phase-1---configurable-source-location-nothing-else-can-fetch-a-file-without-it)
  - [Phase 2 - Download API, the status side](#phase-2---download-api-the-status-side)
  - [Phase 3 - Airflow download DAG](#phase-3---airflow-download-dag)
  - [Phase 4 - Start a download](#phase-4---start-a-download-closes-the-download-api-feature)
  - [Phase 5 - Admin portal](#phase-5---admin-portal)
- [2. The same issues grouped by epic and feature](#2-the-same-issues-grouped-by-epic-and-feature)
- [3. Superpowers workflow](#3-superpowers-workflow)
  - [Phase 1 - Configurable source location](#phase-1---configurable-source-location)
  - [Phase 2 - Download API, the status side](#phase-2---download-api-the-status-side-1)
  - [Phase 3 - Airflow download DAG](#phase-3---airflow-download-dag-1)
  - [Phase 4 - Start a download](#phase-4---start-a-download)
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

### Phase 1 - Configurable source location (nothing else can fetch a file without it)

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 6 | #46 | M02-0011 | Feature | Configurable source location | Parent of the stories below |
| 7 | #55 | M02-0016 | Story | Decide where the location and credentials are stored | Decision first: the factory reads its type from configuration |
| 8 | #47 | M02-0012 | Story | Source location interface and factory | Every source type implements this |
| 9 | #48 | M02-0013 | Story | Source: local path | Simplest type; proves the interface |
| 10 | #49 | M02-0014 | Story | Source: plain HTTP(S) URL | Needed for the CFPB file itself. Confirm it is wanted before starting (open question on the issue) |
| 11 | #50 | M02-0015 | Story | Source: GitHub repo URL or path | Same shape as the HTTP source |

### Phase 2 - Download API, the status side

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 12 | #41 | M02-0006 | Feature | Download API | Parent of the stories below (it finishes in Phase 4) |
| 13 | #44 | M02-0009 | Story | Shared-secret authentication for callbacks | The callback endpoint must be protected from day one |
| 14 | #43 | M02-0008 | Story | Airflow status callback endpoint | Uses #44 and the built `system_datasets` service |
| 15 | #45 | M02-0010 | Story | Read dataset status endpoint | Reads the Phase 0 table; the portal needs it |

### Phase 3 - Airflow download DAG

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 16 | #56 | M02-0017 | Feature | Airflow download DAG | Parent of the stories below |
| 17 | #77 | M02-0027 | Story | Push .env values to Airflow Variables (upsert-secrets endpoint) | Decision D42. Uses the #44 secret; the DAG reads the Variables it creates |
| 18 | #57 | M02-0018 | Story | Download DAG for the All dataset | Uses the Phase 1 source locations, read from the Airflow Variables of #77 |
| 19 | #58 | M02-0019 | Story | 3 months dataset: filter the All file by Date received | Derived from the All file, so it follows #57 |
| 20 | #59 | M02-0020 | Story | Report started, completed and failed to the API, even when a task crashes | Calls the Phase 2 callback and uses its secret |
| 21 | #60 | M02-0021 | Story | Trigger the DAG from the facade (service) | The DAG must exist before it can be triggered |

### Phase 4 - Start a download (closes the Download API feature)

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 22 | #42 | M02-0007 | Story | Start-download endpoint (one endpoint, any usecase) | Calls the trigger service from #60 |

### Phase 5 - Admin portal

| # | Issue | Key | Type | Title | Why here |
|---|---|---|---|---|---|
| 23 | #61 | M02-0022 | Feature | Admin portal: DataSets and Imports | Parent of the stories below |
| 24 | #62 | M02-0023 | Story | Angular app scaffold (consumer-complaints-admin) | Everything in the portal builds on it |
| 25 | #63 | M02-0024 | Story | DataSets top menu and Imports left navigation | Shell for the accordions |
| 26 | #64 | M02-0025 | Story | Two accordions: 3 months and All, with status from the API | Reads the Phase 2 status endpoint (#45) |
| 27 | #65 | M02-0026 | Story | Start download button and status refresh | Calls the Phase 4 endpoint (#42) |

## 2. The same issues grouped by epic and feature

```
Epic #29  M02-0001  Downloads Management
|
+-- Feature #37  M02-0002  Dataset status (system_datasets)            [done]
|     +-- #38  system_datasets table and migration                     [done]
|     +-- #39  system_datasets DAO                                     [done]
|     +-- #40  Record outcome in one transaction                       [done]
|
+-- Feature #46  M02-0011  Configurable source location
|     +-- #55  Decide where the location and credentials are stored
|     +-- #47  Source location interface and factory
|     +-- #48  Source: local path
|     +-- #49  Source: plain HTTP(S) URL
|     +-- #50  Source: GitHub repo URL or path
|
+-- Feature #41  M02-0006  Download API
|     +-- #44  Shared-secret authentication for callbacks
|     +-- #43  Airflow status callback endpoint
|     +-- #45  Read dataset status endpoint
|     +-- #42  Start-download endpoint (one endpoint, any usecase)     (built in Phase 4)
|
+-- Feature #56  M02-0017  Airflow download DAG
|     +-- #77  Push .env values to Airflow Variables (upsert-secrets endpoint)
|     +-- #57  Download DAG for the All dataset
|     +-- #58  3 months dataset: filter the All file by Date received
|     +-- #59  Report started, completed and failed to the API, even when a task crashes
|     +-- #60  Trigger the DAG from the facade (service)
|
+-- Feature #61  M02-0022  Admin portal: DataSets and Imports
      +-- #62  Angular app scaffold (consumer-complaints-admin)
      +-- #63  DataSets top menu and Imports left navigation
      +-- #64  Two accordions: 3 months and All, with status from the API
      +-- #65  Start download button and status refresh
```

## 3. Superpowers workflow

One chat per story. Run the commands of a story from top to bottom. `/ccaa-*` are the project skills (section 4); the others come from the Superpowers plugin.

Every command has its own row with a **Status** (`Planned`, `In progress` or `Done`), a **Started** date and a **Completed** date (`-` until set). The step that is `In progress` is the one to run next. You do not edit the table: when a step finishes, `/ccaa-milestone-log N` marks it `Done` with today's date and starts the next step. `/ccaa-story-start` and `/ccaa-story-complete` log their own step. The change is saved in the next `/ccaa-commit-push`.

Standard code story, with `N` as the issue number:

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Marks the issue in progress and refreshes the feature and epic |
| 2 | `/brainstorming Story #N ...` | Confirms the design against the issue and `DESIGN.md` |
| 3 | `/writing-plans Story #N` | Breaks the story into small tasks |
| 4 | `/subagent-driven-development Story #N` | Builds each task test-first (red, green, refactor) |
| 5 | `/ccaa-commit-push N` | After every task of step 4 (repeat for each task) |
| 6 | `/verification-before-completion Story #N` | Runs lint and tests and checks every acceptance item |
| 7 | `/requesting-code-review Story #N` | Reviews the story against the plan |
| 8 | `/ccaa-commit-push N` | Commits the review fixes |
| 9 | `/ccaa-story-complete N` | Ticks the acceptance list, closes the issue, refreshes the feature |

If a test fails and you do not know why, run `/systematic-debugging Story #N` before changing code.

Every command carries its issue number (`Story #N` or `N`), so a chat history or a commit log always shows which story a command was run for.

### Phase 1 - Configurable source location

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #55 (decision only, no code) | 1 | `/ccaa-story-start 55` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 2 | `/brainstorming Story #55: where the source location and credentials live (database, config file or Airflow connection; never in the repo). Record the decision as D42 in Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | Done | 2026-11-14 | 2026-11-14 |
| #55 | 3 | `/verification-before-completion Story #55` | In progress | 2026-11-14 | - |
| #55 | 4 | `/ccaa-commit-push 55` | Planned | - | - |
| #55 | 5 | `/ccaa-story-complete 55` | Planned | - | - |
| #47 | 1 | `/ccaa-story-start 47` | Planned | - | - |
| #47 | 2 | `/brainstorming Story #47: source location interface and factory; ctx in, integer out; type chosen from configuration (D42)` | Planned | - | - |
| #47 | 3 | `/writing-plans Story #47` | Planned | - | - |
| #47 | 4 | `/subagent-driven-development Story #47` | Planned | - | - |
| #47 | 5 | `/ccaa-commit-push 47` after every task (repeat) | Planned | - | - |
| #47 | 6 | `/verification-before-completion Story #47` | Planned | - | - |
| #47 | 7 | `/requesting-code-review Story #47` | Planned | - | - |
| #47 | 8 | `/ccaa-commit-push 47` | Planned | - | - |
| #47 | 9 | `/ccaa-story-complete 47` | Planned | - | - |
| #48 | 1 | `/ccaa-story-start 48` | Planned | - | - |
| #48 | 2 | `/brainstorming Story #48: local path source; must work with the zipped CSV` | Planned | - | - |
| #48 | 3 | `/writing-plans Story #48` | Planned | - | - |
| #48 | 4 | `/subagent-driven-development Story #48` | Planned | - | - |
| #48 | 5 | `/ccaa-commit-push 48` after every task (repeat) | Planned | - | - |
| #48 | 6 | `/verification-before-completion Story #48` | Planned | - | - |
| #48 | 7 | `/requesting-code-review Story #48` | Planned | - | - |
| #48 | 8 | `/ccaa-commit-push 48` | Planned | - | - |
| #48 | 9 | `/ccaa-story-complete 48` | Planned | - | - |
| #49 | 1 | `/ccaa-story-start 49` | Planned | - | - |
| #49 | 2 | `/brainstorming Story #49: plain HTTP(S) source for files.consumerfinance.gov; stream the ~350 MB file without loading it into memory; confirm the story is wanted` | Planned | - | - |
| #49 | 3 | `/writing-plans Story #49` | Planned | - | - |
| #49 | 4 | `/subagent-driven-development Story #49` | Planned | - | - |
| #49 | 5 | `/ccaa-commit-push 49` after every task (repeat) | Planned | - | - |
| #49 | 6 | `/verification-before-completion Story #49` | Planned | - | - |
| #49 | 7 | `/requesting-code-review Story #49` | Planned | - | - |
| #49 | 8 | `/ccaa-commit-push 49` | Planned | - | - |
| #49 | 9 | `/ccaa-story-complete 49` | Planned | - | - |
| #50 | 1 | `/ccaa-story-start 50` | Planned | - | - |
| #50 | 2 | `/brainstorming Story #50: GitHub repo URL or path source; must work with a raw file URL` | Planned | - | - |
| #50 | 3 | `/writing-plans Story #50` | Planned | - | - |
| #50 | 4 | `/subagent-driven-development Story #50` | Planned | - | - |
| #50 | 5 | `/ccaa-commit-push 50` after every task (repeat) | Planned | - | - |
| #50 | 6 | `/verification-before-completion Story #50` | Planned | - | - |
| #50 | 7 | `/requesting-code-review Story #50` | Planned | - | - |
| #50 | 8 | `/ccaa-commit-push 50` | Planned | - | - |
| #50 | 9 | `/ccaa-story-complete 50` | Planned | - | - |
| Feature #46 | 1 | `/ccaa-feature-complete 46` | In progress | 2026-11-14 | - |

### Phase 2 - Download API, the status side

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #44 | 1 | `/ccaa-story-start 44` | Planned | - | - |
| #44 | 2 | `/brainstorming Story #44: shared-secret authentication for callbacks; missing or wrong secret returns 401; secret is configuration, never in the repo` | Planned | - | - |
| #44 | 3 | `/writing-plans Story #44` | Planned | - | - |
| #44 | 4 | `/subagent-driven-development Story #44` | Planned | - | - |
| #44 | 5 | `/ccaa-commit-push 44` after every task (repeat) | Planned | - | - |
| #44 | 6 | `/verification-before-completion Story #44` | Planned | - | - |
| #44 | 7 | `/requesting-code-review Story #44` | Planned | - | - |
| #44 | 8 | `/ccaa-commit-push 44` | Planned | - | - |
| #44 | 9 | `/ccaa-story-complete 44` | Planned | - | - |
| #43 | 1 | `/ccaa-story-start 43` | Planned | - | - |
| #43 | 2 | `/brainstorming Story #43: Airflow status callback (usecase, status started/completed/failed, optional run_id and message); duplicate and out-of-order calls are harmless; updates the log and system_datasets; uses the #44 secret` | Planned | - | - |
| #43 | 3 | `/writing-plans Story #43` | Planned | - | - |
| #43 | 4 | `/subagent-driven-development Story #43` | Planned | - | - |
| #43 | 5 | `/ccaa-commit-push 43` after every task (repeat) | Planned | - | - |
| #43 | 6 | `/verification-before-completion Story #43` | Planned | - | - |
| #43 | 7 | `/requesting-code-review Story #43` | Planned | - | - |
| #43 | 8 | `/ccaa-commit-push 43` | Planned | - | - |
| #43 | 9 | `/ccaa-story-complete 43` | Planned | - | - |
| #45 | 1 | `/ccaa-story-start 45` | Planned | - | - |
| #45 | 2 | `/brainstorming Story #45: read dataset status endpoint; one call returns all dataset rows` | Planned | - | - |
| #45 | 3 | `/writing-plans Story #45` | Planned | - | - |
| #45 | 4 | `/subagent-driven-development Story #45` | Planned | - | - |
| #45 | 5 | `/ccaa-commit-push 45` after every task (repeat) | Planned | - | - |
| #45 | 6 | `/verification-before-completion Story #45` | Planned | - | - |
| #45 | 7 | `/requesting-code-review Story #45` | Planned | - | - |
| #45 | 8 | `/ccaa-commit-push 45` | Planned | - | - |
| #45 | 9 | `/ccaa-story-complete 45` | Planned | - | - |

Feature #41 is not complete yet. Its last story, #42, is in Phase 4.

### Phase 3 - Airflow download DAG

Verify DAG stories against the local Airflow: `npm run local:containers:all:start`, then check the DAG appears and runs.

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #77 | 1 | `/ccaa-story-start 77` | Planned | - | - |
| #77 | 2 | `/brainstorming Story #77: POST /management/airflow/upsert-secrets copies the names listed in CICD/Local/airflow/Airflow_Variables_Upsert.txt from .env into Airflow Variables through Airflow's REST API (D42); result per name, never a value; missing name reported and return code is a failure; protected by the #44 shared secret; .env.example lists the names` | Planned | - | - |
| #77 | 3 | `/writing-plans Story #77` | Planned | - | - |
| #77 | 4 | `/subagent-driven-development Story #77` | Planned | - | - |
| #77 | 5 | `/ccaa-commit-push 77` after every task (repeat) | Planned | - | - |
| #77 | 6 | `/verification-before-completion Story #77` | Planned | - | - |
| #77 | 7 | `/requesting-code-review Story #77` | Planned | - | - |
| #77 | 8 | `/ccaa-commit-push 77` | Planned | - | - |
| #77 | 9 | `/ccaa-story-complete 77` | Planned | - | - |
| #57 | 1 | `/ccaa-story-start 57` | Planned | - | - |
| #57 | 2 | `/brainstorming Story #57: download DAG for the All dataset; read the source location from the Airflow Variables of #77 (D42) and fetch it with the Phase 1 source types; DAG appears in Airflow; file lands in the agreed place` | Planned | - | - |
| #57 | 3 | `/writing-plans Story #57` | Planned | - | - |
| #57 | 4 | `/subagent-driven-development Story #57` | Planned | - | - |
| #57 | 5 | `/ccaa-commit-push 57` after every task (repeat) | Planned | - | - |
| #57 | 6 | `/verification-before-completion Story #57` | Planned | - | - |
| #57 | 7 | `/requesting-code-review Story #57` | Planned | - | - |
| #57 | 8 | `/ccaa-commit-push 57` | Planned | - | - |
| #57 | 9 | `/ccaa-story-complete 57` | Planned | - | - |
| #58 | 1 | `/ccaa-story-start 58` | Planned | - | - |
| #58 | 2 | `/brainstorming Story #58: derive the 3 months dataset by filtering the All file on Date received; the file is not date-sorted so read it all; check the row count against the site figure` | Planned | - | - |
| #58 | 3 | `/writing-plans Story #58` | Planned | - | - |
| #58 | 4 | `/subagent-driven-development Story #58` | Planned | - | - |
| #58 | 5 | `/ccaa-commit-push 58` after every task (repeat) | Planned | - | - |
| #58 | 6 | `/verification-before-completion Story #58` | Planned | - | - |
| #58 | 7 | `/requesting-code-review Story #58` | Planned | - | - |
| #58 | 8 | `/ccaa-commit-push 58` | Planned | - | - |
| #58 | 9 | `/ccaa-story-complete 58` | Planned | - | - |
| #59 | 1 | `/ccaa-story-start 59` | Planned | - | - |
| #59 | 2 | `/brainstorming Story #59: report started, completed and failed to the API from the DAG; a final task always runs so a crashed run never stays running; callbacks reach the API from the container (host.docker.internal)` | Planned | - | - |
| #59 | 3 | `/writing-plans Story #59` | Planned | - | - |
| #59 | 4 | `/subagent-driven-development Story #59` | Planned | - | - |
| #59 | 5 | `/ccaa-commit-push 59` after every task (repeat) | Planned | - | - |
| #59 | 6 | `/verification-before-completion Story #59` | Planned | - | - |
| #59 | 7 | `/requesting-code-review Story #59` | Planned | - | - |
| #59 | 8 | `/ccaa-commit-push 59` | Planned | - | - |
| #59 | 9 | `/ccaa-story-complete 59` | Planned | - | - |
| #60 | 1 | `/ccaa-story-start 60` | Planned | - | - |
| #60 | 2 | `/brainstorming Story #60: a facade service starts the DAG asynchronously through Airflow's API; returns immediately; run_id stored on the log row` | Planned | - | - |
| #60 | 3 | `/writing-plans Story #60` | Planned | - | - |
| #60 | 4 | `/subagent-driven-development Story #60` | Planned | - | - |
| #60 | 5 | `/ccaa-commit-push 60` after every task (repeat) | Planned | - | - |
| #60 | 6 | `/verification-before-completion Story #60` | Planned | - | - |
| #60 | 7 | `/requesting-code-review Story #60` | Planned | - | - |
| #60 | 8 | `/ccaa-commit-push 60` | Planned | - | - |
| #60 | 9 | `/ccaa-story-complete 60` | Planned | - | - |
| Feature #56 | 1 | `/ccaa-feature-complete 56` | Planned | - | - |

### Phase 4 - Start a download

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #42 | 1 | `/ccaa-story-start 42` | Planned | - | - |
| #42 | 2 | `/brainstorming Story #42: start-download endpoint taking usecase; creates the log row and calls the #60 trigger service; returns accepted without waiting; unknown usecase returns 422` | Planned | - | - |
| #42 | 3 | `/writing-plans Story #42` | Planned | - | - |
| #42 | 4 | `/subagent-driven-development Story #42` | Planned | - | - |
| #42 | 5 | `/ccaa-commit-push 42` after every task (repeat) | Planned | - | - |
| #42 | 6 | `/verification-before-completion Story #42` | Planned | - | - |
| #42 | 7 | `/requesting-code-review Story #42` | Planned | - | - |
| #42 | 8 | `/ccaa-commit-push 42` | Planned | - | - |
| #42 | 9 | `/ccaa-story-complete 42` | Planned | - | - |
| Feature #41 | 1 | `/ccaa-feature-complete 41` | Planned | - | - |

### Phase 5 - Admin portal

Verify with `ng build` and `ng test` inside `Portals/consumer-complaints-admin`. Methods take a single ctx and return an integer, like the Python side.

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #62 | 1 | `/ccaa-story-start 62` | Planned | - | - |
| #62 | 2 | `/brainstorming Story #62: Angular app scaffold consumer-complaints-admin under Portals/; app builds and serves` | Planned | - | - |
| #62 | 3 | `/writing-plans Story #62` | Planned | - | - |
| #62 | 4 | `/subagent-driven-development Story #62` | Planned | - | - |
| #62 | 5 | `/ccaa-commit-push 62` after every task (repeat) | Planned | - | - |
| #62 | 6 | `/verification-before-completion Story #62` | Planned | - | - |
| #62 | 7 | `/requesting-code-review Story #62` | Planned | - | - |
| #62 | 8 | `/ccaa-commit-push 62` | Planned | - | - |
| #62 | 9 | `/ccaa-story-complete 62` | Planned | - | - |
| #63 | 1 | `/ccaa-story-start 63` | Planned | - | - |
| #63 | 2 | `/brainstorming Story #63: DataSets top menu and Imports left navigation (DB Ingest comes later); navigation works` | Planned | - | - |
| #63 | 3 | `/writing-plans Story #63` | Planned | - | - |
| #63 | 4 | `/subagent-driven-development Story #63` | Planned | - | - |
| #63 | 5 | `/ccaa-commit-push 63` after every task (repeat) | Planned | - | - |
| #63 | 6 | `/verification-before-completion Story #63` | Planned | - | - |
| #63 | 7 | `/requesting-code-review Story #63` | Planned | - | - |
| #63 | 8 | `/ccaa-commit-push 63` | Planned | - | - |
| #63 | 9 | `/ccaa-story-complete 63` | Planned | - | - |
| #64 | 1 | `/ccaa-story-start 64` | Planned | - | - |
| #64 | 2 | `/brainstorming Story #64: two accordions, 3 months and All; each shows downloaded or not, when, and the failure reason from the #45 endpoint; status is never guessed in the UI` | Planned | - | - |
| #64 | 3 | `/writing-plans Story #64` | Planned | - | - |
| #64 | 4 | `/subagent-driven-development Story #64` | Planned | - | - |
| #64 | 5 | `/ccaa-commit-push 64` after every task (repeat) | Planned | - | - |
| #64 | 6 | `/verification-before-completion Story #64` | Planned | - | - |
| #64 | 7 | `/requesting-code-review Story #64` | Planned | - | - |
| #64 | 8 | `/ccaa-commit-push 64` | Planned | - | - |
| #64 | 9 | `/ccaa-story-complete 64` | Planned | - | - |
| #65 | 1 | `/ccaa-story-start 65` | Planned | - | - |
| #65 | 2 | `/brainstorming Story #65: start download button calling the #42 endpoint, then show progress (poll or refresh: decide); button disabled while running` | Planned | - | - |
| #65 | 3 | `/writing-plans Story #65` | Planned | - | - |
| #65 | 4 | `/subagent-driven-development Story #65` | Planned | - | - |
| #65 | 5 | `/ccaa-commit-push 65` after every task (repeat) | Planned | - | - |
| #65 | 6 | `/verification-before-completion Story #65` | Planned | - | - |
| #65 | 7 | `/requesting-code-review Story #65` | Planned | - | - |
| #65 | 8 | `/ccaa-commit-push 65` | Planned | - | - |
| #65 | 9 | `/ccaa-story-complete 65` | Planned | - | - |
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

- **Work happens on `main`, as in M01.** There is no worktree or pull request step, so `using-git-worktrees` and `finishing-a-development-branch` are left out. Add them to a row if you want a branch per story.
- **Checklists that were out of date.** Epic #29 still lists #30 (Data ingest log), which is an M01 feature, and feature #46 still lists #51 to #54 (cloud sources), which moved to M03. `/ccaa-progress-sync` drops children that point to a different parent, so the first `/ccaa-story-start` cleans this up.
- **Open questions on the issues:** #49 (is the HTTP source wanted), #65 (poll or refresh). The #55 question is decided in D42: values in `.env`, copied into Airflow Variables by story #77.
- **Story #77 was added** while deciding #55 (D42). It is under feature #56 and is built first in Phase 3, because the DAG reads the Variables it creates.
- **Moved to M03 - Cloud Deployment:** #51 S3, #52 Azure Blob, #53 GCP Cloud Storage, #54 Google Drive, and the cloud migration workflow #24. They are not part of this milestone.
- **Where the details are:** every decision behind these issues is in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. The next decision number is D43.
