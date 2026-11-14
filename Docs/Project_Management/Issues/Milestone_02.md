# Milestone M02 - Downloads Management

**Scope (decision D38 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`):** download the free CFPB dataset on demand from the admin portal, asynchronously through Airflow, from a configured source location, and always show whether it has been downloaded. Everything runs locally. Cloud work is M03.

**Status: in progress.** 1 epic, 5 features and 21 stories. 3 stories (and 1 feature) are already done, 18 stories are left to build.

How to read this file:
- `#42` is the GitHub issue number in this repository. The `M02-00NN` key is the sequence tag at the start of the issue title. Keys are not in build order.
- Section 1 is the table of contents in the order the work should be built. Section 2 groups the same issues as epic, feature and story.
- Section 3 has the Superpowers commands to run for each story, one after the other. Section 4 explains the project skills (`ccaa-`) those commands use.

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

One chat per story. Run the commands in each row from top to bottom. `/ccaa-*` are the project skills (section 4); the others come from the Superpowers plugin.

Each row has a **Status** (`Planned`, `In progress` or `Done`), a **Started** date and a **Completed** date (`-` until set). You do not edit them: `/ccaa-story-start`, `/ccaa-story-complete`, `/ccaa-feature-complete` and `/ccaa-epic-complete` call `/ccaa-milestone-log`, which updates the row and pushes it.

Standard code story, with `N` as the issue number:

| Step | Command | What it does |
|---|---|---|
| 1 | `/ccaa-story-start N` | Marks the issue in progress and refreshes the feature and epic |
| 2 | `/brainstorming Story #N ...` | Confirms the design against the issue and `DESIGN.md` |
| 3 | `/writing-plans` | Breaks the story into small tasks |
| 4 | `/subagent-driven-development` | Builds each task test-first (red, green, refactor) |
| 4a | `/ccaa-commit-push` | After every task (repeat for each task) |
| 5 | `/verification-before-completion` | Runs lint and tests and checks every acceptance item |
| 6 | `/requesting-code-review` | Reviews the story against the plan |
| 7 | `/ccaa-commit-push` | Commits the review fixes |
| 8 | `/ccaa-story-complete N` | Ticks the acceptance list, closes the issue, refreshes the feature |

If a test fails and you do not know why, run `/systematic-debugging` before changing code.

### Phase 1 - Configurable source location

| Issue | Status | Started | Completed | Commands, in order |
|---|---|---|---|---|
| #55 (decision only, no code) | In progress | 2026-11-14 | - | 1. `/ccaa-story-start 55`<br>2. `/brainstorming Story #55: where the source location and credentials live (database, config file or Airflow connection; never in the repo). Record the decision as D42 in Middleware/ConsumerComplaintsHandsOn/DESIGN.md`<br>3. `/verification-before-completion`<br>4. `/ccaa-commit-push`<br>5. `/ccaa-story-complete 55` |
| #47 | Planned | - | - | 1. `/ccaa-story-start 47`<br>2. `/brainstorming Story #47: source location interface and factory; ctx in, integer out; type chosen from configuration (D42)`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 47` |
| #48 | Planned | - | - | 1. `/ccaa-story-start 48`<br>2. `/brainstorming Story #48: local path source; must work with the zipped CSV`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 48` |
| #49 | Planned | - | - | 1. `/ccaa-story-start 49`<br>2. `/brainstorming Story #49: plain HTTP(S) source for files.consumerfinance.gov; stream the ~350 MB file without loading it into memory; confirm the story is wanted`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 49` |
| #50 | Planned | - | - | 1. `/ccaa-story-start 50`<br>2. `/brainstorming Story #50: GitHub repo URL or path source; must work with a raw file URL`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 50` |
| Feature #46 | In progress | 2026-11-14 | - | `/ccaa-feature-complete 46` |

### Phase 2 - Download API, the status side

| Issue | Status | Started | Completed | Commands, in order |
|---|---|---|---|---|
| #44 | Planned | - | - | 1. `/ccaa-story-start 44`<br>2. `/brainstorming Story #44: shared-secret authentication for callbacks; missing or wrong secret returns 401; secret is configuration, never in the repo`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 44` |
| #43 | Planned | - | - | 1. `/ccaa-story-start 43`<br>2. `/brainstorming Story #43: Airflow status callback (usecase, status started/completed/failed, optional run_id and message); duplicate and out-of-order calls are harmless; updates the log and system_datasets; uses the #44 secret`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 43` |
| #45 | Planned | - | - | 1. `/ccaa-story-start 45`<br>2. `/brainstorming Story #45: read dataset status endpoint; one call returns all dataset rows`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 45` |

Feature #41 is not complete yet. Its last story, #42, is in Phase 4.

### Phase 3 - Airflow download DAG

Verify DAG stories against the local Airflow: `npm run local:containers:all:start`, then check the DAG appears and runs.

| Issue | Status | Started | Completed | Commands, in order |
|---|---|---|---|---|
| #77 | Planned | - | - | 1. `/ccaa-story-start 77`<br>2. `/brainstorming Story #77: POST /management/airflow/upsert-secrets copies the names listed in CICD/Local/airflow/Airflow_Variables_Upsert.txt from .env into Airflow Variables through Airflow's REST API (D42); result per name, never a value; missing name reported and return code is a failure; protected by the #44 shared secret; .env.example lists the names`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 77` |
| #57 | Planned | - | - | 1. `/ccaa-story-start 57`<br>2. `/brainstorming Story #57: download DAG for the All dataset; read the source location from the Airflow Variables of #77 (D42) and fetch it with the Phase 1 source types; DAG appears in Airflow; file lands in the agreed place`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 57` |
| #58 | Planned | - | - | 1. `/ccaa-story-start 58`<br>2. `/brainstorming Story #58: derive the 3 months dataset by filtering the All file on Date received; the file is not date-sorted so read it all; check the row count against the site figure`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 58` |
| #59 | Planned | - | - | 1. `/ccaa-story-start 59`<br>2. `/brainstorming Story #59: report started, completed and failed to the API from the DAG; a final task always runs so a crashed run never stays running; callbacks reach the API from the container (host.docker.internal)`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 59` |
| #60 | Planned | - | - | 1. `/ccaa-story-start 60`<br>2. `/brainstorming Story #60: a facade service starts the DAG asynchronously through Airflow's API; returns immediately; run_id stored on the log row`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 60` |
| Feature #56 | Planned | - | - | `/ccaa-feature-complete 56` |

### Phase 4 - Start a download

| Issue | Status | Started | Completed | Commands, in order |
|---|---|---|---|---|
| #42 | Planned | - | - | 1. `/ccaa-story-start 42`<br>2. `/brainstorming Story #42: start-download endpoint taking usecase; creates the log row and calls the #60 trigger service; returns accepted without waiting; unknown usecase returns 422`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 42` |
| Feature #41 | Planned | - | - | `/ccaa-feature-complete 41` |

### Phase 5 - Admin portal

Verify with `ng build` and `ng test` inside `Portals/consumer-complaints-admin`. Methods take a single ctx and return an integer, like the Python side.

| Issue | Status | Started | Completed | Commands, in order |
|---|---|---|---|---|
| #62 | Planned | - | - | 1. `/ccaa-story-start 62`<br>2. `/brainstorming Story #62: Angular app scaffold consumer-complaints-admin under Portals/; app builds and serves`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 62` |
| #63 | Planned | - | - | 1. `/ccaa-story-start 63`<br>2. `/brainstorming Story #63: DataSets top menu and Imports left navigation (DB Ingest comes later); navigation works`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 63` |
| #64 | Planned | - | - | 1. `/ccaa-story-start 64`<br>2. `/brainstorming Story #64: two accordions, 3 months and All; each shows downloaded or not, when, and the failure reason from the #45 endpoint; status is never guessed in the UI`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 64` |
| #65 | Planned | - | - | 1. `/ccaa-story-start 65`<br>2. `/brainstorming Story #65: start download button calling the #42 endpoint, then show progress (poll or refresh: decide); button disabled while running`<br>3. `/writing-plans`<br>4. `/subagent-driven-development`, then `/ccaa-commit-push` after each task<br>5. `/verification-before-completion`<br>6. `/requesting-code-review`<br>7. `/ccaa-commit-push`<br>8. `/ccaa-story-complete 65` |
| Feature #61 | Planned | - | - | `/ccaa-feature-complete 61` |
| Epic #29 | In progress | 2026-11-14 | - | `/ccaa-epic-complete 29` |

## 4. Project skills (`ccaa-` = Consumer Complaints Agentic App)

The skills live in `.cursor/skills/`. Each takes a GitHub issue number.

| Command | When | What it does |
|---|---|---|
| `/ccaa-story-start N` | Before the first Superpowers command of a story | Sets the story to `status: in-progress`, writes the status line, moves the parent feature and epic to in progress |
| `/ccaa-story-complete N` | After review and the final commit | Checks the acceptance items and the push, ticks them, writes the commits into the status line, sets `status: done`, closes the story, refreshes the feature |
| `/ccaa-feature-complete N` | When every story of the feature is done | Checks all stories are closed, marks the feature done and closes it, refreshes the epic |
| `/ccaa-epic-complete N` | When every feature of the epic is done | Marks the epic done and closes it, and marks this file complete |
| `/ccaa-milestone-log N started\|completed` | Used by the four skills above | Updates the Status, Started and Completed columns of the row for issue N in section 3, refreshes the story counts at the top, and pushes |
| `/ccaa-commit-push` | After every task, and at the end of each story | Runs lint and tests, commits one logical change as the repository owner, pushes to `main` |
| `/ccaa-progress-sync N` | Used by the skills above | Rebuilds a feature or epic checklist and its progress line from the real state of its children |

## 5. Notes

- **Work happens on `main`, as in M01.** There is no worktree or pull request step, so `using-git-worktrees` and `finishing-a-development-branch` are left out. Add them to a row if you want a branch per story.
- **Checklists that were out of date.** Epic #29 still lists #30 (Data ingest log), which is an M01 feature, and feature #46 still lists #51 to #54 (cloud sources), which moved to M03. `/ccaa-progress-sync` drops children that point to a different parent, so the first `/ccaa-story-start` cleans this up.
- **Open questions on the issues:** #49 (is the HTTP source wanted), #65 (poll or refresh). The #55 question is decided in D42: values in `.env`, copied into Airflow Variables by story #77.
- **Story #77 was added** while deciding #55 (D42). It is under feature #56 and is built first in Phase 3, because the DAG reads the Variables it creates.
- **Moved to M03 - Cloud Deployment:** #51 S3, #52 Azure Blob, #53 GCP Cloud Storage, #54 Google Drive, and the cloud migration workflow #24. They are not part of this milestone.
- **Where the details are:** every decision behind these issues is in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. The next decision number is D43.
