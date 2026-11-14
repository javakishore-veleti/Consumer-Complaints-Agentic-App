# M02-0032 (#82) `app_workflows_exec_log` table with its DAO

Decisions: D43, D50, D30, D55 and D56 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Goal

Record every execution of every workflow in `app_workflows_exec_log` (admin schema), with one DAO. The row keeps the workflow's details as they were when the execution was requested. No endpoint and no engine code.

## Naming

Class names shorten `Workflows` to `Wf` (D55): `AppWfExecLogModel`, `AppWfExecLogDao`, `AppWfExecLogCtx`, `AppWfExecLogReq`, `AppWfExecLogResp`, `AppWfExecLogRecord`, `SqlAlchemyAppWfExecLogDao`. Modules follow the class names: `app_wf_exec_log_dao.py`, `app_wf_exec_log_dtos.py`, `sqlalchemy_app_wf_exec_log_dao.py`.

## Table `app_workflows_exec_log` (migration `0004_create_app_workflows_exec_log.py`)

| Column | Type | Rules |
|---|---|---|
| id | String(36) | primary key, application-generated UUID; the only value the API hands to the engine (D51) |
| workflow_id | String(36) | not null, indexed, **no foreign key** (the log must survive a rename or delete of the workflow, and SQLite does not enforce keys by default) |
| workflow_name | String(100) | not null, copied from `app_workflows` |
| engine_type | String(32) | not null, copied |
| engine_workflow_id | String(255) | not null, copied |
| config_used | JSON | nullable (`none_as_null`), a copy of the workflow's config |
| engine_run_id | String(128) | nullable (for example the Airflow run id) |
| status | String(32) | not null, one of `ExecStatus` |
| message | Text | nullable |
| requested_at | DateTime(timezone) | not null, UTC |
| started_at, finished_at | DateTime(timezone) | nullable, UTC |

Index `ix_app_wf_exec_log_workflow_status` on (`workflow_id`, `status`). The optional reference to a MIO ingest row is added by #87 as a nullable column with its own migration.

## Status rules (D30)

`ExecStatus(AppTypeEnum)` in `app/core/common/app_types_constants.py`: `requested`, `started`, `completed`, `failed`, plus the table of allowed moves next to it.

- A new row is always `requested`.
- `requested` goes to `started` or `failed`; `started` goes to `completed` or `failed`; `completed` and `failed` are final.
- The same status again is accepted and changes nothing (Airflow retries).
- Any other move returns `CONFLICT`. The check and the write happen in one DAO transaction.
- `started_at` is set on the move to `started`; `finished_at` on the move to `completed` or `failed`.
- `data_ingest_constants` stays as it is; #88 retires it with `data_ingest_log`.

## DAO

`AppWfExecLogDao(metaclass=SingletonMeta)`. Every method takes one `AppWfExecLogCtx` and returns an integer code; results go to `ctx.resp.records`.

| Method | Needs | Result |
|---|---|---|
| create | `workflow_id` | reads the `app_workflows` row in the same session and copies `workflow_name`, `engine_type`, `engine_workflow_id` and `config` (as `config_used`) into a new `requested` row; NOT_FOUND if the workflow does not exist; INVALID_INPUT without a `workflow_id` |
| get | `id` | the row; NOT_FOUND |
| list | optional `workflow_id`, `status`, `engine_type`, `limit`, `offset` | newest first (`requested_at` descending, then `id`) |
| update | `id`; any of `status`, `engine_run_id`, `message` | the row; NOT_FOUND; INVALID_INPUT for an unknown status or an `engine_run_id` over 128 characters; CONFLICT for an illegal move; the snapshot columns are never changed |

There is no delete: the log is append-only. `create` does not look at `enabled`; whether a disabled workflow may start is policy for the start endpoint (#42). The impl reads the `AppWfModel` table class for the copy: the one place a DAO touches a second table (D56).

Files: `dao/app_wf_exec_log_dao.py`, `dao/impl/sqlalchemy_app_wf_exec_log_dao.py`, `common/dtos/app_wf_exec_log_dtos.py`, `AppWfExecLogModel` in `dao/impl/models.py`, `get_app_wf_exec_log_dao()` in `dao/objects_factory.py` (static-method style; `init()` is #80). Only `impl/` sees SQLAlchemy.

## Tests

- `tests/test_app_wf_exec_log_dao.py`: create with the snapshot and `requested` status; the snapshot unchanged after the workflow is renamed or deleted; NOT_FOUND and INVALID_INPUT on create; get; list filters, order, limit and offset; every legal and illegal move, and a repeated status; `started_at` and `finished_at`; NULL `config_used`; a stale second update after `completed` returns CONFLICT and leaves the row unchanged; a shared transaction with rollback.
- `test_schema.py`: the table and migration `0004` up, down, up. `test_singletons.py`: the factory. `test_postgres.py`: the same flow when `CCA_TEST_POSTGRES_URL` is set (D33).

## Out of scope

The MIO ingest reference (#87), the engine callback endpoints, deleting log rows.
