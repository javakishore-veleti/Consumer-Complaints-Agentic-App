# M02-0032 (#82) `app_workflows_exec_log` table with its DAO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `app_workflows_exec_log` table in the admin schema and one DAO (`AppWfExecLogDao`) with create, get, list and update, where `create` copies the workflow's details so the row keeps them as they were at execution time.

**Architecture:** Follow the `app_workflows` pattern from #81: one SQLAlchemy model in `dao/impl/models.py`, one Alembic migration, one DAO interface in `dao/`, its SQLAlchemy implementation in `dao/impl/`, the singleton handed out by `dao/objects_factory.py`. Every method takes one ctx and returns an integer code. The status rules (D30) live in an `ExecStatus` enum in `app_types_constants.py`.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, pytest, `uv`; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0032-app-wf-exec-log-design.md`. Decisions: D30, D43, D50, D55, D56 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there unless it says the repository root. All paths below are relative to it.
- Table name exactly `app_workflows_exec_log`, in schema `consumer_comp_admin_db` (`SCHEMA_ADMIN`); migration `0004`, revising `0003`.
- In **class names** `Workflows` is `Wf`: `AppWfExecLogModel`, `AppWfExecLogDao`, `AppWfExecLogCtx`, `AppWfExecLogReq`, `AppWfExecLogResp`, `AppWfExecLogRecord`, `SqlAlchemyAppWfExecLogDao`; module names follow the class names (D55).
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`... (D37, enforced by `tests/test_ctx_only_signatures.py`, which scans `app`, `alembic`, `scripts` and `main.py` and skips `self` and `cls`).
- Every method that takes a ctx returns an integer from `app/core/common/return_codes.py`: `SUCCESS 0`, `FAILURE 1`, `NOT_FOUND 2`, `INVALID_INPUT 3`, `CONFLICT 4`.
- `workflow_id` is a plain indexed `String(36)` column with **no foreign key** (D56). `config_used` is a nullable JSON column; nothing means NULL, never `{}` (D55).
- Status moves (D30): new rows are `requested`; `requested` goes to `started` or `failed`; `started` goes to `completed` or `failed`; `completed` and `failed` are final; the same status again is accepted and changes nothing; any other move is `CONFLICT`. The check and the write happen in one DAO transaction.
- The log is append-only: no `delete` method. The snapshot columns (`workflow_name`, `engine_type`, `engine_workflow_id`, `config_used`) are never changed after `create`.
- Migrations use Alembic Python ops, never raw SQL (D23), and work on SQLite and Postgres (D33).
- Only `dao/impl` imports SQLAlchemy; only `dao/objects_factory.py` imports `dao/impl` (`npm run local:api:lint`).
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35).
- Commit with `/ccaa-commit-push 82` (it checks lint and tests, writes the `M02-0032 #82: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/app_types_constants.py` (modify) | `ExecStatus` and its allowed moves |
| `alembic/versions/0004_create_admin_app_workflows_exec_log.py` (create) | the table and its index |
| `app/core/dao/impl/models.py` (modify) | `AppWfExecLogModel` |
| `app/core/common/dtos/app_wf_exec_log_dtos.py` (create) | `AppWfExecLogRecord`, `AppWfExecLogReq`, `AppWfExecLogResp`, `AppWfExecLogCtx` |
| `app/core/dao/app_wf_exec_log_dao.py` (create) | `AppWfExecLogDao` interface |
| `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py` (create) | the implementation |
| `app/core/dao/objects_factory.py` (modify) | `get_app_wf_exec_log_dao()` |
| `tests/test_app_types_constants.py`, `tests/test_app_wf_exec_log_dao.py` (create / modify) | tests |
| `tests/test_schema.py`, `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | tests |
| `DESIGN.md` (modify) | marks the exec-log table as built in #82 |

---

### Task 1: `ExecStatus` and its allowed moves

**Files:**
- Modify: `app/core/common/app_types_constants.py`
- Test: `tests/test_app_types_constants.py`

**Interfaces:**
- Consumes: `AppTypeEnum` (already in the file).
- Produces: `ExecStatus` with members `REQUESTED`, `STARTED`, `COMPLETED`, `FAILED` (string values `"requested"`, `"started"`, `"completed"`, `"failed"`), `ExecStatus.values() -> list[str]`, property `next_statuses -> tuple[ExecStatus, ...]`, property `is_final -> bool`.

- [ ] **Step 1: Write the failing tests** (replace the import line at the top of `tests/test_app_types_constants.py` and append the new tests)

```python
from app.core.common.app_types_constants import AppTypeEnum, EngineType, ExecStatus
```

Append at the end of the file:

```python


def test_exec_status_values_in_the_order_of_a_normal_run():
    assert ExecStatus.values() == ["requested", "started", "completed", "failed"]
    assert ExecStatus.STARTED == "started"
    assert issubclass(ExecStatus, AppTypeEnum)


