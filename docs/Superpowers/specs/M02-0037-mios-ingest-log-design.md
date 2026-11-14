# M02-0037 (#87) `mios_ingest_log` table with its DAO, and the exec-log reference

Decisions: D50, D30, D56, D57 and D58 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

The user was away while this design was written; every choice below is recorded as D58 so it can be reviewed and reversed.

## Goal

Record, per MIO, each ingest: its status, its message, its times and its volume. One ingest can have many executions (reruns, batches, a dataset split in parts), so `app_workflows_exec_log` gets an optional reference to the ingest row. No endpoint, no engine code, and no code that derives an ingest's status from its executions (still open, see Out of scope).

## Naming

Singular `Mio`, like `MioDatasetModel` for `mios_datasets`: `MioIngestLogModel`, `MioIngestLogDao`, `MioIngestLogCtx`, `MioIngestLogReq`, `MioIngestLogResp`, `MioIngestLogRecord`, `SqlAlchemyMioIngestLogDao`. Modules: `mio_ingest_log_dao.py`, `mio_ingest_log_dtos.py`, `sqlalchemy_mio_ingest_log_dao.py`. Factory: `DaoObjectsFactory.get_mio_ingest_log_dao()`.

## Table `mios_ingest_log` (migration `0007_create_admin_mios_ingest_log.py`)

| Column | Type | Rules |
|---|---|---|
| id | String(36) | primary key, application-generated UUID |
| mio_id | String(36) | not null, indexed, **no foreign key** (D57); the DAO checks the MIO exists on create |
| status | String(32) | not null, one of `ExecStatus` (the same D30 statuses, shared with the exec log) |
| message | Text | nullable |
| requested_at | DateTime(timezone) | not null, UTC |
| started_at, finished_at | DateTime(timezone) | nullable, UTC |
| rows_loaded | BigInteger | nullable, 0 or more |
| batch_count | Integer | nullable, 0 or more: how many batches or parts the ingest was split into |
| increment_marker | String(255) | nullable: an opaque marker of how far an incremental ingest got (a date, an offset, a cursor); no code reads inside it |

Index `ix_mios_ingest_log_mio_status` on (`mio_id`, `status`).

The same migration adds to `app_workflows_exec_log` the nullable column `mios_ingest_log_id` (String(36), no foreign key) and the index `ix_app_wf_exec_log_mios_ingest_log_id`, so one migration moves both tables and downgrade drops both. The column is added with Alembic batch mode so SQLite can drop it again.

## Status rules (D30)

Reuse `ExecStatus` and its moves unchanged: a new row is `requested`; `requested` goes to `started` or `failed`; `started` goes to `completed` or `failed`; `completed` and `failed` are final; the same status again is accepted and changes nothing; any other move is `CONFLICT`. The check and the write are one transaction with a conditional `UPDATE ... WHERE status = <read status>`, exactly as in `SqlAlchemyAppWfExecLogDao.update` (the first to commit wins; the second gets `CONFLICT`, or `SUCCESS` when the first made the same move). `started_at` is set on the move to `started`, `finished_at` on the move to `completed` or `failed`. `message`, `rows_loaded`, `batch_count` and `increment_marker` are notes, not part of the rules: they may be set on any row, also a final one, so a late callback can still fill in the final volume.

## DAO

`MioIngestLogDao(metaclass=SingletonMeta)`. Every method takes one `MioIngestLogCtx` and returns an integer code; results go to `ctx.resp.records`.

| Method | Needs | Result |
|---|---|---|
| create | `mio_id`; optional `message`, `rows_loaded`, `batch_count`, `increment_marker` | a new `requested` row; NOT_FOUND if the MIO does not exist; INVALID_INPUT for a missing `mio_id` or an invalid message or volume field |
| get | `id` | the row; NOT_FOUND |
| list | optional `mio_id`, `status`, `limit`, `offset` | newest first (`requested_at` descending, then `id`); INVALID_INPUT for a `limit` or `offset` that is not a whole number of 0 or more, or an unknown status |
| update | `id`; any of `status`, `message`, `rows_loaded`, `batch_count`, `increment_marker` | the row; NOT_FOUND; INVALID_INPUT for an unknown status or an invalid message or volume field; CONFLICT for an illegal move; `mio_id` never changes |

There is no delete: the log is append-only (as in D56). Invalid message or volume field: a `message` that is not a string; a `rows_loaded` or `batch_count` that is not an `int` (a `bool` counts as invalid), is negative, or is above its column maximum (`rows_loaded` 9223372036854775807, `batch_count` 2147483647); or an `increment_marker` that is not a string or is over 255 characters. Paging: a `limit` or `offset` that is not an `int` (a `bool` counts as invalid) or is negative is INVALID_INPUT, never an exception. The same checks apply to the exec-log DAO: `limit` and `offset` in `list`, and in `update` an `engine_run_id` or `message` that is not a string (INVALID_INPUT). The impl reads `MioModel` to check the MIO on create: the same exception to D7 as D56 and D57.

## The exec-log reference

- `AppWfExecLogReq`, `AppWfExecLogRecord` and the model gain `mios_ingest_log_id` (nullable).
- `AppWfExecLogDao.create` accepts an optional `mios_ingest_log_id`; when given, the ingest row must exist (read through `MioIngestLogModel` in the same session), otherwise NOT_FOUND. It is stored as given and never changes afterwards (`update` does not touch it).
- `AppWfExecLogDao.list` accepts an optional `mios_ingest_log_id` filter, so all executions of one ingest can be read.
- A workflow without a MIO leaves it NULL (a RAG workflow later, D50).

## Tests

- `tests/test_mio_ingest_log_dao.py`: create (defaults, `requested`, volume stored), NOT_FOUND for a missing MIO, INVALID_INPUT cases (missing `mio_id`, bool, negative, float, long marker), get, list (filters, order, paging, negative paging, unknown status), every legal and illegal move and a repeated status, `started_at` and `finished_at`, notes and volume on a final row, `mio_id` unchanged, a stale second update returns CONFLICT and leaves the row unchanged, a rival callback that commits between the read and the write, a shared transaction with rollback.
- `tests/test_app_wf_exec_log_dao.py`: create with an ingest id (stored; NOT_FOUND for an unknown one; NULL by default), list by `mios_ingest_log_id`, several executions pointing to one ingest row, `update` leaves the reference alone.
- `test_schema.py`: the new table and column, migration `0007` up, down, up. `test_singletons.py`: the factory. `test_postgres.py`: the same flow when `CCA_TEST_POSTGRES_URL` is set (D33).

## Out of scope

Deriving an ingest's status from its executions (for example completed only when every execution is completed), the endpoints and callbacks, deleting log rows, and retiring `data_ingest_log` (#88).
