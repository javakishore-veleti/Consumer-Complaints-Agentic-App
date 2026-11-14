# M02-0031 (#81) Admin schema and `app_workflows` with its DAO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the admin schema `consumer_comp_admin_db`, the `app_workflows` table and one DAO (`AppWfDao`) with create, get, list, update and delete.

**Architecture:** Follow the existing `system_datasets` pattern: one SQLAlchemy model in `dao/impl/models.py`, one Alembic migration, one DAO interface in `dao/`, its SQLAlchemy implementation in `dao/impl/`, the singleton handed out by `dao/objects_factory.py`. Every method takes one ctx and returns an integer code. Only `dao/impl` sees SQLAlchemy.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, pytest, `uv`; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0031-admin-schema-app-workflows-design.md`. Decisions: D43, D48, D52, D55 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there unless it says the repository root. All paths below are relative to it.
- Schema name exactly `consumer_comp_admin_db`; table name exactly `app_workflows` (D48, D43).
- In **class names** `Workflows` is `Wf` (`AppWfDao`, `AppWfCtx`, `AppWfReq`, `AppWfResp`, `AppWfRecord`, `AppWfModel`, `SqlAlchemyAppWfDao`); module names follow the class names (D55).
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`... (D37, enforced by `tests/test_ctx_only_signatures.py`).
- Every method that takes a ctx returns an integer from `app/core/common/return_codes.py`: `SUCCESS 0`, `FAILURE 1`, `NOT_FOUND 2`, `INVALID_INPUT 3`, `CONFLICT 4`.
- `config` is a nullable JSON column; nothing means NULL, never `{}` (D55).
- `workflow_name` is at most 100 characters and unique; `engine_type` must be one of `EngineType`.
- Migrations use Alembic Python ops, never raw SQL (D23), and work on SQLite and Postgres (D33).
- Only `dao/impl` imports SQLAlchemy; only `dao/objects_factory.py` imports `dao/impl` (`npm run local:api:lint`).
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35).
- Commit with `/ccaa-commit-push 81` (it checks lint and tests, writes the `M02-0031 #81: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/config.py` (modify) | `SCHEMA_ADMIN`, added to `ALL_SCHEMAS` |
| `app/core/common/app_types_constants.py` (create) | `AppTypeEnum` parent and `EngineType` |
| `alembic/versions/0003_create_admin_app_workflows.py` (create) | the table |
| `app/core/dao/impl/models.py` (modify) | `AppWfModel` |
| `app/core/common/dtos/app_wf_dtos.py` (create) | `AppWfRecord`, `AppWfReq`, `AppWfResp`, `AppWfCtx` |
| `app/core/dao/app_wf_dao.py` (create) | `AppWfDao` interface |
| `app/core/dao/impl/sqlalchemy_app_wf_dao.py` (create) | the implementation |
| `app/core/dao/objects_factory.py` (modify) | `get_app_wf_dao()` |
| `tests/test_app_types_constants.py`, `tests/test_app_wf_dao.py` (create) | tests |
| `tests/test_schema.py`, `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | tests |
| `DESIGN.md` (modify) | mark the table built |

---

### Task 1: Admin schema name and the types file

**Files:**
- Modify: `app/core/common/config.py`
- Create: `app/core/common/app_types_constants.py`
- Create: `tests/test_app_types_constants.py`
- Modify: `tests/test_schema.py`

**Interfaces:**
- Produces: `SCHEMA_ADMIN: str`; `ALL_SCHEMAS` now has four names; `AppTypeEnum.values() -> list[str]`; `EngineType.APACHE_AIRFLOW == "apache_airflow"`, `EngineType.AWS_STEP_FUNCTIONS == "aws_step_functions"`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_app_types_constants.py`:

```python
from app.core.common.app_types_constants import AppTypeEnum, EngineType


def test_engine_type_values_are_the_short_codes():
    assert EngineType.values() == ["apache_airflow", "aws_step_functions"]


def test_engine_type_members_are_plain_strings():
    assert EngineType.APACHE_AIRFLOW == "apache_airflow"
    assert "aws_step_functions" in EngineType.values()
    assert "bogus" not in EngineType.values()


def test_the_parent_has_no_members_and_every_type_list_extends_it():
    assert list(AppTypeEnum) == []
    assert issubclass(EngineType, AppTypeEnum)
```

In `tests/test_schema.py` replace the first test with:

```python
def test_schema_names():
    assert ALL_SCHEMAS == (
        "consumer_comp_db",
        "consumer_compl_intellect_db",
        "consumer_comp_users_db",
        "consumer_comp_admin_db",
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_types_constants.py tests/test_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.common.app_types_constants'`, and `test_schema_names` fails on the tuple.

- [ ] **Step 3: Write the minimal implementation**

In `app/core/common/config.py`, add `SCHEMA_ADMIN`, put it last in `ALL_SCHEMAS`, and add a line to the docstring list:

```python
SCHEMA_COMPLAINTS = "consumer_comp_db"
SCHEMA_INTELLECT = "consumer_compl_intellect_db"
SCHEMA_USERS = "consumer_comp_users_db"
SCHEMA_ADMIN = "consumer_comp_admin_db"
ALL_SCHEMAS = (SCHEMA_COMPLAINTS, SCHEMA_INTELLECT, SCHEMA_USERS, SCHEMA_ADMIN)
```

and in the module docstring, after the `consumer_comp_users_db` line:

```
* consumer_comp_admin_db      everything admin-related: the workflow registry and the catalog (D48)
```

Create `app/core/common/app_types_constants.py`:

```python
"""Every type list of the app (DESIGN.md, D55). Each list is an enum whose parent is AppTypeEnum.

Add the next list (dataset location types, statuses, ...) here as one more subclass.
"""

from enum import Enum


class AppTypeEnum(str, Enum):
    """Parent of every type list. It has no members of its own."""

    @classmethod
    def values(cls) -> list[str]:
        """The allowed string values, in definition order. Callers check `value in EngineType.values()`."""
        return [member.value for member in cls]


class EngineType(AppTypeEnum):
    """The workflow engines (D52). M02 runs only apache_airflow."""

    APACHE_AIRFLOW = "apache_airflow"
    AWS_STEP_FUNCTIONS = "aws_step_functions"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_types_constants.py tests/test_schema.py tests/test_ctx_only_signatures.py -v`
Expected: PASS (the signature test accepts `values(cls)` because `cls` is skipped).

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 81` with the summary `add the admin schema name and the app types file`. Stage `app/core/common/config.py`, `app/core/common/app_types_constants.py`, `tests/test_app_types_constants.py`, `tests/test_schema.py` and `docs/Project_Management/Issues/Milestone_02.md` (the milestone log change).

---

### Task 2: The table (model and migration)

**Files:**
- Modify: `app/core/dao/impl/models.py`
- Create: `alembic/versions/0003_create_admin_app_workflows.py`
- Modify: `tests/test_schema.py`

**Interfaces:**
- Consumes: `SCHEMA_ADMIN` from Task 1.
- Produces: table `consumer_comp_admin_db.app_workflows`; `AppWfModel` with attributes `id, workflow_name, engine_type, engine_workflow_id, config, enabled, created_at, updated_at`.

- [ ] **Step 1: Write the failing tests**

At the top of `tests/test_schema.py` the imports become:

```python
import sqlite3

from alembic import command
from alembic.config import Config

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT
```

Then add:

```python
def _admin_db(data_dir):
    return sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite")


def test_app_workflows_table_is_in_the_admin_schema_with_the_expected_columns(data_dir):
    with _admin_db(data_dir) as db:
        columns = {r[1]: (r[2], r[3]) for r in db.execute("pragma table_info(app_workflows)")}  # name: (type, not null)
        sql = db.execute("select sql from sqlite_master where name = 'app_workflows'").fetchone()[0]
    assert set(columns) == {
        "id",
        "workflow_name",
        "engine_type",
        "engine_workflow_id",
        "config",
        "enabled",
        "created_at",
        "updated_at",
    }
    assert columns["workflow_name"] == ("VARCHAR(100)", 1)
    assert columns["engine_type"] == ("VARCHAR(32)", 1)
    assert columns["engine_workflow_id"] == ("VARCHAR(255)", 1)
    assert columns["config"][1] == 0  # nullable: nothing is stored as NULL, never {}
    assert "uq_app_workflows_workflow_name" in sql


def test_migration_0003_runs_down_and_up(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0002")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'app_workflows'").fetchall() == []
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'app_workflows'").fetchall() != []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schema.py -v`
Expected: FAIL: `table_info` is empty (no such table) and `downgrade(config, "0002")` fails because revision `0003` does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

Create `alembic/versions/0003_create_admin_app_workflows.py`:

```python
"""create app_workflows in the admin schema (the registry of workflows)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "app_workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("engine_type", sa.String(32), nullable=False),
        sa.Column("engine_workflow_id", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workflow_name", name="uq_app_workflows_workflow_name"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("app_workflows", schema=SCHEMA)
```

In `app/core/dao/impl/models.py` change the imports and add the model at the end:

```python
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Text, UniqueConstraint, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.common.config import SCHEMA_ADMIN, SCHEMA_COMPLAINTS
```

```python
class AppWfModel(Base):
    __tablename__ = "app_workflows"
    __table_args__ = (
        UniqueConstraint("workflow_name", name="uq_app_workflows_workflow_name"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    engine_type: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # none_as_null: Python None is stored as SQL NULL, not as the JSON text "null".
    config: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_schema.py tests/test_ctx_only_signatures.py -v && npm --prefix ../.. run local:api:lint`
Expected: PASS, and `Contracts: 7 kept, 0 broken.`

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 81` with the summary `add the app_workflows table and migration`. Stage `app/core/dao/impl/models.py`, `alembic/versions/0003_create_admin_app_workflows.py`, `tests/test_schema.py`.

---

### Task 3: DTOs, DAO interface, factory, and create, get, list

**Files:**
- Create: `app/core/common/dtos/app_wf_dtos.py`
- Create: `app/core/dao/app_wf_dao.py`
- Create: `app/core/dao/impl/sqlalchemy_app_wf_dao.py`
- Modify: `app/core/dao/objects_factory.py`
- Create: `tests/test_app_wf_dao.py`

**Interfaces:**
- Consumes: `AppWfModel` (Task 2), `EngineType` (Task 1), `unit_of_work(ctx)` from `app/core/dao/impl/unit_of_work.py`.
- Produces: `AppWfCtx(transaction=None, req=AppWfReq(), resp=AppWfResp())`; `AppWfReq(id, workflow_name, engine_type, engine_workflow_id, config, enabled)` (all default `None`, `None` means "not given"); `AppWfResp(records: list[AppWfRecord])`; `AppWfRecord(id, workflow_name, engine_type, engine_workflow_id, config, enabled, created_at, updated_at)`; `AppWfDao.create/get/list/update/delete(ctx: AppWfCtx) -> int`; `DaoObjectsFactory.get_app_wf_dao() -> AppWfDao`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_app_wf_dao.py`:

```python
import sqlite3

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> AppWfCtx:
    return AppWfCtx(req=AppWfReq(**fields))


def _create(dao, name="download_3_months", engine_workflow_id="download_dag", **more) -> AppWfCtx:
    ctx = _ctx(workflow_name=name, engine_type="apache_airflow", engine_workflow_id=engine_workflow_id, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def test_create_returns_the_row_with_defaults(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    row = _create(dao).resp.records[0]
    assert len(row.id) == 36
    assert (row.workflow_name, row.engine_type, row.engine_workflow_id) == (
        "download_3_months",
        "apache_airflow",
        "download_dag",
    )
    assert row.enabled is True
    assert row.config is None
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_no_config_is_stored_as_sql_null_and_not_as_json_null_or_empty_object(data_dir):
    _create(DaoObjectsFactory.get_app_wf_dao())
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        assert db.execute("select config from app_workflows").fetchall() == [(None,)]


def test_config_round_trips_nested_json(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    config = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "dry_run": False, "limit": None}
    created = _create(dao, config=config)
    assert created.resp.records[0].config == config
    fetched = _ctx(id=created.resp.records[0].id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].config == config


def test_create_accepts_a_100_character_name_and_a_disabled_workflow(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    row = _create(dao, name="n" * 100, enabled=False).resp.records[0]
    assert len(row.workflow_name) == 100 and row.enabled is False


def test_create_rejects_a_duplicate_name(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    _create(dao)
    again = _ctx(workflow_name="download_3_months", engine_type="aws_step_functions", engine_workflow_id="other")
    assert dao.create(again) == CONFLICT


def test_create_rejects_invalid_input(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    good = dict(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="d")
    for bad in (
        {"workflow_name": None},
        {"workflow_name": "  "},
        {"workflow_name": "n" * 101},
        {"engine_type": None},
        {"engine_type": "bogus"},
        {"engine_workflow_id": None},
        {"engine_workflow_id": ""},
        {"engine_workflow_id": "d" * 256},
    ):
        assert dao.create(_ctx(**{**good, **bad})) == INVALID_INPUT, bad


def test_get_by_id_and_by_name(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    created = _create(dao).resp.records[0]
    by_id = _ctx(id=created.id)
    by_name = _ctx(workflow_name="download_3_months")
    assert dao.get(by_id) == SUCCESS and by_id.resp.records[0].workflow_name == "download_3_months"
    assert dao.get(by_name) == SUCCESS and by_name.resp.records[0].id == created.id


def test_get_not_found_and_invalid_input(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx(workflow_name="nope")) == NOT_FOUND
    assert dao.get(_ctx()) == INVALID_INPUT


def test_list_is_ordered_by_name_and_filters(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    _create(dao, name="b_flow", engine_workflow_id="b")
    _create(dao, name="a_flow", engine_workflow_id="a", enabled=False)
    other = _ctx(workflow_name="c_flow", engine_type="aws_step_functions", engine_workflow_id="c")
    assert dao.create(other) == SUCCESS

    everything = _ctx()
    assert dao.list(everything) == SUCCESS
    assert [r.workflow_name for r in everything.resp.records] == ["a_flow", "b_flow", "c_flow"]

    airflow = _ctx(engine_type="apache_airflow")
    assert dao.list(airflow) == SUCCESS and [r.workflow_name for r in airflow.resp.records] == ["a_flow", "b_flow"]
    disabled = _ctx(enabled=False)
    assert dao.list(disabled) == SUCCESS and [r.workflow_name for r in disabled.resp.records] == ["a_flow"]
    none = _ctx(engine_type="bogus")
    assert dao.list(none) == SUCCESS and none.resp.records == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_wf_dao.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.common.dtos.app_wf_dtos'`.

- [ ] **Step 3: Write the minimal implementation**

Create `app/core/common/dtos/app_wf_dtos.py`:

```python
"""Ctx, Req and Resp for the app_workflows table (the registry of workflows, DESIGN.md D43)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class AppWfRecord:
    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    config: dict | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class AppWfReq:
    """A field left as None means "not given". id (or, for get, workflow_name) identifies one row."""

    id: str | None = None
    workflow_name: str | None = None
    engine_type: str | None = None
    engine_workflow_id: str | None = None
    config: dict | None = None
    enabled: bool | None = None


@dataclass
class AppWfResp:
    records: list[AppWfRecord] = field(default_factory=list)


@dataclass
class AppWfCtx(TransactionalCtx):
    req: AppWfReq = field(default_factory=AppWfReq)
    resp: AppWfResp = field(default_factory=AppWfResp)
```

Create `app/core/dao/app_wf_dao.py`:

```python
"""Interface of the DAO for the app_workflows table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.singleton import SingletonMeta


class AppWfDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one AppWfCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits."""

    @abstractmethod
    def create(self, ctx: AppWfCtx) -> int:
        """Needs req.workflow_name (up to 100 characters), req.engine_type (an EngineType value) and
        req.engine_workflow_id (up to 255 characters). Optional: config (default NULL), enabled (default true).
        INVALID_INPUT for a missing or unacceptable field, CONFLICT if the name is taken."""

    @abstractmethod
    def get(self, ctx: AppWfCtx) -> int:
        """Needs req.id or req.workflow_name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is
        no such row."""

    @abstractmethod
    def list(self, ctx: AppWfCtx) -> int:
        """Optional filters: req.engine_type, req.enabled. Ordered by workflow_name."""

    @abstractmethod
    def update(self, ctx: AppWfCtx) -> int:
        """Needs req.id. Changes the given workflow_name, engine_type, engine_workflow_id, config and enabled and
        sets updated_at. NOT_FOUND if there is no such row, INVALID_INPUT for an unacceptable field, CONFLICT if the
        new name belongs to another row."""

    @abstractmethod
    def delete(self, ctx: AppWfCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row."""
```

Create `app/core/dao/impl/sqlalchemy_app_wf_dao.py` (create, get and list now; update and delete come in Task 4 and are added to this class):

```python
"""AppWfDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common.app_types_constants import EngineType
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_dao import AppWfDao
from app.core.dao.impl.models import AppWfModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

NAME_MAX = 100
ENGINE_WORKFLOW_ID_MAX = 255


def _as_utc(stamp: datetime) -> datetime:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp


def _to_record(row: AppWfModel) -> AppWfRecord:
    return AppWfRecord(
        id=row.id,
        workflow_name=row.workflow_name,
        engine_type=row.engine_type,
        engine_workflow_id=row.engine_workflow_id,
        config=row.config,
        enabled=row.enabled,
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _has_invalid_field(req: AppWfReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    if req.workflow_name is not None and (not req.workflow_name.strip() or len(req.workflow_name) > NAME_MAX):
        return True
    if req.engine_type is not None and req.engine_type not in EngineType.values():
        return True
    if req.engine_workflow_id is not None and (
        not req.engine_workflow_id.strip() or len(req.engine_workflow_id) > ENGINE_WORKFLOW_ID_MAX
    ):
        return True
    return False


def _find_by_name(session: Session, req: AppWfReq) -> AppWfModel | None:
    return session.scalars(select(AppWfModel).where(AppWfModel.workflow_name == req.workflow_name)).first()


class SqlAlchemyAppWfDao(AppWfDao):
    def create(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (req.workflow_name and req.engine_type and req.engine_workflow_id) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if _find_by_name(session, req) is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = AppWfModel(
                    id=str(uuid4()),
                    workflow_name=req.workflow_name,
                    engine_type=req.engine_type,
                    engine_workflow_id=req.engine_workflow_id,
                    config=req.config,
                    enabled=True if req.enabled is None else req.enabled,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows create failed")
            return FAILURE

    def get(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (req.id or req.workflow_name):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id) if req.id else _find_by_name(session, req)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows get failed")
            return FAILURE

    def list(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        try:
            query = select(AppWfModel)
            if req.engine_type is not None:
                query = query.where(AppWfModel.engine_type == req.engine_type)
            if req.enabled is not None:
                query = query.where(AppWfModel.enabled == req.enabled)
            query = query.order_by(AppWfModel.workflow_name)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows list failed")
            return FAILURE
```

Note: the class is incomplete until Task 4 (`SingletonMeta` is an `ABCMeta`, so a class with abstract methods left over cannot be built). To keep Task 3 testable, add these two stubs at the end of the class now and remove them in Task 4 when the real methods go in:

```python
    def update(self, ctx: AppWfCtx) -> int:
        return FAILURE  # replaced in Task 4

    def delete(self, ctx: AppWfCtx) -> int:
        return FAILURE  # replaced in Task 4
```

In `app/core/dao/objects_factory.py` add the import `from app.core.dao.app_wf_dao import AppWfDao` (keep imports alphabetical: it goes first) and this static method before `get_data_ingest_dao`:

```python
    @staticmethod
    def get_app_wf_dao() -> AppWfDao:
        from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao

        return SqlAlchemyAppWfDao()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_wf_dao.py tests/test_ctx_only_signatures.py tests/test_import_contracts.py -v && npm --prefix ../.. run local:api:lint`
Expected: PASS, `Contracts: 7 kept, 0 broken.`

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 81` with the summary `add the AppWfDao with create, get and list`. Stage the five files of this task.

---

### Task 4: Update and delete

**Files:**
- Modify: `app/core/dao/impl/sqlalchemy_app_wf_dao.py`
- Modify: `tests/test_app_wf_dao.py`

**Interfaces:**
- Consumes: everything from Task 3, including the two stub methods to replace.
- Produces: working `AppWfDao.update(ctx)` and `AppWfDao.delete(ctx)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_app_wf_dao.py`:

```python
def test_update_changes_only_the_given_fields_and_the_time(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    created = _create(dao, config={"a": 1}).resp.records[0]
    other = _create(dao, name="other", engine_workflow_id="o").resp.records[0]

    updated = _ctx(id=created.id, engine_workflow_id="new_dag", enabled=False, config={"b": [1, 2]})
    assert dao.update(updated) == SUCCESS
    row = updated.resp.records[0]
    assert (row.workflow_name, row.engine_type, row.engine_workflow_id) == (
        "download_3_months",
        "apache_airflow",
        "new_dag",
    )
    assert row.enabled is False and row.config == {"b": [1, 2]}
    assert row.updated_at >= created.updated_at and row.created_at == created.created_at

    untouched = _ctx(id=other.id)
    assert dao.get(untouched) == SUCCESS and untouched.resp.records[0].engine_workflow_id == "o"


def test_update_keeps_config_when_it_is_not_given(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    created = _create(dao, config={"keep": True}).resp.records[0]
    renamed = _ctx(id=created.id, workflow_name="renamed")
    assert dao.update(renamed) == SUCCESS
    assert renamed.resp.records[0].config == {"keep": True}


def test_update_name_conflicts_only_with_another_row(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    first = _create(dao, name="first", engine_workflow_id="f").resp.records[0]
    _create(dao, name="second", engine_workflow_id="s")
    assert dao.update(_ctx(id=first.id, workflow_name="second")) == CONFLICT
    same = _ctx(id=first.id, workflow_name="first", enabled=False)  # its own name is not a conflict
    assert dao.update(same) == SUCCESS
    check = _ctx(id=first.id)
    assert dao.get(check) == SUCCESS and check.resp.records[0].workflow_name == "first"


def test_update_not_found_and_invalid_input(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    created = _create(dao).resp.records[0]
    assert dao.update(_ctx(workflow_name="x")) == INVALID_INPUT  # no id
    assert dao.update(_ctx(id="nope", enabled=False)) == NOT_FOUND
    for bad in ({"workflow_name": ""}, {"workflow_name": "n" * 101}, {"engine_type": "bogus"}, {"engine_workflow_id": " "}):
        assert dao.update(_ctx(id=created.id, **bad)) == INVALID_INPUT, bad
    unchanged = _ctx(id=created.id)
    assert dao.get(unchanged) == SUCCESS and unchanged.resp.records[0].workflow_name == "download_3_months"


def test_delete_returns_the_row_and_removes_it(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    created = _create(dao).resp.records[0]
    deleted = _ctx(id=created.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].workflow_name == "download_3_months"
    assert dao.get(_ctx(id=created.id)) == NOT_FOUND
    assert dao.delete(_ctx(id=created.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    _create(dao)  # the name is free again
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app_wf_dao.py -v`
Expected: the five new tests FAIL (the stubs return `FAILURE = 1`); the Task 3 tests still pass.

- [ ] **Step 3: Write the minimal implementation**

In `app/core/dao/impl/sqlalchemy_app_wf_dao.py` delete the two stub methods and add, inside the class:

```python
    def update(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id)
                if row is None:
                    return NOT_FOUND
                if req.workflow_name is not None and req.workflow_name != row.workflow_name:
                    if _find_by_name(session, req) is not None:
                        return CONFLICT
                if req.workflow_name is not None:
                    row.workflow_name = req.workflow_name
                if req.engine_type is not None:
                    row.engine_type = req.engine_type
                if req.engine_workflow_id is not None:
                    row.engine_workflow_id = req.engine_workflow_id
                if req.config is not None:
                    row.config = req.config
                if req.enabled is not None:
                    row.enabled = req.enabled
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("app_workflows update failed")
            return FAILURE

    def delete(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(AppWfModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("app_workflows delete failed")
            return FAILURE
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app_wf_dao.py tests/test_ctx_only_signatures.py -v`
Expected: PASS, all tests in `test_app_wf_dao.py`.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 81` with the summary `add update and delete to the AppWfDao`. Stage `app/core/dao/impl/sqlalchemy_app_wf_dao.py` and `tests/test_app_wf_dao.py`.

---

### Task 5: Transactions, singletons and Postgres

**Files:**
- Modify: `tests/test_app_wf_dao.py`
- Modify: `tests/test_singletons.py`
- Modify: `tests/test_postgres.py`

**Interfaces:**
- Consumes: `DaoObjectsFactory.get_transaction_dao()` (`begin/commit/rollback(TransactionCtx) -> int`), `AppWfDao`, `SqlAlchemyAppWfDao`.
- Produces: tests only.

- [ ] **Step 1: Write the failing or new tests**

Append to `tests/test_app_wf_dao.py` (add `from app.core.common.dtos.transaction_dtos import TransactionCtx` to the imports):

```python
def _in_transaction(tx: TransactionCtx, **fields) -> AppWfCtx:
    return AppWfCtx(transaction=tx, req=AppWfReq(**fields))


def test_a_shared_transaction_can_be_rolled_back_or_committed(data_dir):
    dao = DaoObjectsFactory.get_app_wf_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    assert dao.create(_in_transaction(rolled_back, workflow_name="gone", engine_type="apache_airflow", engine_workflow_id="d")) == SUCCESS
    seen = _in_transaction(rolled_back, workflow_name="gone")
    assert dao.get(seen) == SUCCESS  # visible inside the transaction
    assert transactions.rollback(rolled_back) == SUCCESS
    assert dao.get(_ctx(workflow_name="gone")) == NOT_FOUND

    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    assert dao.create(_in_transaction(committed, workflow_name="kept", engine_type="apache_airflow", engine_workflow_id="d")) == SUCCESS
    assert dao.get(_ctx(workflow_name="kept")) == NOT_FOUND  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert dao.get(_ctx(workflow_name="kept")) == SUCCESS
```

In `tests/test_singletons.py` add `from app.core.dao.app_wf_dao import AppWfDao` and `from app.core.dao.impl.sqlalchemy_app_wf_dao import SqlAlchemyAppWfDao` with the other imports, then add `(DaoObjectsFactory.get_app_wf_dao, AppWfDao),` as the first entry of the tuple in `test_factories_return_the_same_object_typed_as_the_interface`, and `assert SqlAlchemyAppWfDao() is SqlAlchemyAppWfDao()` in `test_the_classes_themselves_are_singletons`.

In `tests/test_postgres.py` change the import line to `from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT, SCHEMA_ADMIN, SCHEMA_COMPLAINTS`, add `from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq`, add this helper below `_complaint_tables`:

```python
def _admin_tables():
    engine = create_engine(URL)
    try:
        return set(inspect(engine).get_table_names(schema=SCHEMA_ADMIN))
    finally:
        engine.dispose()
```

and add this test at the end of the file:

```python
def test_app_wf_dao_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert "app_workflows" in _admin_tables()
    dao = DaoObjectsFactory.get_app_wf_dao()
    config = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "limit": None}
    created = AppWfCtx(
        req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="dag", config=config)
    )
    assert dao.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.created_at.tzinfo is not None and row.config == config

    again = AppWfCtx(req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="x"))
    assert dao.create(again) == CONFLICT

    no_config = AppWfCtx(req=AppWfReq(workflow_name="plain", engine_type="aws_step_functions", engine_workflow_id="sm"))
    assert dao.create(no_config) == SUCCESS and no_config.resp.records[0].config is None

    fetched = AppWfCtx(req=AppWfReq(id=row.id))
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].config == config
    listed = AppWfCtx(req=AppWfReq(engine_type="apache_airflow"))
    assert dao.list(listed) == SUCCESS and [r.workflow_name for r in listed.resp.records] == ["download_3_months"]
    assert dao.update(AppWfCtx(req=AppWfReq(id=row.id, enabled=False))) == SUCCESS
    assert dao.delete(AppWfCtx(req=AppWfReq(id=row.id))) == SUCCESS
```

and in `test_upgrade_downgrade_upgrade` add, after each of the three existing table checks respectively: after the first `assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()` add `assert "app_workflows" in _admin_tables()`; after the `assert not {...} & _complaint_tables()` add `assert "app_workflows" not in _admin_tables()`; after the last `assert {...} <= _complaint_tables()` add `assert "app_workflows" in _admin_tables()`.

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test_app_wf_dao.py tests/test_singletons.py -v`
Expected: PASS (the DAO already works; these tests lock in transaction behavior and singletons). If `test_singletons` fails, the import or tuple edit is wrong: fix the test, not the DAO.

- [ ] **Step 3: Run the Postgres tests**

Run (needs Docker): `docker run -d --name cca-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:16`, wait a few seconds, then
`CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55432/postgres uv run pytest tests/test_postgres.py -v`
Expected: PASS, including `test_app_wf_dao_works_on_postgres`. Then `docker rm -f cca-pg`. If Docker is not available, say so in the story report; CI runs the same file against its Postgres service (D33).

- [ ] **Step 4: Run everything**

Run from the repository root: `npm run local:api:lint && npm run local:api:test`
Expected: `Contracts: 7 kept, 0 broken.`; all tests pass; the Postgres tests are skipped unless the URL is set.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 81` with the summary `test transactions, singletons and Postgres for the AppWfDao`. Stage the three test files.

---

### Task 6: Documentation

**Files:**
- Modify: `DESIGN.md`

- [ ] **Step 1: Mark the table built**

In `DESIGN.md`, the heading `### The admin schema `consumer_comp_admin_db` (D48) — **Decided (D43, D46 to D52), not built**` becomes:

```
### The admin schema `consumer_comp_admin_db` (D48) — **Decided (D43, D46 to D52); `app_workflows` built in story #81, the rest not built**
```

In the `app_workflows` column table, replace the `config` row and the last row with:

```
| config | JSON, nullable (NULL means none, never `{}`); non-secret values only, secrets stay in `.env` and Airflow Variables (D42) |
| enabled, created_at, updated_at | built: `enabled` defaults to true; times are UTC |
```

Directly under the table add:

```
Built in story #81 (migration `0003`): `AppWfDao` (create, get by id or name, list by engine type and enabled, update, delete). `engine_type` is checked against `EngineType` in `app/core/common/app_types_constants.py` (D55); checking it against the registered engine classes comes with the engine interface (#83) and the start endpoint (#42).
```

- [ ] **Step 2: Run everything once more**

Run from the repository root: `npm run local:api:lint && npm run local:api:test`
Expected: `Contracts: 7 kept, 0 broken.` and all tests pass.

- [ ] **Step 3: Commit**

Run `/ccaa-commit-push 81` with the summary `mark app_workflows built in the design`. Stage `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

---

## Self-Review

- **Spec coverage:** schema name (Task 1), types file with parent enum (Task 1), table with every column, nullable JSON and unique name (Task 2), CRUD with every return code, id-or-name get, filters, update semantics (Tasks 3 and 4), `Wf` class names and module names (Tasks 3 and 4), factory method in the static style (Task 3), transaction and singleton tests (Task 5), Postgres cases (Task 5), up and down migration test (Task 2), design note (Task 6). The spec's `is_valid(value)` was dropped: a method taking a bare `str` breaks the one-object signature rule (D37, `test_ctx_only_signatures`), so callers use `value in EngineType.values()`.
- **Placeholders:** none. The two Task 3 stubs are replaced in Task 4, as stated in both tasks.
- **Type consistency:** `AppWfCtx/AppWfReq/AppWfResp/AppWfRecord`, `AppWfDao`, `SqlAlchemyAppWfDao`, `AppWfModel`, `get_app_wf_dao`, `EngineType.values()` and `SCHEMA_ADMIN` are spelled the same in every task. Return codes are the five in `return_codes.py`.