def test_exec_status_allowed_moves_follow_d30():
    assert ExecStatus.REQUESTED.next_statuses == (ExecStatus.STARTED, ExecStatus.FAILED)
    assert ExecStatus.STARTED.next_statuses == (ExecStatus.COMPLETED, ExecStatus.FAILED)
    assert ExecStatus.COMPLETED.next_statuses == ()
    assert ExecStatus.FAILED.next_statuses == ()


def test_only_completed_and_failed_are_final():
    assert [s for s in ExecStatus if s.is_final] == [ExecStatus.COMPLETED, ExecStatus.FAILED]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_types_constants.py -v`
Expected: collection error `ImportError: cannot import name 'ExecStatus'`.

- [ ] **Step 3: Write the implementation** (append to `app/core/common/app_types_constants.py`)

```python


class ExecStatus(AppTypeEnum):
    """The status of one workflow execution (D30). A new execution is REQUESTED."""

    REQUESTED = "requested"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def next_statuses(self) -> tuple["ExecStatus", ...]:
        """The statuses this one may move to. The same status again is also accepted by the DAO (retries)."""
        return _EXEC_STATUS_MOVES[self]

    @property
    def is_final(self) -> bool:
        return not self.next_statuses


_EXEC_STATUS_MOVES = {
    ExecStatus.REQUESTED: (ExecStatus.STARTED, ExecStatus.FAILED),
    ExecStatus.STARTED: (ExecStatus.COMPLETED, ExecStatus.FAILED),
    ExecStatus.COMPLETED: (),
    ExecStatus.FAILED: (),
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_types_constants.py tests/test_ctx_only_signatures.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 82` with the summary `ExecStatus with the D30 status moves`.

---

### Task 2: The table, its model and migration `0004`

**Files:**
- Create: `alembic/versions/0004_create_admin_app_workflows_exec_log.py`
- Modify: `app/core/dao/impl/models.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: `SCHEMA_ADMIN`; revision `0003`.
- Produces: table `consumer_comp_admin_db.app_workflows_exec_log`; model `AppWfExecLogModel` with attributes `id`, `workflow_id`, `workflow_name`, `engine_type`, `engine_workflow_id`, `config_used`, `engine_run_id`, `status`, `message`, `requested_at`, `started_at`, `finished_at`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_schema.py`; `_admin_db`, `Config`, `command` and `PROJECT_ROOT` are already there)

```python


def test_app_workflows_exec_log_table_is_in_the_admin_schema_with_the_expected_columns(data_dir):
    with _admin_db(data_dir) as db:
        columns = {
            r[1]: (r[2], r[3]) for r in db.execute("pragma table_info(app_workflows_exec_log)")
        }  # name: (type, not null)
        indexes = {r[1] for r in db.execute("pragma index_list(app_workflows_exec_log)")}
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
    }
    assert columns["id"] == ("VARCHAR(36)", 1)
    assert columns["workflow_id"] == ("VARCHAR(36)", 1)
    assert columns["workflow_name"] == ("VARCHAR(100)", 1)
    assert columns["engine_type"] == ("VARCHAR(32)", 1)
    assert columns["engine_workflow_id"] == ("VARCHAR(255)", 1)
    assert columns["config_used"][1] == 0  # nullable: nothing is stored as NULL, never {}
    assert columns["engine_run_id"] == ("VARCHAR(128)", 0)
    assert columns["status"] == ("VARCHAR(32)", 1)
    assert columns["message"][1] == 0
    assert columns["requested_at"][1] == 1
    assert columns["started_at"][1] == 0 and columns["finished_at"][1] == 0
    assert "ix_app_wf_exec_log_workflow_status" in indexes


def test_exec_log_has_no_foreign_key_to_the_workflow_registry(data_dir):
    with _admin_db(data_dir) as db:
        assert db.execute("pragma foreign_key_list(app_workflows_exec_log)").fetchall() == []


def test_migration_0004_runs_down_and_up(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0003")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'app_workflows_exec_log'").fetchall() == []
        assert db.execute("select name from sqlite_master where name = 'app_workflows'").fetchall() != []
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'app_workflows_exec_log'").fetchall() != []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schema.py -v`
Expected: the three new tests FAIL because the table does not exist yet: `pragma table_info` returns no columns so the set comparison fails, `pragma foreign_key_list` still returns `[]` (that one may already pass, it only guards the later model), and the down-and-up test fails on its last assertion because `0003` is still the head, so `upgrade head` does not create the table.

- [ ] **Step 3: Write the model** (append to `app/core/dao/impl/models.py`)

