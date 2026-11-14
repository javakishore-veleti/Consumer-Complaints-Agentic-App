# Milestone M01 - Project Setup and Downloads Feature

**Scope (decision D38 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`):** the foundation of the project, and the data ingest log API.
Everything runs locally. Downloads management is M02 and cloud work is M03.

**Status: complete.** 2 epics, 6 features and 33 stories, all closed.

How to read this file:
- `#12` is the GitHub issue number in this repository. The `M01-00NN` key is the sequence tag at the start of the issue title.
  Keys are not in build order, because some stories were added after the board was first made (for example `#66` carries `M01-0018`).
- The list below is in the order the work was built, not the order of the issue numbers. The commit column is the commit that introduced it.
- The table of contents at the end shows the same issues grouped as epic, feature and story.

## 1. Build order

### Phase 1 - Project skeleton and local infrastructure (commits `f52a4e4`, `17080f3`)

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 1 | #1 | M01-0001 | Epic | Project Organization | (parent of the features below) |
| 2 | #2 | M01-0002 | Feature | Local infrastructure with Docker | `17080f3` |
| 3 | #3 | M01-0003 | Story | Local Apache Airflow 3.4.0 in Docker | `17080f3` |
| 4 | #5 | M01-0005 | Story | Start, stop and status scripts and npm commands | `17080f3` |
| 5 | #6 | M01-0006 | Feature | Repository, documentation and conventions | (grows through the milestone) |
| 6 | #7 | M01-0007 | Story | Repository layout and backup of the early draft | `f52a4e4`, `17080f3` |
| 7 | #12 | M01-0012 | Feature | Layered Middleware project structure | `17080f3` |
| 8 | #13 | M01-0013 | Story | uv project and layered folder skeleton | `17080f3` |

### Phase 2 - Documents, MongoDB and project tracking (commit `a63bd5b`)

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 9 | #4 | M01-0004 | Story | Local MongoDB 8.0 in Docker | `a63bd5b` |
| 10 | #8 | M01-0008 | Story | Product features, architecture and design documents | `a63bd5b` |
| 11 | #9 | M01-0009 | Story | Never commit the CFPB dataset | `a63bd5b` |
| 12 | #10 | M01-0010 | Story | Track the milestone, epics, features and stories as GitHub issues | (GitHub only) |

### Phase 3 - The convention every layer follows (commit `50ab86f`)

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 13 | #14 | M01-0014 | Story | Ctx, Req and Resp convention and shared DTOs | `50ab86f` |

### Phase 4 - The data ingest log, from API to database (commit `78a4d47`)

The foundations the slice needs, then the slice itself.

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 14 | #15 | M01-0015 | Story | Integer return codes | `78a4d47` |
| 15 | #16 | M01-0016 | Story | Interface and objects_factory in every package | `78a4d47` |
| 16 | #18 | M01-0017 | Story | Facade task pattern | `78a4d47` |
| 17 | #66 | M01-0018 | Story | Singleton classes and static objects_factory methods | `78a4d47` |
| 18 | #19 | M01-0019 | Feature | Operational database foundation | `78a4d47` |
| 19 | #20 | M01-0020 | Story | Three schemas: consumer_comp_db, consumer_compl_intellect_db, consumer_comp_users_db | `78a4d47` |
| 20 | #21 | M01-0021 | Story | Configurable database engine (SQLite now, Postgres later) | `78a4d47` |
| 21 | #22 | M01-0022 | Story | Alembic setup and first migration (data_ingest_log) | `78a4d47` |
| 22 | #26 | M01-0026 | Feature | API foundation | `78a4d47` |
| 23 | #27 | M01-0027 | Story | FastAPI application, health endpoint and router wiring | `78a4d47` |
| 24 | #76 | M01-0072 | Epic | Data Ingest Log API (created last, when the milestones were re-scoped; it holds the feature below) | (GitHub only) |
| 25 | #30 | M01-0030 | Feature | Data ingest log | `78a4d47` |
| 26 | #31 | M01-0031 | Story | data_ingest_log table and migration | `78a4d47` |
| 27 | #32 | M01-0032 | Story | Data ingest DAO (create, get, list, update, delete) | `78a4d47` |
| 28 | #33 | M01-0033 | Story | Data ingest facade and tasks | `78a4d47` |
| 29 | #34 | M01-0034 | Story | Data ingest log REST endpoints | `78a4d47` |
| 30 | #35 | M01-0035 | Story | Automated tests for the data ingest log | `78a4d47` |
| 31 | #23 | M01-0023 | Story | Local start script: migrate, then start the API (first as `run_local.sh`, replaced by `run_app.sh`, see #69) | `78a4d47` |

### Phase 5 - Hardening the slice (commit `177369a`)

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 32 | #36 | M01-0036 | Story | Enforce allowed status transitions | `177369a` |
| 33 | #11 | M01-0011 | Story | Enforce layer rules with import-linter in the build | `177369a` |
| 34 | #28 | M01-0028 | Story | Export the OpenAPI specification to a committed file | `177369a` |
| 35 | #25 | M01-0025 | Story | Verify migrations against Postgres | `177369a` |
| 36 | #67 | M01-0066 | Story | One file per facade task (facades/impl/tasks) | `177369a` |
| 37 | #68 | M01-0067 | Story | API endpoints as a singleton class | `177369a` |
| 38 | #69 | M01-0068 | Story | run_app.sh with start, stop and status, and npm scripts | `177369a` |

### Phase 6 - Rules that keep the codebase consistent (commits `8442078`, `2e2b8ad`, `4562399`)

| # | Issue | Key | Type | Title | Commit |
|---|---|---|---|---|---|
| 39 | #70 | M01-0069 | Story | Nothing machine- or person-specific in the repo | `8442078` |
| 40 | #71 | M01-0070 | Story | Scratch space in git-ignored runtime_data/tmp, not /tmp | `8442078`, fixed in `4562399` |
| 41 | #72 | M01-0071 | Story | Every function takes nothing or one ctx object | `2e2b8ad` |

## 2. The same issues grouped by epic and feature

```
Epic #1  M01-0001  Project Organization
|
+-- Feature #2   M01-0002  Local infrastructure with Docker
|     +-- #3   Local Apache Airflow 3.4.0 in Docker
|     +-- #4   Local MongoDB 8.0 in Docker
|     +-- #5   Start, stop and status scripts and npm commands
|
+-- Feature #6   M01-0006  Repository, documentation and conventions
|     +-- #7   Repository layout and backup of the early draft
|     +-- #8   Product features, architecture and design documents
|     +-- #9   Never commit the CFPB dataset
|     +-- #10  Track the milestone, epics, features and stories as GitHub issues
|     +-- #11  Enforce layer rules with import-linter in the build
|     +-- #70  Nothing machine- or person-specific in the repo
|     +-- #71  Scratch space in git-ignored runtime_data/tmp, not /tmp
|
+-- Feature #12  M01-0012  Layered Middleware project structure
|     +-- #13  uv project and layered folder skeleton
|     +-- #14  Ctx, Req and Resp convention and shared DTOs
|     +-- #15  Integer return codes
|     +-- #16  Interface and objects_factory in every package
|     +-- #18  Facade task pattern
|     +-- #66  Singleton classes and static objects_factory methods
|     +-- #67  One file per facade task (facades/impl/tasks)
|     +-- #68  API endpoints as a singleton class
|     +-- #72  Every function takes nothing or one ctx object
|
+-- Feature #19  M01-0019  Operational database foundation
|     +-- #20  Three schemas
|     +-- #21  Configurable database engine (SQLite now, Postgres later)
|     +-- #22  Alembic setup and first migration (data_ingest_log)
|     +-- #23  Local start script: migrate, then start the API
|     +-- #25  Verify migrations against Postgres
|     +-- #69  run_app.sh with start, stop and status, and npm scripts
|
+-- Feature #26  M01-0026  API foundation
      +-- #27  FastAPI application, health endpoint and router wiring
      +-- #28  Export the OpenAPI specification to a committed file

Epic #76  M01-0072  Data Ingest Log API
|
+-- Feature #30  M01-0030  Data ingest log
      +-- #31  data_ingest_log table and migration
      +-- #32  Data ingest DAO (create, get, list, update, delete)
      +-- #33  Data ingest facade and tasks
      +-- #34  Data ingest log REST endpoints
      +-- #35  Automated tests for the data ingest log
      +-- #36  Enforce allowed status transitions
```

## 3. Notes

- **#17** is a stray duplicate of #18 (the "Facade task pattern" story), created by an interrupted run. It is closed and is not part of the counts above.
- **Moved out of this milestone:**
  - M02 - Downloads Management has the dataset status (`system_datasets`), the download API, source locations, the Airflow download DAG and the admin portal.
  - M03 - Cloud Deployment has the cloud migration workflow and the cloud storage sources.
- **Where the details are:** every decision behind these issues is in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (D1 to D41). The issue numbers above are the GitHub issues of this repository.
