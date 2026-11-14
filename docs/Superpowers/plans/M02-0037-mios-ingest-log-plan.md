# M02-0037 (#87) `mios_ingest_log` table with its DAO, and the exec-log reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `mios_ingest_log` in the admin schema (one row per ingest of a MIO: status, message, times, volume) with `MioIngestLogDao` (create, get, list, update; no delete), and give `app_workflows_exec_log` an optional `mios_ingest_log_id` so many executions can point to one ingest.

**Architecture:** Follow the `app_workflows_exec_log` (#82) pattern exactly: a SQLAlchemy model in `dao/impl/models.py`, one Alembic migration `0007` that creates the new table **and** adds the column to the exec log (batch mode, so SQLite can drop it again), DTOs in `common/dtos/`, an interface in `dao/`, a SQLAlchemy implementation in `dao/impl/`, and a singleton handed out by `dao/objects_factory.py`. Status moves reuse `ExecStatus` and the conditional `UPDATE ... WHERE status = <read status>` of `SqlAlchemyAppWfExecLogDao.update` (D30). No foreign keys (D57, D58): the DAOs check the MIO and the ingest row in the same transaction.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, pytest, `uv`; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0037-mios-ingest-log-design.md`. Decisions: D5, D7, D26, D30, D37, D45, D50, D55, D56, D57, D58 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there unless it says the repository root. All paths below are relative to it, except the plan and spec paths.
- Table `mios_ingest_log` in schema `consumer_comp_admin_db` (`SCHEMA_ADMIN`); migration `0007_create_admin_mios_ingest_log.py` with `revision = "0007"` and `down_revision = "0006"`. The same migration adds `app_workflows_exec_log.mios_ingest_log_id` and its index; its downgrade removes both.
- Names (D55, singular `Mio` like `MioDatasetModel`): `MioIngestLogModel`, `MioIngestLogDao`, `MioIngestLogCtx`, `MioIngestLogReq`, `MioIngestLogResp`, `MioIngestLogRecord`, `SqlAlchemyMioIngestLogDao`; modules `mio_ingest_log_dao.py`, `mio_ingest_log_dtos.py`, `sqlalchemy_mio_ingest_log_dao.py`; factory `DaoObjectsFactory.get_mio_ingest_log_dao()`. Index names `ix_mios_ingest_log_mio_status` and `ix_app_wf_exec_log_mios_ingest_log_id`.
- Ids are `String(36)` `uuid4` strings made by the DAO. Times are stored UTC; SQLite hands them back naive, so `_to_record` adds `timezone.utc` (as the exec-log DAO does).
- Statuses are `ExecStatus` (`app/core/common/app_types_constants.py`) with its D30 moves, unchanged: new rows are `requested`; `requested` to `started` or `failed`; `started` to `completed` or `failed`; `completed` and `failed` are final; the same status again is SUCCESS and changes no time; anything else is `CONFLICT`. `started_at` is set on the move to `started`, `finished_at` on the move to `completed` or `failed`.
- Notes (`message`, `rows_loaded`, `batch_count`, `increment_marker`) may be set on any row, also a final one. Invalid volume: `rows_loaded` or `batch_count` not an `int`, a `bool`, or negative; `increment_marker` not a `str` or longer than 255 characters.
- No delete on either log (append-only, D56, D58). `mio_id` and `mios_ingest_log_id` never change after create. The DAO does not derive an ingest's status from its executions (out of scope).
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `datetime`, `dict`, `list`... (D5, D37, enforced by `tests/test_ctx_only_signatures.py`, which scans `app`, `alembic`, `scripts` and `main.py`; it skips `self` and `cls`). So a helper that would need a row **and** a session is written inline in the DAO method instead.
- Do not annotate with `list[...]` inside a DAO class body: the method named `list` shadows the builtin there. Use list comprehensions and no annotation.
- Every method that takes a ctx returns an integer from `app/core/common/return_codes.py`: `SUCCESS 0`, `FAILURE 1`, `NOT_FOUND 2`, `INVALID_INPUT 3`, `CONFLICT 4`.
- All early `return`s in a DAO method happen **before** any change to a loaded row: leaving the `with unit_of_work(...)` block commits whatever is pending.
- Migrations use Alembic Python ops, never raw SQL strings (D23), and work on SQLite and Postgres (D33).
- Only `dao/impl` imports SQLAlchemy; only `dao/objects_factory.py` imports `dao/impl` (`uv run lint-imports`: `Contracts: 7 kept, 0 broken.`). Every class in `dao` is a singleton through its interface's `metaclass=SingletonMeta` (D26); the new DAO is registered in the factory in the task that adds it (D45 acceptance).
- The seed (migration `0006`) puts four MIOs in every migrated test database; test MIOs use the prefix `t_` so names never clash with the seed.
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35).
- Commit with `/ccaa-commit-push 87` (it checks lint and tests, writes the `M02-0037 #87: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/dao/impl/models.py` (modify) | `MioIngestLogModel`; the `mios_ingest_log_id` column and index on `AppWfExecLogModel` |
| `alembic/versions/0007_create_admin_mios_ingest_log.py` (create) | the new table and index; the exec-log column and index (batch mode) |
| `app/core/common/dtos/mio_ingest_log_dtos.py` (create) | Record, Req, Resp, Ctx of `mios_ingest_log` |
| `app/core/dao/mio_ingest_log_dao.py` (create) | the interface |
| `app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py` (create) | the implementation |
| `app/core/dao/objects_factory.py` (modify) | `get_mio_ingest_log_dao()` |
| `app/core/common/dtos/app_wf_exec_log_dtos.py`, `app/core/dao/app_wf_exec_log_dao.py`, `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py` (modify) | the exec-log reference |
| `tests/test_schema.py`, `tests/test_singletons.py`, `tests/test_app_wf_exec_log_dao.py`, `tests/test_postgres.py` (modify) | tests |
| `tests/test_mio_ingest_log_dao.py`, `tests/test_mio_ingest_flow.py` (create) | tests |
| `DESIGN.md` (modify) | marks the ingest log and the reference as built in #87 |

---

### Task 1: the table and the exec-log column (models and migration `0007`)

**Files:**
- Modify: `app/core/dao/impl/models.py`
- Create: `alembic/versions/0007_create_admin_mios_ingest_log.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `MioIngestLogModel` in `app.core.dao.impl.models` with columns `id`, `mio_id`, `status`, `message`, `requested_at`, `started_at`, `finished_at`, `rows_loaded`, `batch_count`, `increment_marker`; `AppWfExecLogModel.mios_ingest_log_id: Mapped[str | None]`. After `alembic upgrade head` the table, the column and both indexes exist.

- [ ] **Step 1: Write the failing tests**

In `tests/test_schema.py`, in `test_app_workflows_exec_log_table_is_in_the_admin_schema_with_the_expected_columns`, add `"mios_ingest_log_id",` as the last item of the `assert set(columns) == {...}` set, directly after `"finished_at",`, so the set reads:

```python
    assert set(columns) == {
        "id",
        "workflow_id",
        "workflow_name",
        "engine_type",
        "engine_workflow_id",
        "config_used",
        "engine_run_id",
        "status",
        "message",
        "requested_at",
        "started_at",
        "finished_at",
        "mios_ingest_log_id",
    }
```

Then append at the end of `tests/test_schema.py` (it already has `_admin_db`, `_columns`, `command`, `Config` and `PROJECT_ROOT`):

```python


def test_mios_ingest_log_table_is_in_the_admin_schema_with_the_expected_columns(data_dir):
    with _admin_db(data_dir) as db:
        columns = _columns(db, "mios_ingest_log")
        indexes = {r[1] for r in db.execute("pragma index_list(mios_ingest_log)")}
        foreign_keys = db.execute("pragma foreign_key_list(mios_ingest_log)").fetchall()
    assert columns == {
        "id": ("VARCHAR(36)", 1),
        "mio_id": ("VARCHAR(36)", 1),
        "status": ("VARCHAR(32)", 1),
        "message": ("TEXT", 0),
        "requested_at": ("DATETIME", 1),
        "started_at": ("DATETIME", 0),
        "finished_at": ("DATETIME", 0),
        "rows_loaded": ("BIGINT", 0),
        "batch_count": ("INTEGER", 0),
        "increment_marker": ("VARCHAR(255)", 0),
    }
    assert "ix_mios_ingest_log_mio_status" in indexes
    assert foreign_keys == []


def test_exec_log_has_the_optional_ingest_reference_without_a_foreign_key(data_dir):
    with _admin_db(data_dir) as db:
        columns = _columns(db, "app_workflows_exec_log")
        indexes = {r[1] for r in db.execute("pragma index_list(app_workflows_exec_log)")}
        foreign_keys = db.execute("pragma foreign_key_list(app_workflows_exec_log)").fetchall()
    assert columns["mios_ingest_log_id"] == ("VARCHAR(36)", 0)
    assert {"ix_app_wf_exec_log_mios_ingest_log_id", "ix_app_wf_exec_log_workflow_status"} <= indexes
    assert foreign_keys == []


def test_migration_0007_runs_down_and_up_and_keeps_the_exec_log_rows(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into app_workflows_exec_log (id, workflow_id, workflow_name, engine_type, engine_workflow_id,"
            " status, requested_at, mios_ingest_log_id) values ('e1', 'w', 'n', 'apache_airflow', 'd', 'requested',"
            " '2026-01-01', 'some-ingest')"
        )
    command.downgrade(config, "0006")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'mios_ingest_log'").fetchall() == []
        assert "mios_ingest_log_id" not in _columns(db, "app_workflows_exec_log")
        indexes = {r[1] for r in db.execute("pragma index_list(app_workflows_exec_log)")}
        assert "ix_app_wf_exec_log_mios_ingest_log_id" not in indexes
        assert "ix_app_wf_exec_log_workflow_status" in indexes  # the rebuilt table keeps its other index
        assert db.execute("select id, workflow_name from app_workflows_exec_log").fetchall() == [("e1", "n")]
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'mios_ingest_log'").fetchall() != []
        assert db.execute("select id, mios_ingest_log_id from app_workflows_exec_log").fetchall() == [("e1", None)]
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_schema.py -v`
Expected: the four tests above FAIL (`mios_ingest_log_id` missing from the set; `no such table: mios_ingest_log` shows up as an empty column dict; `KeyError: 'mios_ingest_log_id'`; the insert fails with `table app_workflows_exec_log has no column named mios_ingest_log_id`).

- [ ] **Step 3: Add the models**

In `app/core/dao/impl/models.py` replace the sqlalchemy import line with:

```python
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
```

In `class AppWfExecLogModel`, add the second `Index` to `__table_args__`, so it reads:

```python
    __table_args__ = (
        Index("ix_app_wf_exec_log_workflow_status", "workflow_id", "status"),
        Index("ix_app_wf_exec_log_mios_ingest_log_id", "mios_ingest_log_id"),
        {"schema": SCHEMA_ADMIN},
    )
```

and add, directly after its `finished_at` column (the last line of the class):

```python
    # The MIO ingest this execution belongs to, or NULL (a workflow without a MIO). No foreign key (D58).
    mios_ingest_log_id: Mapped[str | None] = mapped_column(String(36))
```

Append at the end of the file:

```python


class MioIngestLogModel(Base):
    __tablename__ = "mios_ingest_log"
    __table_args__ = (
        Index("ix_mios_ingest_log_mio_status", "mio_id", "status"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D57, D58): the DAO checks the MIO on create.
    mio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Volume (D58): notes that may be set on any row, also a final one.
    rows_loaded: Mapped[int | None] = mapped_column(BigInteger)
    batch_count: Mapped[int | None] = mapped_column(Integer)
    # An opaque marker of how far an incremental ingest got. No code reads inside it.
    increment_marker: Mapped[str | None] = mapped_column(String(255))
```

- [ ] **Step 4: Add the migration**

Create `alembic/versions/0007_create_admin_mios_ingest_log.py`:

```python
"""create mios_ingest_log in the admin schema and the optional ingest reference of app_workflows_exec_log

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"


def upgrade() -> None:
    op.create_table(
        "mios_ingest_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),  # no foreign key on purpose (D57, D58)
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_loaded", sa.BigInteger(), nullable=True),
        sa.Column("batch_count", sa.Integer(), nullable=True),
        sa.Column("increment_marker", sa.String(255), nullable=True),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_ingest_log_mio_status", "mios_ingest_log", ["mio_id", "status"], schema=SCHEMA)
    # Batch mode, so SQLite can drop the column again on downgrade (it rebuilds the table).
    with op.batch_alter_table("app_workflows_exec_log", schema=SCHEMA) as batch:
        batch.add_column(sa.Column("mios_ingest_log_id", sa.String(36), nullable=True))  # no foreign key (D58)
        batch.create_index("ix_app_wf_exec_log_mios_ingest_log_id", ["mios_ingest_log_id"])


def downgrade() -> None:
    with op.batch_alter_table("app_workflows_exec_log", schema=SCHEMA) as batch:
        batch.drop_index("ix_app_wf_exec_log_mios_ingest_log_id")
        batch.drop_column("mios_ingest_log_id")
    op.drop_index("ix_mios_ingest_log_mio_status", table_name="mios_ingest_log", schema=SCHEMA)
    op.drop_table("mios_ingest_log", schema=SCHEMA)
```

- [ ] **Step 5: Run them and see them pass**

Run: `uv run pytest tests/test_schema.py -v && uv run pytest && uv run lint-imports`
Expected: all PASS (the older `test_migration_0003/0004/0005_runs_down_and_up` tests now also run `0007` down and up); `Contracts: 7 kept, 0 broken.` The exec-log DAO tests still pass: the column is nullable and the DAO does not read it yet.

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 87` with summary `mios_ingest_log table and the exec-log column (migration 0007)` and files `app/core/dao/impl/models.py alembic/versions/0007_create_admin_mios_ingest_log.py tests/test_schema.py`.

---

### Task 2: `MioIngestLogDao` create, get and list

**Files:**
- Create: `app/core/common/dtos/mio_ingest_log_dtos.py`, `app/core/dao/mio_ingest_log_dao.py`, `app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py`
- Modify: `app/core/dao/objects_factory.py`, `tests/test_singletons.py`
- Test: `tests/test_mio_ingest_log_dao.py`

**Interfaces:**
- Consumes: `MioIngestLogModel`, `MioModel` (Task 1 and #86); `MioDao.create` and `MioCtx`/`MioReq` in the tests.
- Produces: `MioIngestLogRecord(id, mio_id, status, message, requested_at, started_at, finished_at, rows_loaded, batch_count, increment_marker)`; `MioIngestLogReq(id, mio_id, status, message, rows_loaded, batch_count, increment_marker, limit, offset)` (all default `None`); `MioIngestLogResp(records: list[MioIngestLogRecord])`; `MioIngestLogCtx(transaction, req, resp)`; `MioIngestLogDao.create/get/list(ctx: MioIngestLogCtx) -> int`; `DaoObjectsFactory.get_mio_ingest_log_dao() -> MioIngestLogDao`. Module-level in `sqlalchemy_mio_ingest_log_dao`: `_now() -> datetime` (tests replace it), `MARKER_MAX = 255`, `NOTE_FIELDS`, `_has_invalid_volume(req: MioIngestLogReq) -> bool`, `_notes_of(req: MioIngestLogReq) -> dict` (Task 3 uses both).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mio_ingest_log_dao.py`:

```python
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogRecord, MioIngestLogReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_ingest_log_dao as dao_impl
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> MioIngestLogCtx:
    return MioIngestLogCtx(req=MioIngestLogReq(**fields))


def _mio(name="t_mio") -> str:
    ctx = MioCtx(req=MioReq(name=name))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ingest(mio_id: str, **more) -> MioIngestLogRecord:
    ctx = _ctx(mio_id=mio_id, **more)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _ingest_rows(data_dir) -> list[tuple]:
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        return db.execute("select id, mio_id from mios_ingest_log").fetchall()


def _list(**fields) -> list[MioIngestLogRecord]:
    ctx = _ctx(**fields)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def _one_tick_per_call(monkeypatch):
    """Makes every _now() later than the one before, so the order of rows does not depend on the clock."""
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    ticks = (start + timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(dao_impl, "_now", lambda: next(ticks))


def test_create_starts_as_requested_with_empty_volume(data_dir):
    mio_id = _mio()
    row = _ingest(mio_id)
    assert len(row.id) == 36
    assert (row.mio_id, row.status) == (mio_id, "requested")
    assert (row.message, row.started_at, row.finished_at) == (None, None, None)
    assert (row.rows_loaded, row.batch_count, row.increment_marker) == (None, None, None)
    assert row.requested_at.tzinfo is not None


def test_create_stores_the_given_message_and_volume(data_dir):
    row = _ingest(_mio(), message="first load", rows_loaded=0, batch_count=3, increment_marker="2026-11-01")
    assert (row.message, row.rows_loaded, row.batch_count, row.increment_marker) == ("first load", 0, 3, "2026-11-01")
    fetched = _ctx(id=row.id)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(fetched) == SUCCESS
    assert fetched.resp.records == [row]


def test_create_stores_a_row_count_above_the_32_bit_range(data_dir):
    assert _ingest(_mio(), rows_loaded=5_000_000_000).rows_loaded == 5_000_000_000


def test_create_always_starts_as_requested_whatever_the_request_says(data_dir):
    assert _ingest(_mio(), status="completed").status == "requested"


def test_create_for_an_unknown_mio_is_not_found_and_stores_nothing(data_dir):
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(_ctx(mio_id="no-such-mio")) == NOT_FOUND
    assert _ingest_rows(data_dir) == []


@pytest.mark.parametrize(
    "fields",
    [
        {"mio_id": None},
        {"mio_id": ""},
        {"rows_loaded": True},
        {"rows_loaded": -1},
        {"rows_loaded": 1.5},
        {"rows_loaded": "10"},
        {"batch_count": False},
        {"batch_count": -2},
        {"batch_count": 2.0},
        {"increment_marker": "m" * 256},
        {"increment_marker": 20261101},
    ],
)
def test_create_rejects_a_missing_mio_id_or_an_invalid_volume_field(data_dir, fields):
    req = {"mio_id": _mio(), **fields}
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(_ctx(**req)) == INVALID_INPUT
    assert _ingest_rows(data_dir) == []


def test_create_accepts_a_marker_of_exactly_255_characters(data_dir):
    assert _ingest(_mio(), increment_marker="m" * 255).increment_marker == "m" * 255


def test_get_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    assert logs.get(_ctx()) == INVALID_INPUT
    assert logs.get(_ctx(id="no-such-row")) == NOT_FOUND


def test_list_of_an_empty_log_is_success_with_no_rows(data_dir):
    assert _list() == []


def test_list_is_newest_first(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    mio_id = _mio()
    first, second, third = (_ingest(mio_id) for _ in range(3))
    assert [r.id for r in _list()] == [third.id, second.id, first.id]


def test_list_filters_by_mio_and_status(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    three, six = _mio("t_three"), _mio("t_six")
    a = _ingest(three)
    b = _ingest(three)
    c = _ingest(six)
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute("update mios_ingest_log set status = 'started' where id = ?", (b.id,))  # update comes in a later task

    assert [r.id for r in _list(mio_id=three)] == [b.id, a.id]
    assert [r.id for r in _list(mio_id=six)] == [c.id]
    assert [r.id for r in _list(status="started")] == [b.id]
    assert [r.id for r in _list(status="requested")] == [c.id, a.id]
    assert [r.id for r in _list(mio_id=three, status="requested")] == [a.id]
    assert _list(mio_id="no-such-mio") == []
    assert _list(status="completed") == []


def test_list_limit_and_offset(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    mio_id = _mio()
    rows = [_ingest(mio_id) for _ in range(5)]
    newest_first = [r.id for r in reversed(rows)]
    assert [r.id for r in _list(limit=2)] == newest_first[:2]
    assert [r.id for r in _list(limit=2, offset=2)] == newest_first[2:4]
    assert [r.id for r in _list(offset=4)] == newest_first[4:]


def test_list_rejects_a_negative_limit_or_offset_and_an_unknown_status(data_dir):
    _ingest(_mio())
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    assert logs.list(_ctx(limit=-1)) == INVALID_INPUT
    assert logs.list(_ctx(offset=-1)) == INVALID_INPUT
    assert logs.list(_ctx(status="bogus")) == INVALID_INPUT
    zero = _ctx(limit=0)
    assert logs.list(zero) == SUCCESS and zero.resp.records == []


def test_create_reads_the_mio_inside_the_same_shared_transaction(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    new_mio = MioCtx(transaction=rolled_back, req=MioReq(name="t_inside"))
    assert DaoObjectsFactory.get_mio_dao().create(new_mio) == SUCCESS  # not committed: only this transaction sees it
    ingest = MioIngestLogCtx(transaction=rolled_back, req=MioIngestLogReq(mio_id=new_mio.resp.records[0].id))
    assert logs.create(ingest) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert _list() == []
    assert DaoObjectsFactory.get_mio_dao().get(MioCtx(req=MioReq(name="t_inside"))) == NOT_FOUND

    mio_id = _mio("t_kept")
    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    kept = MioIngestLogCtx(transaction=committed, req=MioIngestLogReq(mio_id=mio_id))
    assert logs.create(kept) == SUCCESS
    assert _list() == []  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert [r.id for r in _list()] == [kept.resp.records[0].id]
```

(`CONFLICT` is imported now because Task 3 appends tests that use it.)

In `tests/test_singletons.py`:
- add `from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import SqlAlchemyMioIngestLogDao` directly below `from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao`;
- add `from app.core.dao.mio_ingest_log_dao import MioIngestLogDao` directly below `from app.core.dao.mio_dataset_dao import MioDatasetDao`;
- in `test_factories_return_the_same_object_typed_as_the_interface`, add `(DaoObjectsFactory.get_mio_ingest_log_dao, MioIngestLogDao),` directly below `(DaoObjectsFactory.get_mio_dataset_dao, MioDatasetDao),`;
- in `test_the_classes_themselves_are_singletons`, add `assert SqlAlchemyMioIngestLogDao() is SqlAlchemyMioIngestLogDao()` directly below `assert SqlAlchemyMioDatasetDao() is SqlAlchemyMioDatasetDao()`.

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_mio_ingest_log_dao.py tests/test_singletons.py -v`
Expected: ERROR at collection with `ModuleNotFoundError: No module named 'app.core.common.dtos.mio_ingest_log_dtos'` (and `app.core.dao.impl.sqlalchemy_mio_ingest_log_dao` for the singletons test).

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/mio_ingest_log_dtos.py`:

```python
"""Ctx, Req and Resp for the mios_ingest_log table (each ingest of a MIO, DESIGN.md D50 and D58)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioIngestLogRecord:
    id: str
    mio_id: str
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    rows_loaded: int | None
    batch_count: int | None
    increment_marker: str | None


@dataclass
class MioIngestLogReq:
    """A field left as None means "not given". id identifies one row. mio_id is what create needs and list filters
    on; status is a list filter; status, message, rows_loaded, batch_count and increment_marker are what update
    changes (create also takes the last four)."""

    id: str | None = None
    mio_id: str | None = None
    status: str | None = None
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class MioIngestLogResp:
    records: list[MioIngestLogRecord] = field(default_factory=list)


@dataclass
class MioIngestLogCtx(TransactionalCtx):
    req: MioIngestLogReq = field(default_factory=MioIngestLogReq)
    resp: MioIngestLogResp = field(default_factory=MioIngestLogResp)
```

- [ ] **Step 4: Add the interface**

Create `app/core/dao/mio_ingest_log_dao.py`:

```python
"""Interface of the DAO for the mios_ingest_log table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx
from app.core.common.singleton import SingletonMeta


class MioIngestLogDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioIngestLogCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    One row per ingest of a MIO (D50, D58). The log is append-only: there is no delete. mio_id is a plain column
    with no foreign key; create checks that the MIO exists. The volume fields are rows_loaded and batch_count
    (whole numbers, 0 or more) and increment_marker (an opaque string of up to 255 characters that no code reads
    inside); a bool is not a whole number here."""

    @abstractmethod
    def create(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.mio_id. Optional: message, rows_loaded, batch_count, increment_marker. The new row is always
        "requested", whatever req.status says, and is returned. INVALID_INPUT without a mio_id or for an invalid
        volume field, NOT_FOUND if there is no such MIO (read in the same transaction)."""

    @abstractmethod
    def get(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: MioIngestLogCtx) -> int:
        """Optional filters: req.mio_id, req.status; optional req.limit and req.offset. Newest first (requested_at
        descending, then id). An empty result is SUCCESS with no records. INVALID_INPUT for a negative limit or
        offset or an unknown status."""
```

- [ ] **Step 5: Add the implementation**

Create `app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py`:

```python
"""MioIngestLogDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioModel to check the MIO on create (no foreign key, D57 and D58)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogRecord, MioIngestLogReq
from app.core.common.return_codes import FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import MioIngestLogModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao

log = logging.getLogger(__name__)

MARKER_MAX = 255
NOTE_FIELDS = ("message", "rows_loaded", "batch_count", "increment_marker")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(row: MioIngestLogModel) -> MioIngestLogRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    times = {name: getattr(row, name) for name in ("requested_at", "started_at", "finished_at")}
    times = {
        name: value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
        for name, value in times.items()
    }
    return MioIngestLogRecord(
        id=row.id,
        mio_id=row.mio_id,
        status=row.status,
        message=row.message,
        rows_loaded=row.rows_loaded,
        batch_count=row.batch_count,
        increment_marker=row.increment_marker,
        **times,
    )


def _has_invalid_volume(req: MioIngestLogReq) -> bool:
    """True when rows_loaded or batch_count is given but is not a whole number of 0 or more (a bool is not one),
    or increment_marker is given but is not a string of up to MARKER_MAX characters."""
    for count in (req.rows_loaded, req.batch_count):
        if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
            return True
    marker = req.increment_marker
    return marker is not None and (not isinstance(marker, str) or len(marker) > MARKER_MAX)


def _notes_of(req: MioIngestLogReq) -> dict:
    """The given message and volume fields: informational, so they may change on any row."""
    return {name: getattr(req, name) for name in NOTE_FIELDS if getattr(req, name) is not None}


def _new_row(req: MioIngestLogReq) -> MioIngestLogModel:
    """A requested ingest of req.mio_id with the given notes."""
    return MioIngestLogModel(
        id=str(uuid4()),
        mio_id=req.mio_id,
        status=ExecStatus.REQUESTED.value,
        requested_at=_now(),
        **_notes_of(req),
    )


class SqlAlchemyMioIngestLogDao(MioIngestLogDao):
    def create(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.mio_id or _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None:
                    return NOT_FOUND
                row = _new_row(req)
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log create failed")
            return FAILURE

    def get(self, ctx: MioIngestLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioIngestLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log get failed")
            return FAILURE

    def list(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if (req.limit is not None and req.limit < 0) or (req.offset is not None and req.offset < 0):
            return INVALID_INPUT  # SQLite would return every row, Postgres would fail: reject on both
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        try:
            query = select(MioIngestLogModel)
            if req.mio_id:
                query = query.where(MioIngestLogModel.mio_id == req.mio_id)
            if req.status:
                query = query.where(MioIngestLogModel.status == req.status)
            query = query.order_by(MioIngestLogModel.requested_at.desc(), MioIngestLogModel.id)
            if req.limit is not None:
                query = query.limit(req.limit)
            if req.offset:
                query = query.offset(req.offset)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log list failed")
            return FAILURE
```

- [ ] **Step 6: Register it in the factory**

In `app/core/dao/objects_factory.py` add `from app.core.dao.mio_ingest_log_dao import MioIngestLogDao` directly below `from app.core.dao.mio_dataset_dao import MioDatasetDao`, and add this method directly after `get_mio_dataset_dao`:

```python
    @staticmethod
    def get_mio_ingest_log_dao() -> MioIngestLogDao:
        from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import SqlAlchemyMioIngestLogDao

        return SqlAlchemyMioIngestLogDao()
```

- [ ] **Step 7: Run them and see them pass**

Run: `uv run pytest tests/test_mio_ingest_log_dao.py tests/test_singletons.py -v && uv run pytest && uv run lint-imports`
Expected: all PASS (including `tests/test_ctx_only_signatures.py`: every new helper takes one `MioIngestLogReq` or `MioIngestLogModel`); `Contracts: 7 kept, 0 broken.`

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 87` with summary `MioIngestLogDao create, get and list` and files `app/core/common/dtos/mio_ingest_log_dtos.py app/core/dao/mio_ingest_log_dao.py app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py app/core/dao/objects_factory.py tests/test_mio_ingest_log_dao.py tests/test_singletons.py`.

---

### Task 3: `MioIngestLogDao.update` (D30 moves, notes and volume)

**Files:**
- Modify: `app/core/dao/mio_ingest_log_dao.py`, `app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py`
- Test: `tests/test_mio_ingest_log_dao.py`

**Interfaces:**
- Consumes: from Task 2 `_now`, `_has_invalid_volume(req)`, `_notes_of(req)`, `_to_record(row)`, the test helpers `_ctx`, `_mio`, `_ingest`.
- Produces: `MioIngestLogDao.update(ctx: MioIngestLogCtx) -> int`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_mio_ingest_log_dao.py`:

```python


# ---- update (D30) ----


def _update(row_id: str, **fields) -> tuple[int, MioIngestLogCtx]:
    ctx = _ctx(id=row_id, **fields)
    return DaoObjectsFactory.get_mio_ingest_log_dao().update(ctx), ctx


def _stored(row_id: str) -> MioIngestLogRecord:
    ctx = _ctx(id=row_id)
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def test_requested_to_started_sets_started_at_and_the_notes(data_dir):
    row = _ingest(_mio())
    code, ctx = _update(row.id, status="started", message="picked up", batch_count=4)
    assert code == SUCCESS
    started = ctx.resp.records[0]
    assert (started.status, started.message, started.batch_count) == ("started", "picked up", 4)
    assert started.started_at is not None and started.started_at.tzinfo is not None
    assert started.finished_at is None
    assert _stored(row.id) == started


def test_started_to_completed_sets_finished_at_keeps_started_at_and_stores_the_volume(data_dir):
    row = _ingest(_mio())
    started = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="completed", rows_loaded=1200, increment_marker="2026-11-13")
    assert code == SUCCESS
    done = ctx.resp.records[0]
    assert done.status == "completed"
    assert done.started_at == started.started_at
    assert done.finished_at is not None and done.finished_at >= done.started_at
    assert (done.rows_loaded, done.increment_marker) == (1200, "2026-11-13")


def test_requested_to_failed_sets_finished_at_and_leaves_started_at_empty(data_dir):
    row = _ingest(_mio())
    code, ctx = _update(row.id, status="failed", message="could not start")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert (failed.status, failed.message) == ("failed", "could not start")
    assert failed.started_at is None and failed.finished_at is not None


def test_started_then_failed_is_a_legal_path(data_dir):
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    code, ctx = _update(row.id, status="failed", message="batch 3 failed")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert failed.status == "failed" and failed.started_at is not None and failed.finished_at is not None


@pytest.mark.parametrize(
    "path, bad",
    [
        ((), "completed"),
        (("started",), "requested"),
        (("started", "completed"), "started"),
        (("started", "completed"), "failed"),
        (("started", "completed"), "requested"),
        (("failed",), "started"),
        (("failed",), "completed"),
        (("failed",), "requested"),
    ],
)
def test_an_illegal_move_is_a_conflict_and_changes_nothing(data_dir, path, bad):
    row = _ingest(_mio())
    for status in path:
        assert _update(row.id, status=status)[0] == SUCCESS
    before = _stored(row.id)
    code, _ = _update(row.id, status=bad, message="must not be stored", rows_loaded=99, increment_marker="no")
    assert code == CONFLICT
    assert _stored(row.id) == before


def test_the_same_status_again_is_accepted_and_changes_no_time(data_dir):
    row = _ingest(_mio())
    first = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="started", message="retry of the callback")
    assert code == SUCCESS
    again = ctx.resp.records[0]
    assert again.started_at == first.started_at and again.finished_at is None
    assert again.message == "retry of the callback"


def test_update_without_a_status_changes_only_the_given_fields(data_dir):
    row = _ingest(_mio(), message="kept", batch_count=2)
    code, ctx = _update(row.id, rows_loaded=10)
    assert code == SUCCESS
    after = ctx.resp.records[0]
    assert (after.status, after.message, after.batch_count, after.rows_loaded) == ("requested", "kept", 2, 10)


def test_a_final_row_keeps_its_status_and_times_but_still_accepts_the_notes_and_volume(data_dir):
    # D30 protects the status and the times; the message and the volume are notes a late callback may still fill in.
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    done = _update(row.id, status="completed")[1].resp.records[0]
    code, ctx = _update(
        row.id, status="completed", message="late note", rows_loaded=5000, batch_count=7, increment_marker="offset:5000"
    )
    assert code == SUCCESS
    after = ctx.resp.records[0]
    assert (after.status, after.started_at, after.finished_at) == (done.status, done.started_at, done.finished_at)
    assert (after.message, after.rows_loaded, after.batch_count, after.increment_marker) == (
        "late note",
        5000,
        7,
        "offset:5000",
    )
    code, ctx = _update(row.id, rows_loaded=5001)  # no status at all on a final row
    assert code == SUCCESS and ctx.resp.records[0].rows_loaded == 5001


def test_update_never_changes_the_mio(data_dir):
    mio_id = _mio()
    row = _ingest(mio_id)
    code, ctx = _update(row.id, mio_id=_mio("t_other"), status="started")
    assert code == SUCCESS
    assert ctx.resp.records[0].mio_id == mio_id
    assert _stored(row.id).mio_id == mio_id


def test_a_stale_second_update_after_completed_is_a_conflict(data_dir):
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    assert _update(row.id, status="completed", rows_loaded=10)[0] == SUCCESS
    done = _stored(row.id)
    assert _update(row.id, status="failed", rows_loaded=0)[0] == CONFLICT  # a callback that arrives late
    assert _stored(row.id) == done


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "bogus"},
        {"rows_loaded": True},
        {"rows_loaded": -1},
        {"rows_loaded": 2.5},
        {"batch_count": -1},
        {"batch_count": True},
        {"increment_marker": "m" * 256},
        {"increment_marker": 7},
    ],
)
def test_update_rejects_an_unknown_status_or_an_invalid_volume_field(data_dir, fields):
    row = _ingest(_mio())
    assert _update(row.id, **fields)[0] == INVALID_INPUT
    assert _stored(row.id) == row


def test_update_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    assert DaoObjectsFactory.get_mio_ingest_log_dao().update(_ctx(status="started")) == INVALID_INPUT
    assert _update("no-such-row", status="started")[0] == NOT_FOUND


def test_a_rival_move_made_after_the_read_is_not_overwritten(data_dir, monkeypatch):
    # _now() runs after update has read the row and before it writes, so a rival callback that commits inside it
    # is exactly the race: two callbacks both read "started".
    row = _ingest(_mio())
    assert _update(row.id, status="started")[0] == SUCCESS
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="failed", message="rival")[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, _ = _update(row.id, status="completed", message="loser", rows_loaded=42)
    assert code == CONFLICT
    stored = _stored(row.id)
    assert (stored.status, stored.message, stored.rows_loaded) == ("failed", "rival", None)  # the loser changed nothing
    assert stored.finished_at is not None


def test_a_rival_that_made_the_same_move_first_is_accepted_like_a_retry(data_dir, monkeypatch):
    row = _ingest(_mio())
    real_now = dao_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            assert _update(row.id, status="started", batch_count=3)[0] == SUCCESS
        return real_now()

    monkeypatch.setattr(dao_impl, "_now", now_after_a_rival_wins)
    code, ctx = _update(row.id, status="started", message="mine")
    assert code == SUCCESS
    result = ctx.resp.records[0]
    assert (result.status, result.message, result.batch_count) == ("started", "mine", 3)
    assert result == _stored(row.id)
    assert result.started_at is not None  # the rival's time, set once


def test_an_update_inside_a_rolled_back_transaction_leaves_no_trace(data_dir):
    logs = DaoObjectsFactory.get_mio_ingest_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()
    row = _ingest(_mio())
    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    moved = MioIngestLogCtx(transaction=tx, req=MioIngestLogReq(id=row.id, status="started", rows_loaded=8))
    assert logs.update(moved) == SUCCESS
    assert moved.resp.records[0].status == "started"
    assert transactions.rollback(tx) == SUCCESS
    assert _stored(row.id) == row
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_mio_ingest_log_dao.py -v`
Expected: the Task 2 tests PASS; every new test FAILS with `AttributeError: 'SqlAlchemyMioIngestLogDao' object has no attribute 'update'`.

- [ ] **Step 3: Add `update` to the interface**

Append to the class in `app/core/dao/mio_ingest_log_dao.py` (after `list`):

```python

    @abstractmethod
    def update(self, ctx: MioIngestLogCtx) -> int:
        """Needs req.id. Changes the given status, message, rows_loaded, batch_count and increment_marker; mio_id
        never changes. Status moves follow D30: requested to started or failed, started to completed or failed,
        completed and failed are final, the same status again is accepted and keeps its times. started_at is set on
        the move to started, finished_at on the move to completed or failed. NOT_FOUND if there is no such row,
        INVALID_INPUT for an unknown status or an invalid volume field, CONFLICT for any other move; a CONFLICT
        changes nothing.

        Two callbacks at once: the status write only matches a row that still has the status that was read, so the
        first to commit wins. The second gets CONFLICT, or SUCCESS if the first made the very same move (a retry).

        message and the volume fields are notes, not part of the D30 rules: they may be set on any row, also a
        final one, so a late callback can still fill in the final volume."""
```

- [ ] **Step 4: Implement `update`**

In `app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py`:
- below `from sqlalchemy import select` add `from sqlalchemy import update as sql_update`;
- change the return-codes import to `from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS`;
- append this method to `SqlAlchemyMioIngestLogDao` (after `list`):

```python

    def update(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioIngestLogModel, req.id)
                if row is None:
                    return NOT_FOUND
                current = ExecStatus(row.status)
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT
                notes = _notes_of(req)
                if changes_status:
                    changes = {**notes, "status": target.value}
                    if target == ExecStatus.STARTED:
                        changes["started_at"] = _now()
                    elif target.is_final:
                        changes["finished_at"] = _now()
                    # The write only matches while the row still has the status read above, so when two callbacks
                    # race the second one finds no row to change instead of overwriting the first (D30).
                    moved = session.execute(
                        sql_update(MioIngestLogModel)
                        .where(MioIngestLogModel.id == req.id, MioIngestLogModel.status == current.value)
                        .values(**changes)
                    ).rowcount
                    session.refresh(row)
                    if not moved:
                        if row.status != target.value:
                            return CONFLICT  # a rival moved the row somewhere else first; nothing was changed
                        # A rival made the same move first (a retry): keep its status and times, add only the notes.
                        for name, value in notes.items():
                            setattr(row, name, value)
                else:
                    for name, value in notes.items():
                        setattr(row, name, value)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_ingest_log update failed")
            return FAILURE
```

`req.mio_id` is never read here, which is what keeps `mio_id` unchanged.

- [ ] **Step 5: Run them and see them pass**

Run: `uv run pytest tests/test_mio_ingest_log_dao.py -v && uv run pytest && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 87` with summary `MioIngestLogDao update with the D30 rules and the volume notes` and files `app/core/dao/mio_ingest_log_dao.py app/core/dao/impl/sqlalchemy_mio_ingest_log_dao.py tests/test_mio_ingest_log_dao.py`.

---

### Task 4: the exec-log reference to the ingest row

**Files:**
- Modify: `app/core/common/dtos/app_wf_exec_log_dtos.py`, `app/core/dao/app_wf_exec_log_dao.py`, `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`
- Test: `tests/test_app_wf_exec_log_dao.py`

**Interfaces:**
- Consumes: `AppWfExecLogModel.mios_ingest_log_id` and `MioIngestLogModel` (Task 1); `MioIngestLogDao.create` (Task 2) in the tests.
- Produces: `AppWfExecLogRecord.mios_ingest_log_id: str | None` (last field, no default); `AppWfExecLogReq.mios_ingest_log_id: str | None = None`; `AppWfExecLogDao.create` honours it (NOT_FOUND for an unknown ingest), `list` filters by it, `update` ignores it.

- [ ] **Step 1: Write the failing tests**

In `tests/test_app_wf_exec_log_dao.py` replace the three DTO import lines

```python
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord, AppWfExecLogReq
```

with

```python
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
```

and append at the end of the file (it already has `_ctx`, `_workflow`, `_execute`, `_exec_log_rows`, `_update`, `_stored`, `_list` and `_one_tick_per_call`):

```python


def _ingest_row() -> str:
    """A requested mios_ingest_log row of a new MIO; its id."""
    mio = MioCtx(req=MioReq(name="t_ingest_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    return ingest.resp.records[0].id


def test_an_execution_without_an_ingest_has_a_null_reference(data_dir):
    row = _execute(_workflow().id)
    assert row.mios_ingest_log_id is None
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        assert db.execute("select mios_ingest_log_id from app_workflows_exec_log").fetchall() == [(None,)]


def test_create_stores_the_ingest_reference(data_dir):
    ingest_id = _ingest_row()
    row = _execute(_workflow().id, mios_ingest_log_id=ingest_id)
    assert row.mios_ingest_log_id == ingest_id
    assert _stored(row.id).mios_ingest_log_id == ingest_id


def test_create_with_an_unknown_ingest_is_not_found_and_stores_nothing(data_dir):
    workflow = _workflow()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.create(_ctx(workflow_id=workflow.id, mios_ingest_log_id="no-such-ingest")) == NOT_FOUND
    assert _exec_log_rows(data_dir) == []


def test_several_executions_of_one_ingest_are_listed_by_its_id(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    ingest_id = _ingest_row()
    workflow = _workflow()
    first = _execute(workflow.id, mios_ingest_log_id=ingest_id)
    assert _update(first.id, status="failed", message="batch 1 failed")[0] == SUCCESS
    rerun = _execute(workflow.id, mios_ingest_log_id=ingest_id)  # a rerun after the failure
    batch_2 = _execute(_workflow("load_batch_2").id, mios_ingest_log_id=ingest_id)
    unrelated = _execute(workflow.id)

    assert [r.id for r in _list(mios_ingest_log_id=ingest_id)] == [batch_2.id, rerun.id, first.id]
    assert [r.id for r in _list(mios_ingest_log_id=ingest_id, status="failed")] == [first.id]
    assert [r.id for r in _list(mios_ingest_log_id=ingest_id, workflow_id=workflow.id)] == [rerun.id, first.id]
    assert _list(mios_ingest_log_id="no-such-ingest") == []
    assert unrelated.id in {r.id for r in _list()}  # the filter is optional


def test_update_leaves_the_ingest_reference_alone(data_dir):
    ingest_id = _ingest_row()
    row = _execute(_workflow().id, mios_ingest_log_id=ingest_id)
    code, ctx = _update(row.id, status="started", mios_ingest_log_id="something-else")
    assert code == SUCCESS
    assert ctx.resp.records[0].mios_ingest_log_id == ingest_id
    assert _update(row.id, status="completed")[0] == SUCCESS
    assert _stored(row.id).mios_ingest_log_id == ingest_id
    plain = _execute(_workflow("plain").id)
    assert _update(plain.id, mios_ingest_log_id=ingest_id)[0] == SUCCESS
    assert _stored(plain.id).mios_ingest_log_id is None


def test_create_reads_the_ingest_inside_the_same_shared_transaction(data_dir):
    workflow = _workflow()
    transactions = DaoObjectsFactory.get_transaction_dao()
    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    mio = MioCtx(transaction=tx, req=MioReq(name="t_tx_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    ingest = MioIngestLogCtx(transaction=tx, req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS  # not committed: only tx sees it
    execution = AppWfExecLogCtx(
        transaction=tx, req=AppWfExecLogReq(workflow_id=workflow.id, mios_ingest_log_id=ingest.resp.records[0].id)
    )
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS
    assert transactions.rollback(tx) == SUCCESS
    assert _list() == []
    outside = _ctx(workflow_id=workflow.id, mios_ingest_log_id=ingest.resp.records[0].id)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(outside) == NOT_FOUND  # the ingest was rolled back
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py -v`
Expected: the old tests PASS; the six new tests FAIL with `TypeError: AppWfExecLogReq.__init__() got an unexpected keyword argument 'mios_ingest_log_id'` or `AttributeError: 'AppWfExecLogRecord' object has no attribute 'mios_ingest_log_id'`.

- [ ] **Step 3: Extend the DTOs**

In `app/core/common/dtos/app_wf_exec_log_dtos.py`:
- in `AppWfExecLogRecord` add as the last field, after `finished_at: datetime | None`:

```python
    mios_ingest_log_id: str | None
```

- in `AppWfExecLogReq` replace the docstring with

```python
    """A field left as None means "not given". id identifies one row. workflow_id is what create needs and list
    filters on; mios_ingest_log_id is optional on create and a list filter; engine_type and status are list filters;
    status, engine_run_id and message are what update changes."""
```

  and add `mios_ingest_log_id: str | None = None` directly after `message: str | None = None` (before `limit`).

- [ ] **Step 4: Extend the interface docstrings**

In `app/core/dao/app_wf_exec_log_dao.py`:
- replace the `create` docstring with

```python
        """Needs req.workflow_id. Reads that workflow from app_workflows in the same transaction and copies its
        name, engine type, engine workflow id and config (as config_used) into a new row with the status
        "requested". The new row is returned. INVALID_INPUT without a workflow_id, NOT_FOUND if there is no such
        workflow. Does not look at the workflow's enabled flag.

        Optional req.mios_ingest_log_id: the MIO ingest this execution belongs to (many executions to one ingest,
        D50). When given, that mios_ingest_log row must exist (read in the same transaction), otherwise NOT_FOUND.
        It is stored as given and never changes afterwards. Left out, it stays NULL (a workflow without a MIO)."""
```

- in the `update` docstring change `CONFLICT changes nothing.` to `CONFLICT changes nothing. mios_ingest_log_id is never changed.`;
- replace the first line of the `list` docstring, `"""Optional filters: req.workflow_id, req.status, req.engine_type; optional req.limit and req.offset.`, with the two lines

```python
        """Optional filters: req.workflow_id, req.status, req.engine_type, req.mios_ingest_log_id; optional req.limit
        and req.offset.
```

  (the rest of that docstring stays).

- [ ] **Step 5: Implement the reference**

In `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`:
- change the models import to `from app.core.dao.impl.models import AppWfExecLogModel, AppWfModel, MioIngestLogModel`;
- in `_to_record`, add `mios_ingest_log_id=row.mios_ingest_log_id,` directly after `message=row.message,`;
- replace the whole `create` method with:

```python
    def create(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if not req.workflow_id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                workflow = session.get(AppWfModel, req.workflow_id)
                if workflow is None:
                    return NOT_FOUND
                # No foreign key (D58): the ingest row must exist now; the reference never changes afterwards.
                ingest_id = req.mios_ingest_log_id
                if ingest_id is not None and session.get(MioIngestLogModel, ingest_id) is None:
                    return NOT_FOUND
                row = _new_row(workflow)
                row.mios_ingest_log_id = ingest_id
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log create failed")
            return FAILURE
```

- in `list`, directly after the `if req.engine_type:` filter (two lines), add:

```python
            if req.mios_ingest_log_id:
                query = query.where(AppWfExecLogModel.mios_ingest_log_id == req.mios_ingest_log_id)
```

`update` is not changed: it never reads `req.mios_ingest_log_id`, so the reference stays as created.

- [ ] **Step 6: Run them and see them pass**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py -v && uv run pytest && uv run lint-imports`
Expected: all PASS (the existing equality checks such as `assert gone.resp.records[0] == old` still hold, both sides carry `mios_ingest_log_id=None`); `Contracts: 7 kept, 0 broken.`

- [ ] **Step 7: Commit**

Run `/ccaa-commit-push 87` with summary `exec log references its MIO ingest row` and files `app/core/common/dtos/app_wf_exec_log_dtos.py app/core/dao/app_wf_exec_log_dao.py app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py tests/test_app_wf_exec_log_dao.py`.

---

### Task 5: the flow test, Postgres, and the design note

**Files:**
- Create: `tests/test_mio_ingest_flow.py`
- Modify: `tests/test_postgres.py`, `DESIGN.md`

**Interfaces:**
- Consumes: `MioIngestLogDao`, `AppWfExecLogDao`, `AppWfDao`, `MioDao` through `DaoObjectsFactory`; the seeded MIO `Customer complaints 3 months 2026` (#86).

- [ ] **Step 1: Write the tests**

Create `tests/test_mio_ingest_flow.py`:

```python
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import CONFLICT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def test_one_ingest_of_a_seeded_mio_served_by_several_executions(data_dir):
    ingests = DaoObjectsFactory.get_mio_ingest_log_dao()
    executions = DaoObjectsFactory.get_app_wf_exec_log_dao()
    mio = MioCtx(req=MioReq(name="Customer complaints 3 months 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_ingest", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS
    workflow_id = workflow.resp.records[0].id

    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, batch_count=2))
    assert ingests.create(ingest) == SUCCESS
    ingest_id = ingest.resp.records[0].id
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="started"))) == SUCCESS

    def execute():
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=ingest_id))
        assert executions.create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    def move(exec_id, status):
        return executions.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=exec_id, status=status)))

    first = execute()
    assert move(first, "started") == SUCCESS and move(first, "failed") == SUCCESS
    rerun = execute()
    assert move(rerun, "started") == SUCCESS and move(rerun, "completed") == SUCCESS

    # The caller decides the ingest's status (D58); the DAO does not derive it from the executions.
    still = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert ingests.get(still) == SUCCESS and still.resp.records[0].status == "started"
    done = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="completed", rows_loaded=1500))
    assert ingests.update(done) == SUCCESS
    late = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="failed"))
    assert ingests.update(late) == CONFLICT

    served = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=ingest_id))
    assert executions.list(served) == SUCCESS
    assert sorted((r.id, r.status) for r in served.resp.records) == sorted([(first, "failed"), (rerun, "completed")])
    of_mio = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id))
    assert ingests.list(of_mio) == SUCCESS
    assert [(r.id, r.status, r.rows_loaded, r.batch_count) for r in of_mio.resp.records] == [
        (ingest_id, "completed", 1500, 2)
    ]
```

(The nested `execute()` and `move(exec_id, status)` live in a test file, which `tests/test_ctx_only_signatures.py` does not scan; the existing tests use the same style of helpers.)

In `tests/test_postgres.py` add `from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq` directly below `from app.core.common.dtos.mio_dtos import MioCtx, MioReq`, and `from app.core.dao.impl import sqlalchemy_mio_ingest_log_dao as ingest_log_impl` directly below `from app.core.dao.impl import sqlalchemy_app_wf_exec_log_dao as exec_log_impl`. Then append:

```python


def test_mio_ingest_log_works_on_postgres(postgres, monkeypatch):
    command.upgrade(postgres, "head")
    assert "mios_ingest_log" in _admin_tables()
    ingests = DaoObjectsFactory.get_mio_ingest_log_dao()
    executions = DaoObjectsFactory.get_app_wf_exec_log_dao()
    mio = MioCtx(req=MioReq(name="t_ingest_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    created = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, rows_loaded=5_000_000_000, increment_marker="m"))
    assert ingests.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.status == "requested" and row.requested_at.tzinfo is not None
    assert row.rows_loaded == 5_000_000_000  # BigInteger: above the 32-bit range
    assert ingests.create(MioIngestLogCtx(req=MioIngestLogReq(mio_id="no-such-mio"))) == NOT_FOUND
    assert ingests.create(MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, batch_count=-1))) == INVALID_INPUT
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="completed"))) == CONFLICT
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="started"))) == SUCCESS

    # Postgres runs at READ COMMITTED: a rival that commits between update's read and its write must win cleanly.
    real_now = ingest_log_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            rival = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="failed", message="rival"))
            assert ingests.update(rival) == SUCCESS
        return real_now()

    monkeypatch.setattr(ingest_log_impl, "_now", now_after_a_rival_wins)
    loser = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="completed", message="loser"))
    assert ingests.update(loser) == CONFLICT
    monkeypatch.setattr(ingest_log_impl, "_now", real_now)
    stored = MioIngestLogCtx(req=MioIngestLogReq(id=row.id))
    assert ingests.get(stored) == SUCCESS
    assert (stored.resp.records[0].status, stored.resp.records[0].message) == ("failed", "rival")
    late = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, batch_count=3))  # a note on a final row
    assert ingests.update(late) == SUCCESS and late.resp.records[0].batch_count == 3
    listed = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, status="failed"))
    assert ingests.list(listed) == SUCCESS and [r.id for r in listed.resp.records] == [row.id]

    made = AppWfCtx(req=AppWfReq(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    workflow_id = made.resp.records[0].id
    ids = []
    for _ in range(2):
        execution = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=row.id))
        assert executions.create(execution) == SUCCESS
        ids.append(execution.resp.records[0].id)
    unknown = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id="no-such-ingest"))
    assert executions.create(unknown) == NOT_FOUND
    served = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=row.id))
    assert executions.list(served) == SUCCESS and sorted(r.id for r in served.resp.records) == sorted(ids)

    def exec_log_columns():
        engine = create_engine(URL)
        try:
            return {c["name"] for c in inspect(engine).get_columns("app_workflows_exec_log", schema=SCHEMA_ADMIN)}
        finally:
            engine.dispose()

    command.downgrade(postgres, "0006")
    assert "mios_ingest_log" not in _admin_tables()
    assert "mios_ingest_log_id" not in exec_log_columns()
    command.upgrade(postgres, "head")
    assert "mios_ingest_log" in _admin_tables()
    assert "mios_ingest_log_id" in exec_log_columns()
```

- [ ] **Step 2: Run the SQLite tests**

Run: `uv run pytest tests/test_mio_ingest_flow.py tests/test_postgres.py -v`
Expected: the flow test PASSES (the implementation exists; it locks the behavior); every test in `tests/test_postgres.py` is SKIPPED (`CCA_TEST_POSTGRES_URL is not set`).

- [ ] **Step 3: Run the whole suite on a real Postgres**

Run, from the app root:

```bash
docker run -d --name cca-pg-0037 -e POSTGRES_PASSWORD=postgres -p 55434:5432 postgres:16
sleep 6
CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55434/postgres uv run pytest -v
docker rm -f cca-pg-0037
```

Expected: the whole suite passes with the Postgres tests no longer skipped (`test_app_wf_exec_log_dao_works_on_postgres` and `test_catalog_works_on_postgres` now also run the `0007` downgrade, because they downgrade below it). If the first `pytest` fails with a connection error, Postgres was not ready: wait a few seconds and run the `pytest` line again. Always run the `docker rm -f cca-pg-0037` line, also after a failure. If `docker` is not available, say so in the report and rely on CI's Postgres service.

- [ ] **Step 4: Mark the ingest log as built in the design**

In `DESIGN.md`, in the section `#### app_workflows_exec_log (every execution of every workflow, D50)`, replace the last sentence of the paragraph that starts `Built in story #82 (migration \`0004\`)`, which is `The optional reference to the MIO ingest row comes with #87.`, with:

```
Story #87 (migration `0007`) added the optional `mios_ingest_log_id`: set on create (the ingest row must exist), never changed, and a filter of `list` (D58).
```

In the section `#### The catalog (D49)`, directly after the bullet that starts `- **Built (story #86, M02-0036):**`, add the bullet:

```
- **Built (story #87, M02-0037):** `mios_ingest_log` and the column `app_workflows_exec_log.mios_ingest_log_id` (migration `0007`), and `MioIngestLogDao` (create, get, list, update; no delete) with the D30 moves of `ExecStatus` and the volume notes `rows_loaded`, `batch_count` and `increment_marker` (D58). No endpoint reads them yet, and nothing derives an ingest's status from its executions.
```

- [ ] **Step 5: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; all tests PASS (Postgres tests skipped without the variable).

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 87` with summary `ingest flow test, Postgres test and design note` and files `tests/test_mio_ingest_flow.py tests/test_postgres.py DESIGN.md`.

---

## Self-Review (done)

1. **Spec coverage:** table, columns, types and the `(mio_id, status)` index, no foreign key (Task 1); the exec-log column and index in the same migration with batch mode, downgrade drops both, `0007` up/down/up with an existing exec-log row kept (Task 1); naming (all tasks, per Global Constraints); `create` with `requested`, MIO check, INVALID_INPUT for missing `mio_id` and each invalid volume case (bool, negative, float, string, long or non-string marker), `get`, `list` with filters, newest-first order, paging, negative paging and unknown status (Task 2); every legal and illegal move, a repeated status, `started_at`/`finished_at`, notes and volume on a final row, `mio_id` unchanged, the stale second update, the rival callback (both a different and the same move), a shared transaction with rollback (Task 3, plus the create-side transaction test in Task 2); the exec-log reference stored, NOT_FOUND for an unknown ingest, NULL by default, the list filter, several executions to one ingest, `update` leaves it alone (Task 4); singleton and factory (Task 2); Postgres including the rival and the column downgrade, and the flow from a seeded MIO (Task 5); no delete anywhere; nothing derives an ingest's status (the flow test asserts the ingest stays `started` until the caller moves it).
2. **Placeholders:** none; every code step shows its full code, and every modification names the exact line it goes after or replaces.
3. **Types and names:** `MioIngestLogCtx/Req/Resp/Record`, `MioIngestLogModel`, `SqlAlchemyMioIngestLogDao`, `get_mio_ingest_log_dao`, `_now`, `_has_invalid_volume`, `_notes_of`, `NOTE_FIELDS`, `MARKER_MAX`, `mios_ingest_log_id`, `ix_mios_ingest_log_mio_status`, `ix_app_wf_exec_log_mios_ingest_log_id` are spelled the same in every task. Every helper in `app` and `alembic` takes one object (`req`, `row` or `workflow`), so `tests/test_ctx_only_signatures.py` stays green; no `list[...]` annotation appears in a DAO class body.
4. **Pre-check:** the code in Tasks 1 to 5 was run once in a scratch copy of the app root (outside git): full SQLite suite green (257 passed), `lint-imports` 7 kept, `0007` down/up on SQLite with batch mode working on the attached admin schema. The Postgres run of Task 5 step 3 was **not** run while writing the plan; it is the first real check of batch mode and the `BigInteger` on Postgres.
5. **Accepted gaps (from the spec, not covered):** `MioDao.delete` does not check for `mios_ingest_log` rows, so a MIO with ingests can be deleted (no foreign key; the log keeps the dangling `mio_id`, like the exec log keeps a deleted workflow's id). A `rows_loaded` above the 64-bit range or a `batch_count` above the 32-bit range is accepted by the DAO and fails in Postgres (FAILURE); SQLite stores it. `message` is not type-checked, as in the exec log.