```python


class AppWfExecLogModel(Base):
    __tablename__ = "app_workflows_exec_log"
    __table_args__ = (
        Index("ix_app_wf_exec_log_workflow_status", "workflow_id", "status"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D56): the log must survive a rename or delete of the workflow.
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # The next four are copied from app_workflows when the execution is requested and never change.
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    engine_type: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config_used: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    engine_run_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 4: Write the migration** (`alembic/versions/0004_create_admin_app_workflows_exec_log.py`)

```python
"""create app_workflows_exec_log in the admin schema (every execution of every workflow)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "app_workflows_exec_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),  # no foreign key on purpose (D56)
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("engine_type", sa.String(32), nullable=False),
        sa.Column("engine_workflow_id", sa.String(255), nullable=False),
        sa.Column("config_used", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("engine_run_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_app_wf_exec_log_workflow_status",
        "app_workflows_exec_log",
        ["workflow_id", "status"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_app_wf_exec_log_workflow_status", table_name="app_workflows_exec_log", schema=SCHEMA)
    op.drop_table("app_workflows_exec_log", schema=SCHEMA)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_schema.py tests/test_ctx_only_signatures.py -v`
Expected: all PASS (including the existing `test_migration_0003_runs_down_and_up`, which now also passes through 0004).

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 82` with the summary `app_workflows_exec_log table, model and migration 0004`.

---

### Task 3: DTOs, interface, `create` and `get`, and the factory

**Files:**
- Create: `app/core/common/dtos/app_wf_exec_log_dtos.py`, `app/core/dao/app_wf_exec_log_dao.py`, `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`
- Modify: `app/core/dao/objects_factory.py`
- Test: `tests/test_app_wf_exec_log_dao.py` (create), `tests/test_singletons.py` (modify)

**Interfaces:**
- Consumes: `AppWfModel`, `AppWfExecLogModel`, `ExecStatus`, `TransactionalCtx`, `unit_of_work(ctx)`, return codes, `AppWfDao` (tests only).
- Produces:
  - `AppWfExecLogRecord(id, workflow_id, workflow_name, engine_type, engine_workflow_id, config_used, engine_run_id, status, message, requested_at, started_at, finished_at)`
  - `AppWfExecLogReq(id, workflow_id, engine_type, status, engine_run_id, message, limit, offset)`, all default `None`
  - `AppWfExecLogResp(records)`, `AppWfExecLogCtx(transaction, req, resp)`
  - `AppWfExecLogDao` with abstract `create(ctx) -> int` and `get(ctx) -> int` (Tasks 4 and 5 add `update` and `list`)
  - `SqlAlchemyAppWfExecLogDao`; module helpers `_now()`, `_to_record(row)`, `_new_row(workflow)`
  - `DaoObjectsFactory.get_app_wf_exec_log_dao() -> AppWfExecLogDao`

- [ ] **Step 1: Write the failing tests** (`tests/test_app_wf_exec_log_dao.py`)

```python
import sqlite3

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord, AppWfExecLogReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

CONFIG = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "dry_run": False, "limit": None}


def _ctx(**fields) -> AppWfExecLogCtx:
    return AppWfExecLogCtx(req=AppWfExecLogReq(**fields))


def _workflow(name="download_3_months", engine_type="apache_airflow", engine_workflow_id="download_dag", **more) -> AppWfRecord:
    ctx = AppWfCtx(
        req=AppWfReq(workflow_name=name, engine_type=engine_type, engine_workflow_id=engine_workflow_id, **more)
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _execute(workflow_id: str, **more) -> AppWfExecLogRecord:
    ctx = _ctx(workflow_id=workflow_id, **more)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0]


def _exec_log_rows(data_dir) -> list[tuple]:
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        return db.execute("select id, config_used from app_workflows_exec_log").fetchall()


def test_create_copies_the_workflow_and_starts_as_requested(data_dir):
    workflow = _workflow(config=CONFIG)
    row = _execute(workflow.id)
    assert len(row.id) == 36
    assert row.workflow_id == workflow.id
    assert (row.workflow_name, row.engine_type, row.engine_workflow_id) == (
        "download_3_months",
        "apache_airflow",
        "download_dag",
    )
    assert row.config_used == CONFIG
    assert row.status == "requested"
    assert (row.engine_run_id, row.message, row.started_at, row.finished_at) == (None, None, None, None)
    assert row.requested_at.tzinfo is not None


def test_a_workflow_without_config_gives_a_null_config_used(data_dir):
    row = _execute(_workflow().id)
    assert row.config_used is None
    assert [r[1] for r in _exec_log_rows(data_dir)] == [None]  # SQL NULL, not "null" and not {}


def test_create_always_starts_as_requested_whatever_the_request_says(data_dir):
    assert _execute(_workflow().id, status="completed").status == "requested"


def test_create_accepts_a_disabled_workflow(data_dir):
    # Whether a disabled workflow may start is policy for the start endpoint (#42), not the DAO.
    assert _execute(_workflow(enabled=False).id).status == "requested"


def test_create_without_a_workflow_id_is_invalid_input(data_dir):
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(_ctx()) == INVALID_INPUT
    assert _exec_log_rows(data_dir) == []


def test_create_for_an_unknown_workflow_is_not_found_and_stores_nothing(data_dir):
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(_ctx(workflow_id="no-such-workflow")) == NOT_FOUND
    assert _exec_log_rows(data_dir) == []


def test_the_row_keeps_the_old_details_after_the_workflow_is_renamed_or_deleted(data_dir):
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    workflow = _workflow(config=CONFIG)
    first = _execute(workflow.id)

    renamed = AppWfCtx(
        req=AppWfReq(
            id=workflow.id, workflow_name="renamed", engine_workflow_id="other_dag", config={"retries": 9}
        )
    )
    assert workflows.update(renamed) == SUCCESS
    again = _ctx(id=first.id)
    assert logs.get(again) == SUCCESS
    old = again.resp.records[0]
    assert (old.workflow_name, old.engine_workflow_id, old.config_used) == ("download_3_months", "download_dag", CONFIG)

    second = _execute(workflow.id)  # an execution after the change sees the new details
    assert (second.workflow_name, second.engine_workflow_id, second.config_used) == (
        "renamed",
        "other_dag",
        {"retries": 9},
    )

    assert workflows.delete(AppWfCtx(req=AppWfReq(id=workflow.id))) == SUCCESS
    gone = _ctx(id=first.id)
    assert logs.get(gone) == SUCCESS
    assert gone.resp.records[0] == old
    assert gone.resp.records[0].workflow_id == workflow.id  # the id stays even though the workflow is gone


def test_get_returns_the_row_by_id(data_dir):
    row = _execute(_workflow().id)
    fetched = _ctx(id=row.id)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(fetched) == SUCCESS
    assert fetched.resp.records == [row]


def test_get_without_an_id_is_invalid_input_and_an_unknown_id_is_not_found(data_dir):
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.get(_ctx()) == INVALID_INPUT
    assert logs.get(_ctx(id="no-such-row")) == NOT_FOUND
```

Append to `tests/test_singletons.py`: add these two imports with the other imports at the top of the file,

```python
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import SqlAlchemyAppWfExecLogDao
```

add this line to the `for getter, interface in (...)` tuple in `test_factories_return_the_same_object_typed_as_the_interface`, after the `get_app_wf_dao` line,

```python
        (DaoObjectsFactory.get_app_wf_exec_log_dao, AppWfExecLogDao),
```

and this line to `test_the_classes_themselves_are_singletons`, after the `SqlAlchemyAppWfDao` line,

```python
    assert SqlAlchemyAppWfExecLogDao() is SqlAlchemyAppWfExecLogDao()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py tests/test_singletons.py -v`
Expected: collection errors `ModuleNotFoundError: No module named 'app.core.common.dtos.app_wf_exec_log_dtos'`.

- [ ] **Step 3: Write the DTOs** (`app/core/common/dtos/app_wf_exec_log_dtos.py`)

```python
"""Ctx, Req and Resp for the app_workflows_exec_log table (every execution of every workflow, DESIGN.md D50)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class AppWfExecLogRecord:
    id: str
    workflow_id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    config_used: dict | None
    engine_run_id: str | None
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


@dataclass
class AppWfExecLogReq:
    """A field left as None means "not given". id identifies one row. workflow_id is what create needs and list
    filters on; engine_type and status are list filters; status, engine_run_id and message are what update changes."""

    id: str | None = None
    workflow_id: str | None = None
    engine_type: str | None = None
    status: str | None = None
    engine_run_id: str | None = None
    message: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class AppWfExecLogResp:
    records: list[AppWfExecLogRecord] = field(default_factory=list)


@dataclass
class AppWfExecLogCtx(TransactionalCtx):
    req: AppWfExecLogReq = field(default_factory=AppWfExecLogReq)
    resp: AppWfExecLogResp = field(default_factory=AppWfExecLogResp)
```

- [ ] **Step 4: Write the interface** (`app/core/dao/app_wf_exec_log_dao.py`)

```python
"""Interface of the DAO for the app_workflows_exec_log table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx
from app.core.common.singleton import SingletonMeta


class AppWfExecLogDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one AppWfExecLogCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    The log is append-only: there is no delete. A row keeps the workflow's name, engine type, engine workflow id and
    config as they were when the execution was requested (DESIGN.md D56)."""

    @abstractmethod
    def create(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.workflow_id. Reads that workflow from app_workflows in the same transaction and copies its
        name, engine type, engine workflow id and config (as config_used) into a new row with the status
        "requested". The new row is returned. INVALID_INPUT without a workflow_id, NOT_FOUND if there is no such
        workflow. Does not look at the workflow's enabled flag."""

    @abstractmethod
    def get(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""
```

- [ ] **Step 5: Write the implementation** (`app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`)

```python
"""AppWfExecLogDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogRecord
from app.core.common.return_codes import FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
from app.core.dao.impl.models import AppWfExecLogModel, AppWfModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(row: AppWfExecLogModel) -> AppWfExecLogRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    times = {name: getattr(row, name) for name in ("requested_at", "started_at", "finished_at")}
    times = {
        name: value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
        for name, value in times.items()
    }
    return AppWfExecLogRecord(
        id=row.id,
        workflow_id=row.workflow_id,
        workflow_name=row.workflow_name,
        engine_type=row.engine_type,
        engine_workflow_id=row.engine_workflow_id,
        config_used=row.config_used,
        engine_run_id=row.engine_run_id,
        status=row.status,
        message=row.message,
        **times,
    )


def _new_row(workflow: AppWfModel) -> AppWfExecLogModel:
    """A requested execution that keeps the workflow's details as they are now (D56)."""
    return AppWfExecLogModel(
        id=str(uuid4()),
        workflow_id=workflow.id,
        workflow_name=workflow.workflow_name,
        engine_type=workflow.engine_type,
        engine_workflow_id=workflow.engine_workflow_id,
        config_used=deepcopy(workflow.config),  # a copy, so a later edit of the workflow cannot reach this row
        status=ExecStatus.REQUESTED.value,
        requested_at=_now(),
    )


class SqlAlchemyAppWfExecLogDao(AppWfExecLogDao):
    def create(self, ctx: AppWfExecLogCtx) -> int:
        if not ctx.req.workflow_id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                workflow = session.get(AppWfModel, ctx.req.workflow_id)
                if workflow is None:
                    return NOT_FOUND
                row = _new_row(workflow)
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log create failed")
            return FAILURE

    def get(self, ctx: AppWfExecLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfExecLogModel, ctx.req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log get failed")
            return FAILURE
```

- [ ] **Step 6: Register the factory method** (in `app/core/dao/objects_factory.py`: add the import after the `AppWfDao` import, and the method after `get_app_wf_dao`)

```python
from app.core.dao.app_wf_exec_log_dao import AppWfExecLogDao
```

```python
    @staticmethod
    def get_app_wf_exec_log_dao() -> AppWfExecLogDao:
        from app.core.dao.impl.sqlalchemy_app_wf_exec_log_dao import SqlAlchemyAppWfExecLogDao

        return SqlAlchemyAppWfExecLogDao()

```

- [ ] **Step 7: Run the tests and the lint to verify they pass**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py tests/test_singletons.py tests/test_ctx_only_signatures.py -v` then `uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 82` with the summary `AppWfExecLogDao create and get with the workflow snapshot`.

---

### Task 4: `update` with the D30 status rules

**Files:**
- Modify: `app/core/dao/app_wf_exec_log_dao.py`, `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`
- Test: `tests/test_app_wf_exec_log_dao.py`

**Interfaces:**
- Consumes: everything from Task 3, `ExecStatus.next_statuses`, `ExecStatus.is_final`.
- Produces: `AppWfExecLogDao.update(ctx) -> int`; module constant `RUN_ID_MAX = 128`.

- [ ] **Step 1: Write the failing tests** (add `import pytest` as the first import of `tests/test_app_wf_exec_log_dao.py`, add `CONFLICT` to the return-codes import, and append)

```python


def _update(row_id: str, **fields) -> tuple[int, AppWfExecLogCtx]:
    ctx = _ctx(id=row_id, **fields)
    return DaoObjectsFactory.get_app_wf_exec_log_dao().update(ctx), ctx


def _stored(row_id: str) -> AppWfExecLogRecord:
    ctx = _ctx(id=row_id)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def test_requested_to_started_sets_started_at_run_id_and_message(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, status="started", engine_run_id="manual__2026-11-14", message="picked up")
    assert code == SUCCESS
    started = ctx.resp.records[0]
    assert (started.status, started.engine_run_id, started.message) == ("started", "manual__2026-11-14", "picked up")
    assert started.started_at is not None and started.started_at.tzinfo is not None
    assert started.finished_at is None
    assert (started.workflow_name, started.engine_type, started.engine_workflow_id) == (
        row.workflow_name,
        row.engine_type,
        row.engine_workflow_id,
    )
    assert _stored(row.id) == started


def test_started_to_completed_sets_finished_at_and_keeps_started_at(data_dir):
    row = _execute(_workflow().id)
    started = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="completed")
    assert code == SUCCESS
    done = ctx.resp.records[0]
    assert done.status == "completed"
    assert done.started_at == started.started_at
    assert done.finished_at is not None and done.finished_at >= done.started_at


def test_requested_to_failed_sets_finished_at_and_leaves_started_at_empty(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, status="failed", message="could not start")
    assert code == SUCCESS
    failed = ctx.resp.records[0]
    assert (failed.status, failed.message) == ("failed", "could not start")
    assert failed.started_at is None and failed.finished_at is not None


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
    row = _execute(_workflow().id)
    for status in path:
        assert _update(row.id, status=status)[0] == SUCCESS
    before = _stored(row.id)
    code, _ = _update(row.id, status=bad, message="must not be stored", engine_run_id="must-not-be-stored")
    assert code == CONFLICT
    assert _stored(row.id) == before


def test_a_stale_second_update_after_completed_is_a_conflict(data_dir):
    row = _execute(_workflow().id)
    assert _update(row.id, status="started")[0] == SUCCESS
    assert _update(row.id, status="completed")[0] == SUCCESS
    done = _stored(row.id)
    assert _update(row.id, status="failed")[0] == CONFLICT  # a callback that arrives late
    assert _stored(row.id) == done


def test_the_same_status_again_is_accepted_and_changes_no_time(data_dir):
    row = _execute(_workflow().id)
    first = _update(row.id, status="started")[1].resp.records[0]
    code, ctx = _update(row.id, status="started", message="retry of the callback")
    assert code == SUCCESS
    again = ctx.resp.records[0]
    assert again.started_at == first.started_at and again.finished_at is None
    assert again.message == "retry of the callback"


def test_update_without_a_status_changes_only_the_given_fields(data_dir):
    row = _execute(_workflow().id)
    code, ctx = _update(row.id, engine_run_id="run-1")
    assert code == SUCCESS
    assert (ctx.resp.records[0].status, ctx.resp.records[0].engine_run_id) == ("requested", "run-1")


def test_update_rejects_bad_input(data_dir):
    row = _execute(_workflow().id)
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    assert logs.update(_ctx(status="started")) == INVALID_INPUT  # no id
    assert _update(row.id, status="bogus")[0] == INVALID_INPUT
    assert _update(row.id, engine_run_id="r" * 129)[0] == INVALID_INPUT
    assert _update(row.id, engine_run_id="r" * 128)[0] == SUCCESS
    assert _stored(row.id).status == "requested"


def test_update_of_an_unknown_row_is_not_found(data_dir):
    assert _update("no-such-row", status="started")[0] == NOT_FOUND
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py -v`
Expected: the new tests FAIL with `AttributeError: 'SqlAlchemyAppWfExecLogDao' object has no attribute 'update'`.

- [ ] **Step 3: Add `update` to the interface** (append inside `AppWfExecLogDao` in `app/core/dao/app_wf_exec_log_dao.py`)

```python

    @abstractmethod
    def update(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.id. Changes the given status, engine_run_id (up to 128 characters) and message. The snapshot
        columns are never changed. Status moves follow D30: requested to started or failed, started to completed or
        failed, completed and failed are final, the same status again is accepted and changes nothing. started_at is
        set on the move to started, finished_at on the move to completed or failed. NOT_FOUND if there is no such
        row, INVALID_INPUT for an unknown status or a too long engine_run_id, CONFLICT for any other move; a
        CONFLICT changes nothing."""
```

- [ ] **Step 4: Add `update` to the implementation** (in `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`: add the constant under `log = ...`, and the method at the end of `SqlAlchemyAppWfExecLogDao`)

```python
RUN_ID_MAX = 128
```

```python

    def update(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if req.engine_run_id is not None and len(req.engine_run_id) > RUN_ID_MAX:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfExecLogModel, req.id)
                if row is None:
                    return NOT_FOUND
                current = ExecStatus(row.status)
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT  # checked and written in this one transaction, so retries cannot race
                if req.engine_run_id is not None:
                    row.engine_run_id = req.engine_run_id
                if req.message is not None:
                    row.message = req.message
                if changes_status:
                    row.status = target.value
                    if target == ExecStatus.STARTED:
                        row.started_at = _now()
                    elif target.is_final:
                        row.finished_at = _now()
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log update failed")
            return FAILURE
```

Also add `CONFLICT` to the return-codes import of that module: `from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py tests/test_ctx_only_signatures.py -v` then `uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 82` with the summary `AppWfExecLogDao update with the D30 status rules`.

---

### Task 5: `list` with filters, paging and order

**Files:**
- Modify: `app/core/dao/app_wf_exec_log_dao.py`, `app/core/dao/impl/sqlalchemy_app_wf_exec_log_dao.py`
- Test: `tests/test_app_wf_exec_log_dao.py`

**Interfaces:**
- Consumes: everything from Tasks 3 and 4.
- Produces: `AppWfExecLogDao.list(ctx) -> int`.

- [ ] **Step 1: Write the failing tests** (add `from datetime import datetime, timedelta, timezone` and `from app.core.dao.impl import sqlalchemy_app_wf_exec_log_dao as dao_impl` to the imports of `tests/test_app_wf_exec_log_dao.py`, and append)

```python


def _list(**fields) -> list[AppWfExecLogRecord]:
    ctx = _ctx(**fields)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def _one_tick_per_call(monkeypatch):
    """Makes every _now() later than the one before, so the order of rows does not depend on the clock."""
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    ticks = (start + timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(dao_impl, "_now", lambda: next(ticks))


def test_list_of_an_empty_log_is_success_with_no_rows(data_dir):
    assert _list() == []


def test_list_is_newest_first(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    workflow = _workflow()
    first, second, third = (_execute(workflow.id) for _ in range(3))
    assert [r.id for r in _list()] == [third.id, second.id, first.id]


def test_list_filters_by_workflow_status_and_engine_type(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    download = _workflow("download")
    steps = _workflow("steps", engine_type="aws_step_functions", engine_workflow_id="arn:sm")
    a = _execute(download.id)
    b = _execute(download.id)
    c = _execute(steps.id)
    assert _update(b.id, status="started")[0] == SUCCESS

    assert {r.id for r in _list(workflow_id=download.id)} == {a.id, b.id}
    assert [r.id for r in _list(workflow_id=steps.id)] == [c.id]
    assert [r.id for r in _list(status="started")] == [b.id]
    assert {r.id for r in _list(status="requested")} == {a.id, c.id}
    assert [r.id for r in _list(engine_type="aws_step_functions")] == [c.id]
    assert [r.id for r in _list(workflow_id=download.id, status="requested")] == [a.id]
    assert _list(workflow_id="no-such-workflow") == []


def test_list_limit_and_offset(data_dir, monkeypatch):
    _one_tick_per_call(monkeypatch)
    workflow = _workflow()
    rows = [_execute(workflow.id) for _ in range(5)]
    newest_first = [r.id for r in reversed(rows)]
    assert [r.id for r in _list(limit=2)] == newest_first[:2]
    assert [r.id for r in _list(limit=2, offset=2)] == newest_first[2:4]
    assert [r.id for r in _list(offset=4)] == newest_first[4:]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py -v`
Expected: the new tests FAIL with `AttributeError: 'SqlAlchemyAppWfExecLogDao' object has no attribute 'list'`.

- [ ] **Step 3: Add `list` to the interface** (append inside `AppWfExecLogDao`)

```python

    @abstractmethod
    def list(self, ctx: AppWfExecLogCtx) -> int:
        """Optional filters: req.workflow_id, req.status, req.engine_type; optional req.limit and req.offset.
        Newest first (requested_at descending, then id). An empty result is SUCCESS with no records."""
```

- [ ] **Step 4: Add `list` to the implementation** (add `from sqlalchemy import select` to the imports, and the method at the end of the class)

```python

    def list(self, ctx: AppWfExecLogCtx) -> int:
        req = ctx.req
        try:
            query = select(AppWfExecLogModel)
            if req.workflow_id:
                query = query.where(AppWfExecLogModel.workflow_id == req.workflow_id)
            if req.status:
                query = query.where(AppWfExecLogModel.status == req.status)
            if req.engine_type:
                query = query.where(AppWfExecLogModel.engine_type == req.engine_type)
            query = query.order_by(AppWfExecLogModel.requested_at.desc(), AppWfExecLogModel.id)
            if req.limit is not None:
                query = query.limit(req.limit)
            if req.offset:
                query = query.offset(req.offset)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows_exec_log list failed")
            return FAILURE
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py tests/test_ctx_only_signatures.py -v` then `uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 82` with the summary `AppWfExecLogDao list with filters and paging`.

---

### Task 6: Shared transaction, Postgres, and the design document

**Files:**
- Test: `tests/test_app_wf_exec_log_dao.py`, `tests/test_postgres.py`
- Modify: `DESIGN.md`

**Interfaces:**
- Consumes: the finished DAO, `TransactionDao`, `TransactionCtx`.
- Produces: tests only, plus the `DESIGN.md` status note.

- [ ] **Step 1: Write the shared-transaction test** (add `from app.core.common.dtos.transaction_dtos import TransactionCtx` to the imports of `tests/test_app_wf_exec_log_dao.py` and append)

```python


def test_create_reads_the_workflow_inside_the_same_shared_transaction(data_dir):
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    new_workflow = AppWfCtx(
        transaction=rolled_back,
        req=AppWfReq(workflow_name="inside", engine_type="apache_airflow", engine_workflow_id="d"),
    )
    assert workflows.create(new_workflow) == SUCCESS  # not committed yet: only this transaction sees it
    execution = AppWfExecLogCtx(transaction=rolled_back, req=AppWfExecLogReq(workflow_id=new_workflow.resp.records[0].id))
    assert logs.create(execution) == SUCCESS
    assert execution.resp.records[0].workflow_name == "inside"
    assert transactions.rollback(rolled_back) == SUCCESS
    assert _list() == []
    assert workflows.get(AppWfCtx(req=AppWfReq(workflow_name="inside"))) == NOT_FOUND

    workflow = _workflow("kept")
    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    kept = AppWfExecLogCtx(transaction=committed, req=AppWfExecLogReq(workflow_id=workflow.id))
    assert logs.create(kept) == SUCCESS
    assert _list() == []  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert [r.id for r in _list()] == [kept.resp.records[0].id]
```

- [ ] **Step 2: Run it to verify it passes** (the DAO is finished, so this guards the behaviour and is not red first)

Run: `uv run pytest tests/test_app_wf_exec_log_dao.py -v`
Expected: all PASS.

- [ ] **Step 3: Write the Postgres test** (in `tests/test_postgres.py`: add `from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq` after the `app_wf_dtos` import, and append the test)

```python


def test_app_wf_exec_log_dao_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert "app_workflows_exec_log" in _admin_tables()
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    config = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "limit": None}
    made = AppWfCtx(
        req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="dag", config=config)
    )
    assert workflows.create(made) == SUCCESS
    workflow = made.resp.records[0]

    created = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.id))
    assert logs.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.status == "requested" and row.config_used == config and row.requested_at.tzinfo is not None
    assert logs.create(AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id="no-such-workflow"))) == NOT_FOUND

    assert logs.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="completed"))) == CONFLICT
    started = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="started", engine_run_id="run-1"))
    assert logs.update(started) == SUCCESS and started.resp.records[0].started_at is not None
    done = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="completed"))
    assert logs.update(done) == SUCCESS and done.resp.records[0].finished_at is not None
    assert logs.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="failed"))) == CONFLICT

    # No foreign key: the row survives the workflow being renamed and then deleted.
    assert workflows.update(AppWfCtx(req=AppWfReq(id=workflow.id, workflow_name="renamed"))) == SUCCESS
    assert workflows.delete(AppWfCtx(req=AppWfReq(id=workflow.id))) == SUCCESS
    fetched = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id))
    assert logs.get(fetched) == SUCCESS
    assert (fetched.resp.records[0].workflow_name, fetched.resp.records[0].config_used) == ("download_3_months", config)

    listed = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.id, status="completed"))
    assert logs.list(listed) == SUCCESS and [r.id for r in listed.resp.records] == [row.id]

    command.downgrade(postgres, "0003")
    assert "app_workflows_exec_log" not in _admin_tables()
    command.upgrade(postgres, "head")
    assert "app_workflows_exec_log" in _admin_tables()
```

Also change the return-codes import at the top of `tests/test_postgres.py` to `from app.core.common.return_codes import CONFLICT, NOT_FOUND, SUCCESS`.

- [ ] **Step 4: Run it against a real Postgres**

Run (from the app root; `docker` must be running):

```bash
docker run -d --name cca-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:16
sleep 6
CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55432/postgres uv run pytest tests/test_postgres.py -v
docker rm -f cca-pg
```

Expected: all Postgres tests PASS, including `test_app_wf_exec_log_dao_works_on_postgres`. The container is removed afterwards.

- [ ] **Step 5: Mark the table as built in `DESIGN.md`** (in the heading line of the section "The admin schema `consumer_comp_admin_db` (D48)", change ```app_workflows` built in story #81, the rest not built`` to ```app_workflows` built in story #81, `app_workflows_exec_log` built in story #82, the rest not built``; and add this paragraph after the "Built in story #81 (migration `0003`)" paragraph)

```markdown
Built in story #82 (migration `0004`): `AppWfExecLogDao` (create, get, list, update; no delete). `create` takes only the `workflow_id` and copies the workflow's name, engine type, engine workflow id and config into the row (D56); `ExecStatus` in `app/core/common/app_types_constants.py` holds the D30 moves. The optional reference to the MIO ingest row comes with #87.
```

- [ ] **Step 6: Run the whole suite and the lint**

Run: `uv run lint-imports` then `uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; every test passes, the Postgres tests skip when the variable is unset.

- [ ] **Step 7: Commit**

Run `/ccaa-commit-push 82` with the summary `Exec log transaction and Postgres tests, design note`.

---

## Self-Review

**1. Spec coverage**

| Spec requirement | Task |
|---|---|
| Table, columns, index, no foreign key, migration `0004` up and down | 2 |
| `ExecStatus` and the D30 moves next to it | 1 |
| `create` copies the workflow's details, always `requested`, NOT_FOUND, INVALID_INPUT, ignores `enabled` | 3 |
| Snapshot survives rename and delete of the workflow | 3 (`test_the_row_keeps_the_old_details...`), 6 (Postgres) |
| `get` | 3 |
| `update`: moves, same status again, times, engine_run_id up to 128, INVALID_INPUT, CONFLICT changes nothing, stale second update | 4 |
| `list`: filters `workflow_id`, `status`, `engine_type`, limit, offset, newest first | 5 |
| No delete (append-only) | no task adds one; Task 3 interface docstring says so |
| Factory `get_app_wf_exec_log_dao()` and singletons | 3 |
| Shared transaction with rollback, and the workflow read in the same transaction | 6 |
| Postgres run (D33) | 6 |
| Class and module names with `Wf` (D55) | 2, 3 |
| `DESIGN.md` note | 6 |

No gaps. The spec's one extra rule (engine_run_id over 128 characters is INVALID_INPUT) was added to the spec in the same commit as this plan.

**2. Placeholder scan:** no "TBD", "TODO" or "similar to Task N"; every code step has the code.

**3. Type consistency:** the signature rule (D37) holds for every function in the plan: the module helpers take one object (`_to_record(row: AppWfExecLogModel)`, `_new_row(workflow: AppWfModel)`), `_now()` takes nothing, and `ExecStatus.next_statuses` and `is_final` are properties with only `self`. Names used across tasks match: `AppWfExecLogCtx`, `AppWfExecLogReq`, `AppWfExecLogRecord`, `ExecStatus.next_statuses`, `ExecStatus.is_final`, `_now`, `RUN_ID_MAX`, `get_app_wf_exec_log_dao`. The test helper `_update` returns `(code, ctx)` in every use. In Task 6 the shared-transaction test uses `_list()` and `_workflow()` from Tasks 3 and 5.
