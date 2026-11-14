# M02-0036 (#86) Catalog tables with their DAOs and the seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `datasets`, `datasets_location`, `mios` and `mios_datasets` in the admin schema, one DAO for each (create, get, list, update, delete), and a seed of the CFPB dataset, its two locations and four MIOs.

**Architecture:** Follow the `app_workflows` (#81) and `app_workflows_exec_log` (#82) pattern: SQLAlchemy models in `dao/impl/models.py`, Alembic migrations `0005` (tables) and `0006` (seed), DTOs in `common/dtos/`, one interface per table in `dao/`, one SQLAlchemy implementation per table in `dao/impl/`, singletons handed out by `dao/objects_factory.py`. No database foreign keys (D57): each DAO keeps the parent and in-use rules inside one transaction.

**Tech Stack:** Python 3.13, SQLAlchemy 2, Alembic, pytest, `uv`; SQLite locally and Postgres in CI.

Spec: `docs/Superpowers/specs/M02-0036-catalog-tables-design.md`. Decisions: D7, D22, D23, D26, D37, D45, D48, D49, D55, D56, D57 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- App root is `Middleware/ConsumerComplaintsHandsOn`; run every command below from there unless it says the repository root. All paths below are relative to it, except the plan and spec paths.
- Tables in schema `consumer_comp_admin_db` (`SCHEMA_ADMIN`): `datasets`, `datasets_location`, `mios`, `mios_datasets`; migration `0005` (revises `0004`) creates them, `0006` (revises `0005`) seeds them.
- `Wf` is only for workflows (D55), so class names are `DatasetModel`, `DatasetLocationModel`, `MioModel`, `MioDatasetModel`; `DatasetDao`, `DatasetLocationDao`, `MioDao`, `MioDatasetDao`; `DatasetCtx`/`Req`/`Resp`/`Record` and the same for `DatasetLocation`, `Mio`, `MioDataset`; `SqlAlchemyDatasetDao`, `SqlAlchemyDatasetLocationDao`, `SqlAlchemyMioDao`, `SqlAlchemyMioDatasetDao`. Module names follow the class names.
- Every function takes nothing or exactly one object: never two loose arguments and never a bare `str`, `int`, `bool`, `dict`... (D37, enforced by `tests/test_ctx_only_signatures.py`, which scans `app`, `alembic`, `scripts` and `main.py`; it skips `self` and `cls`). So a helper that would need a row **and** a session is written inline in the DAO method instead.
- Do not annotate with `list[...]` inside a DAO class body: the method named `list` shadows the builtin there. Use list comprehensions and no annotation.
- Every method that takes a ctx returns an integer from `app/core/common/return_codes.py`: `SUCCESS 0`, `FAILURE 1`, `NOT_FOUND 2`, `INVALID_INPUT 3`, `CONFLICT 4`.
- Names (`datasets.name`, `mios.name`) are trimmed and case sensitive; a name or code taken by two writers at once is `CONFLICT` from the unique constraint (`IntegrityError`).
- A field left as `None` in a request means "not given"; so `description` and `credentials_ref` cannot be cleared to NULL by an update (accepted for the MVP).
- All early `return`s in a DAO method happen **before** any change to a loaded row: leaving the `with unit_of_work(...)` block commits whatever is pending.
- `datasets.code`: 1 to 15 characters, only `A-Z` and `0-9`. Env var name: exactly `LOCAL_DATA_PATH_` + the dataset's code. `credentials_ref`: 1 to 100 characters of letters, digits, `_`, `.`, `-`.
- Locations: `path` and `local_env_var_name` are mutually exclusive and exactly one is set; `local_env_var_name` only for type `local`; types are the values of `DatasetLocationType`.
- No code reads a MIO's name or description to choose a dataset, location or window (D57).
- Migrations use Alembic Python ops, never raw SQL strings (D23), and work on SQLite and Postgres (D33). The seed uses fixed ids so a downgrade removes exactly the seeded rows.
- Only `dao/impl` imports SQLAlchemy; only `dao/objects_factory.py` imports `dao/impl` (`npm run local:api:lint`).
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36). Nothing machine-specific is committed (D35).
- Test names written below use the prefix `t_` for datasets and MIOs, and dataset codes `T1`, `T2`..., because the seed rows (`cfpb_consumer_complaints`, `CFPB`, the four "Customer complaints ..." MIOs) are present in every migrated test database. Never assert that a list is exactly your rows without filtering to your prefix or ids.
- Commit with `/ccaa-commit-push 86` (it checks lint and tests, writes the `M02-0036 #86: ...` message and strips any AI trailer). Never run a raw `git commit`.

## File Structure

| File | Responsibility |
|---|---|
| `app/core/common/app_types_constants.py` (modify) | `DatasetLocationType` |
| `app/core/dao/impl/models.py` (modify) | the four table classes |
| `alembic/versions/0005_create_admin_catalog.py` (create) | the four tables, constraints and indexes |
| `alembic/versions/0006_seed_admin_catalog.py` (create) | the seed rows |
| `app/core/common/dtos/dataset_dtos.py`, `mio_dtos.py`, `dataset_location_dtos.py`, `mio_dataset_dtos.py` (create) | Record, Req, Resp, Ctx of each table |
| `app/core/dao/dataset_dao.py`, `mio_dao.py`, `dataset_location_dao.py`, `mio_dataset_dao.py` (create) | the four interfaces |
| `app/core/dao/impl/sqlalchemy_dataset_dao.py`, `sqlalchemy_mio_dao.py`, `sqlalchemy_dataset_location_dao.py`, `sqlalchemy_mio_dataset_dao.py` (create) | the four implementations |
| `app/core/dao/objects_factory.py` (modify) | `get_dataset_dao()`, `get_mio_dao()`, `get_dataset_location_dao()`, `get_mio_dataset_dao()` |
| `tests/test_app_types_constants.py`, `tests/test_schema.py`, `tests/test_singletons.py`, `tests/test_postgres.py` (modify) | tests |
| `tests/test_dataset_dao.py`, `tests/test_mio_dao.py`, `tests/test_dataset_location_dao.py`, `tests/test_mio_dataset_dao.py`, `tests/test_catalog_flow.py` (create) | tests |
| `DESIGN.md` (modify) | marks the catalog as built in #86 |

---

### Task 1: `DatasetLocationType`

**Files:**
- Modify: `app/core/common/app_types_constants.py`
- Test: `tests/test_app_types_constants.py`

**Interfaces:**
- Produces: `DatasetLocationType(AppTypeEnum)` with members `LOCAL`, `HTTP`, `GITHUB`, `S3`, `AZURE_BLOB`, `GCS`, `GOOGLE_DRIVE`, `FTP`; `DatasetLocationType.values()` returns the strings.

- [ ] **Step 1: Write the failing test**

In `tests/test_app_types_constants.py` change the import line to
`from app.core.common.app_types_constants import AppTypeEnum, DatasetLocationType, EngineType, ExecStatus` and append:

```python
def test_dataset_location_type_values_are_the_short_codes():
    assert DatasetLocationType.values() == [
        "local",
        "http",
        "github",
        "s3",
        "azure_blob",
        "gcs",
        "google_drive",
        "ftp",
    ]
    assert DatasetLocationType.LOCAL == "local"
    assert "dropbox" not in DatasetLocationType.values()
    assert issubclass(DatasetLocationType, AppTypeEnum)
```

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_app_types_constants.py -v`
Expected: FAIL with `ImportError: cannot import name 'DatasetLocationType'`.

- [ ] **Step 3: Implement**

In `app/core/common/app_types_constants.py`, change the module docstring's second line to `Add the next list (statuses, ...) here as one more subclass.` and add this class after `ExecStatus` and its `_EXEC_STATUS_MOVES` dict (end of file):

```python


class DatasetLocationType(AppTypeEnum):
    """Where a dataset can be read from or written to (D49, D57). The workflows interpret the code, the API does not."""

    LOCAL = "local"
    HTTP = "http"
    GITHUB = "github"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    GOOGLE_DRIVE = "google_drive"
    FTP = "ftp"
```

- [ ] **Step 4: Run it and see it pass**

Run: `uv run pytest tests/test_app_types_constants.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 86` with summary `DatasetLocationType` and files `app/core/common/app_types_constants.py tests/test_app_types_constants.py`.

---

### Task 2: the four tables (models and migration `0005`)

**Files:**
- Modify: `app/core/dao/impl/models.py`
- Create: `alembic/versions/0005_create_admin_catalog.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `DatasetModel`, `DatasetLocationModel`, `MioModel`, `MioDatasetModel` in `app.core.dao.impl.models` with the columns below; the tables exist after `alembic upgrade head`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_schema.py` (also add `import pytest` at the top, below `import sqlite3`):

```python
def _columns(db, table):
    return {r[1]: (r[2], r[3]) for r in db.execute(f"pragma table_info({table})")}  # name: (type, not null)


def _table_sql(db, table):
    return db.execute("select sql from sqlite_master where name = ?", (table,)).fetchone()[0]


def test_catalog_tables_are_in_the_admin_schema_with_the_expected_columns(data_dir):
    with _admin_db(data_dir) as db:
        datasets = _columns(db, "datasets")
        locations = _columns(db, "datasets_location")
        mios = _columns(db, "mios")
        links = _columns(db, "mios_datasets")
    assert datasets == {
        "id": ("VARCHAR(36)", 1),
        "name": ("VARCHAR(100)", 1),
        "code": ("VARCHAR(15)", 1),
        "description": ("TEXT", 0),
        "created_at": ("DATETIME", 1),
        "updated_at": ("DATETIME", 1),
    }
    assert locations == {
        "id": ("VARCHAR(36)", 1),
        "dataset_id": ("VARCHAR(36)", 1),
        "location_type": ("VARCHAR(32)", 1),
        "path": ("VARCHAR(1000)", 0),
        "local_env_var_name": ("VARCHAR(64)", 0),
        "credentials_ref": ("VARCHAR(100)", 0),
        "description": ("TEXT", 0),
        "created_at": ("DATETIME", 1),
        "updated_at": ("DATETIME", 1),
    }
    assert mios == {
        "id": ("VARCHAR(36)", 1),
        "name": ("VARCHAR(100)", 1),
        "description": ("TEXT", 0),
        "created_at": ("DATETIME", 1),
        "updated_at": ("DATETIME", 1),
    }
    assert links == {
        "id": ("VARCHAR(36)", 1),
        "mio_id": ("VARCHAR(36)", 1),
        "dataset_id": ("VARCHAR(36)", 1),
        "dataset_location_id": ("VARCHAR(36)", 1),
        "created_at": ("DATETIME", 1),
    }


def test_catalog_tables_have_their_unique_constraints_and_indexes_and_no_foreign_keys(data_dir):
    with _admin_db(data_dir) as db:
        assert "uq_datasets_name" in _table_sql(db, "datasets")
        assert "uq_datasets_code" in _table_sql(db, "datasets")
        assert "uq_mios_name" in _table_sql(db, "mios")
        assert "uq_datasets_location_dataset_type_path" in _table_sql(db, "datasets_location")
        assert "uq_datasets_location_dataset_env_var" in _table_sql(db, "datasets_location")
        assert "ck_datasets_location_path_xor_env" in _table_sql(db, "datasets_location")
        assert "uq_mios_datasets_mio_dataset" in _table_sql(db, "mios_datasets")
        assert "ix_datasets_location_dataset_id" in {r[1] for r in db.execute("pragma index_list(datasets_location)")}
        assert "ix_mios_datasets_mio_id" in {r[1] for r in db.execute("pragma index_list(mios_datasets)")}
        for table in ("datasets", "datasets_location", "mios", "mios_datasets"):
            assert db.execute(f"pragma foreign_key_list({table})").fetchall() == [], table


@pytest.mark.parametrize("path, env_var", [("a/path", "SOME_NAME"), (None, None)])
def test_a_location_with_both_or_neither_of_path_and_env_var_name_is_rejected_by_the_database(data_dir, path, env_var):
    with _admin_db(data_dir) as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "insert into datasets_location (id, dataset_id, location_type, path, local_env_var_name, created_at,"
                " updated_at) values ('x', 'd', 'local', ?, ?, '2026-01-01', '2026-01-01')",
                (path, env_var),
            )


def test_the_database_rejects_a_second_link_of_the_same_mio_and_dataset(data_dir):
    sql = (
        "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
        " values (?, 'm', 'd', 'l', '2026-01-01')"
    )
    with _admin_db(data_dir) as db:
        db.execute(sql, ("one",))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(sql, ("two",))


def test_migration_0005_runs_down_and_up(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    tables = ("datasets", "datasets_location", "mios", "mios_datasets")
    command.downgrade(config, "0004")
    with _admin_db(data_dir) as db:
        for table in tables:
            assert db.execute("select name from sqlite_master where name = ?", (table,)).fetchall() == [], table
        assert db.execute("select name from sqlite_master where name = 'app_workflows_exec_log'").fetchall() != []
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        for table in tables:
            assert db.execute("select name from sqlite_master where name = ?", (table,)).fetchall() != [], table
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_schema.py -v`
Expected: the five new tests FAIL (no such table `datasets`...).

- [ ] **Step 3: Add the models**

In `app/core/dao/impl/models.py` change the sqlalchemy import to
`from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Index, String, Text, UniqueConstraint, true` and append at the end of the file:

```python


class DatasetModel(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("name", name="uq_datasets_name"),
        UniqueConstraint("code", name="uq_datasets_code"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # The short code builds the local env var name LOCAL_DATA_PATH_<code> (D57).
    code: Mapped[str] = mapped_column(String(15), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DatasetLocationModel(Base):
    __tablename__ = "datasets_location"
    __table_args__ = (
        UniqueConstraint("dataset_id", "location_type", "path", name="uq_datasets_location_dataset_type_path"),
        UniqueConstraint("dataset_id", "local_env_var_name", name="uq_datasets_location_dataset_env_var"),
        CheckConstraint(
            "(path IS NOT NULL AND local_env_var_name IS NULL) OR (path IS NULL AND local_env_var_name IS NOT NULL)",
            name="ck_datasets_location_path_xor_env",
        ),
        Index("ix_datasets_location_dataset_id", "dataset_id"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # No foreign key (D57): the DAOs keep the parent rule.
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    location_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # A literal path or URL, or NULL when local_env_var_name is set (exactly one of the two).
    path: Mapped[str | None] = mapped_column(String(1000))
    # Only the NAME of an environment variable, only for type "local". Never a value.
    local_env_var_name: Mapped[str | None] = mapped_column(String(64))
    # A name that points to a secret held elsewhere. Never the secret.
    credentials_ref: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MioModel(Base):
    __tablename__ = "mios"
    __table_args__ = (
        UniqueConstraint("name", name="uq_mios_name"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # The name and description are labels for people. No code reads them to choose data (D57).
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MioDatasetModel(Base):
    __tablename__ = "mios_datasets"
    __table_args__ = (
        UniqueConstraint("mio_id", "dataset_id", name="uq_mios_datasets_mio_dataset"),
        Index("ix_mios_datasets_mio_id", "mio_id"),
        {"schema": SCHEMA_ADMIN},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mio_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # The chosen location of that dataset for that MIO. Many MIOs may choose the same one.
    dataset_location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 4: Add the migration**

Create `alembic/versions/0005_create_admin_catalog.py`:

```python
"""create the catalog tables in the admin schema: datasets, datasets_location, mios and mios_datasets

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"  # created by alembic/env.py (ensure_schemas) before any migration runs


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(15), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_datasets_name"),
        sa.UniqueConstraint("code", name="uq_datasets_code"),
        schema=SCHEMA,
    )
    op.create_table(
        "datasets_location",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),  # no foreign key on purpose (D57)
        sa.Column("location_type", sa.String(32), nullable=False),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("local_env_var_name", sa.String(64), nullable=True),
        sa.Column("credentials_ref", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "location_type", "path", name="uq_datasets_location_dataset_type_path"),
        sa.UniqueConstraint("dataset_id", "local_env_var_name", name="uq_datasets_location_dataset_env_var"),
        sa.CheckConstraint(
            "(path IS NOT NULL AND local_env_var_name IS NULL) OR (path IS NULL AND local_env_var_name IS NOT NULL)",
            name="ck_datasets_location_path_xor_env",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_datasets_location_dataset_id", "datasets_location", ["dataset_id"], schema=SCHEMA)
    op.create_table(
        "mios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_mios_name"),
        schema=SCHEMA,
    )
    op.create_table(
        "mios_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mio_id", sa.String(36), nullable=False),  # no foreign keys on purpose (D57)
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("dataset_location_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mio_id", "dataset_id", name="uq_mios_datasets_mio_dataset"),
        schema=SCHEMA,
    )
    op.create_index("ix_mios_datasets_mio_id", "mios_datasets", ["mio_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_mios_datasets_mio_id", table_name="mios_datasets", schema=SCHEMA)
    op.drop_table("mios_datasets", schema=SCHEMA)
    op.drop_table("mios", schema=SCHEMA)
    op.drop_index("ix_datasets_location_dataset_id", table_name="datasets_location", schema=SCHEMA)
    op.drop_table("datasets_location", schema=SCHEMA)
    op.drop_table("datasets", schema=SCHEMA)
```

- [ ] **Step 5: Run them and see them pass**

Run: `uv run pytest tests/test_schema.py -v && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 86` with summary `catalog tables and migration 0005` and files `app/core/dao/impl/models.py alembic/versions/0005_create_admin_catalog.py tests/test_schema.py`.

---

### Task 3: the seed (migration `0006`)

**Files:**
- Create: `alembic/versions/0006_seed_admin_catalog.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces after `alembic upgrade head`: dataset `cfpb_consumer_complaints` (code `CFPB`); two locations of it (`http` with the CFPB URL, `local` with env var name `LOCAL_DATA_PATH_CFPB`); four MIOs "Customer complaints 3|6|9|12 months 2026"; four `mios_datasets` rows linking each MIO to that dataset and its `http` location.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_schema.py`:

```python
HTTP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
SEED_MIO_NAMES = [f"Customer complaints {months} months 2026" for months in (3, 6, 9, 12)]


def test_the_catalog_seed_is_present(data_dir):
    with _admin_db(data_dir) as db:
        assert db.execute("select code, name from datasets").fetchall() == [("CFPB", "cfpb_consumer_complaints")]
        assert db.execute(
            "select location_type, path, local_env_var_name, credentials_ref from datasets_location order by location_type"
        ).fetchall() == [
            ("http", HTTP_URL, None, None),
            ("local", None, "LOCAL_DATA_PATH_CFPB", None),
        ]
        assert [r[0] for r in db.execute("select name from mios order by name")] == sorted(SEED_MIO_NAMES)
        http_id = db.execute("select id from datasets_location where location_type = 'http'").fetchone()[0]
        dataset_id = db.execute("select id from datasets").fetchone()[0]
        links = db.execute("select mio_id, dataset_id, dataset_location_id from mios_datasets").fetchall()
    assert len(links) == 4 and len({link[0] for link in links}) == 4
    assert {(link[1], link[2]) for link in links} == {(dataset_id, http_id)}


def test_the_seeded_ids_and_times_are_fixed_and_utc(data_dir):
    with _admin_db(data_dir) as db:
        assert db.execute("select id from datasets").fetchone()[0] == "5187ad0c-d8ed-56ac-829d-e49313c16dbf"
        assert db.execute("select created_at from datasets").fetchone()[0].startswith("2026-11-14")


def test_migration_0006_removes_exactly_the_seed_on_the_way_down_and_restores_it(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into datasets (id, name, code, created_at, updated_at)"
            " values ('mine', 't_mine', 'MINE', '2026-01-01', '2026-01-01')"
        )
    command.downgrade(config, "0005")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from datasets").fetchall() == [("t_mine",)]
        for table in ("datasets_location", "mios", "mios_datasets"):
            assert db.execute(f"select count(*) from {table}").fetchone()[0] == 0, table
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert sorted(r[0] for r in db.execute("select name from datasets")) == ["cfpb_consumer_complaints", "t_mine"]
        assert db.execute("select count(*) from mios").fetchone()[0] == 4
```

Also edit `test_migration_0005_runs_down_and_up` is unaffected (downgrade to `0004` runs `0006` down first).

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_schema.py -k "seed or 0006" -v`
Expected: FAIL (the seed query returns no rows; `downgrade` to `0005` finds nothing to remove).

- [ ] **Step 3: Add the migration**

Create `alembic/versions/0006_seed_admin_catalog.py`:

```python
"""seed the admin catalog: the CFPB dataset, its two locations and four labelled MIOs

Only data that is the same in every environment is seeded. The local location holds only the NAME of the
environment variable that each environment sets; no machine path is stored (D57).

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "consumer_comp_admin_db"
NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)
HTTP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"

# Fixed ids (uuid5 of "ccaa/m02-0036/<name>") so a downgrade removes exactly these rows.
DATASET_ID = "5187ad0c-d8ed-56ac-829d-e49313c16dbf"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"
MIOS = (  # (mio id, mios_datasets id, months)
    ("a10fbfe0-ac03-5f3f-8d20-5132d470b03a", "f4baf6a8-1b8c-5145-b016-9a870bdecd6f", 3),
    ("b0f8bb64-be6b-5773-9f4c-3552ca36dc37", "012a8fd8-3f34-5843-b0ca-f4cf42f070a4", 6),
    ("f34fa9f1-e361-5fc0-98e0-f557bb561176", "47081de5-5db8-5c50-8b9a-6597d5624a84", 9),
    ("eb33e86c-5972-5d25-95aa-87625bec004d", "47fa4276-bc79-5e7b-a961-c33016e56199", 12),
)

_when = sa.DateTime(timezone=True)
datasets = sa.table(
    "datasets",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("code", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
locations = sa.table(
    "datasets_location",
    sa.column("id", sa.String),
    sa.column("dataset_id", sa.String),
    sa.column("location_type", sa.String),
    sa.column("path", sa.String),
    sa.column("local_env_var_name", sa.String),
    sa.column("credentials_ref", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
mios = sa.table(
    "mios",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("created_at", _when),
    sa.column("updated_at", _when),
    schema=SCHEMA,
)
mios_datasets = sa.table(
    "mios_datasets",
    sa.column("id", sa.String),
    sa.column("mio_id", sa.String),
    sa.column("dataset_id", sa.String),
    sa.column("dataset_location_id", sa.String),
    sa.column("created_at", _when),
    schema=SCHEMA,
)


def upgrade() -> None:
    op.bulk_insert(
        datasets,
        [
            {
                "id": DATASET_ID,
                "name": "cfpb_consumer_complaints",
                "code": "CFPB",
                "description": "The full CFPB Consumer Complaint Database file",
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
    )
    op.bulk_insert(
        locations,
        [
            {
                "id": HTTP_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "http",
                "path": HTTP_URL,
                "local_env_var_name": None,
                "credentials_ref": None,
                "description": "The public download of the CFPB file",
                "created_at": NOW,
                "updated_at": NOW,
            },
            {
                "id": LOCAL_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "local",
                "path": None,
                "local_env_var_name": "LOCAL_DATA_PATH_CFPB",
                "credentials_ref": None,
                "description": "Where the file is kept; each environment sets the variable",
                "created_at": NOW,
                "updated_at": NOW,
            },
        ],
    )
    op.bulk_insert(
        mios,
        [
            {
                "id": mio_id,
                "name": f"Customer complaints {months} months 2026",
                "description": "A label only. The data is what mios_datasets links.",
                "created_at": NOW,
                "updated_at": NOW,
            }
            for mio_id, _link_id, months in MIOS
        ],
    )
    op.bulk_insert(
        mios_datasets,
        [
            {
                "id": link_id,
                "mio_id": mio_id,
                "dataset_id": DATASET_ID,
                "dataset_location_id": HTTP_LOCATION_ID,
                "created_at": NOW,
            }
            for mio_id, link_id, _months in MIOS
        ],
    )


def downgrade() -> None:
    op.execute(sa.delete(mios_datasets).where(mios_datasets.c.id.in_([link_id for _m, link_id, _n in MIOS])))
    op.execute(sa.delete(mios).where(mios.c.id.in_([mio_id for mio_id, _l, _n in MIOS])))
    op.execute(sa.delete(locations).where(locations.c.id.in_([HTTP_LOCATION_ID, LOCAL_LOCATION_ID])))
    op.execute(sa.delete(datasets).where(datasets.c.id == DATASET_ID))
```

- [ ] **Step 4: Run them and see them pass**

Run: `uv run pytest tests/test_schema.py -v && uv run lint-imports`
Expected: all PASS (including `test_migration_0005_runs_down_and_up`, which now also runs the seed down and up).

- [ ] **Step 5: Commit**

Run `/ccaa-commit-push 86` with summary `seed the catalog (migration 0006)` and files `alembic/versions/0006_seed_admin_catalog.py tests/test_schema.py`.

---

### Task 4: `DatasetDao`

**Files:**
- Create: `app/core/common/dtos/dataset_dtos.py`, `app/core/dao/dataset_dao.py`, `app/core/dao/impl/sqlalchemy_dataset_dao.py`
- Modify: `app/core/dao/objects_factory.py`, `tests/test_singletons.py`
- Test: `tests/test_dataset_dao.py`

**Interfaces:**
- Produces: `DatasetReq(id, name, code, description)`, `DatasetResp(records: list[DatasetRecord])`, `DatasetCtx(transaction, req, resp)`, `DatasetRecord(id, name, code, description, created_at, updated_at)`; `DatasetDao.create/get/list/update/delete(ctx) -> int`; `DaoObjectsFactory.get_dataset_dao() -> DatasetDao`; module function `sqlalchemy_dataset_dao._taken_query(req: DatasetReq) -> Select` (tests replace it to simulate a race).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dataset_dao.py`:

```python
import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_dataset_dao as dao_impl
from app.core.dao.impl.models import DatasetModel
from app.core.dao.objects_factory import DaoObjectsFactory

STAMP = "2026-01-01 00:00:00"


def _ctx(**fields) -> DatasetCtx:
    return DatasetCtx(req=DatasetReq(**fields))


def _create(dao, name="t_one", code="T1", **more) -> DatasetCtx:
    ctx = _ctx(name=name, code=code, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _admin_db(data_dir):
    return sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite")


def _add_location(data_dir, dataset_id, path=None, env_var=None):
    """A child row written directly: the location DAO comes in a later task."""
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into datasets_location (id, dataset_id, location_type, path, local_env_var_name, created_at,"
            " updated_at) values (?, ?, ?, ?, ?, ?, ?)",
            (f"loc-{dataset_id}-{env_var or path}", dataset_id, "local" if env_var else "http", path, env_var, STAMP, STAMP),
        )


def _add_link(data_dir, dataset_id):
    with _admin_db(data_dir) as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, 'some-mio', ?, 'some-location', ?)",
            (f"link-{dataset_id}", dataset_id, STAMP),
        )


def _mine(dao) -> list:
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    return [r.name for r in listed.resp.records if r.name.lower().startswith("t_")]


def test_create_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao, name="  t_one  ", description="about").resp.records[0]
    assert len(row.id) == 36
    assert (row.name, row.code, row.description) == ("t_one", "T1", "about")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_create_accepts_the_longest_name_and_code(data_dir):
    row = _create(DaoObjectsFactory.get_dataset_dao(), name="n" * 100, code="A" * 14 + "9").resp.records[0]
    assert len(row.name) == 100 and len(row.code) == 15


@pytest.mark.parametrize(
    "fields",
    [
        dict(name=None, code="T1"),
        dict(name="   ", code="T1"),
        dict(name="n" * 101, code="T1"),
        dict(name="t_x", code=None),
        dict(name="t_x", code=""),
        dict(name="t_x", code="abc"),
        dict(name="t_x", code="A B"),
        dict(name="t_x", code="A_B"),
        dict(name="t_x", code="A" * 16),
        dict(name="t_x", code=5),
    ],
)
def test_create_rejects_bad_input(data_dir, fields):
    assert DaoObjectsFactory.get_dataset_dao().create(_ctx(**fields)) == INVALID_INPUT


def test_a_name_or_a_code_that_is_taken_is_a_conflict_and_names_are_trimmed_and_case_sensitive(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_one", code="T1")
    assert dao.create(_ctx(name=" t_one ", code="T2")) == CONFLICT
    assert dao.create(_ctx(name="t_two", code="T1")) == CONFLICT
    assert dao.create(_ctx(name="T_ONE", code="T3")) == SUCCESS  # a different case is a different name
    assert sorted(_mine(dao)) == ["T_ONE", "t_one"]


def test_get_by_id_or_by_name_and_the_id_wins(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    one = _create(dao, name="t_one", code="T1").resp.records[0]
    two = _create(dao, name="t_two", code="T2").resp.records[0]
    by_id, by_name, both = _ctx(id=one.id), _ctx(name=" t_two "), _ctx(id=one.id, name="t_two")
    assert dao.get(by_id) == SUCCESS and by_id.resp.records[0].id == one.id
    assert dao.get(by_name) == SUCCESS and by_name.resp.records[0].id == two.id
    assert dao.get(both) == SUCCESS and both.resp.records[0].id == one.id
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx(name="nope")) == NOT_FOUND


def test_list_is_ordered_by_name_and_includes_the_seed(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_b", code="T2")
    _create(dao, name="t_a", code="T1")
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    names = [r.name for r in listed.resp.records]
    assert names == sorted(names)
    assert "cfpb_consumer_complaints" in names
    assert _mine(dao) == ["t_a", "t_b"]


def test_update_changes_only_the_given_fields(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao, description="before").resp.records[0]
    described = _ctx(id=row.id, description="after")
    assert dao.update(described) == SUCCESS
    new = described.resp.records[0]
    assert (new.name, new.code, new.description) == ("t_one", "T1", "after")
    assert new.created_at == row.created_at and new.updated_at >= row.updated_at
    renamed = _ctx(id=row.id, name="  t_renamed ", code="T2")
    assert dao.update(renamed) == SUCCESS
    assert (renamed.resp.records[0].name, renamed.resp.records[0].code) == ("t_renamed", "T2")
    assert renamed.resp.records[0].description == "after"
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS  # its own name is not a conflict


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    one = _create(dao, name="t_one", code="T1").resp.records[0]
    _create(dao, name="t_two", code="T2")
    assert dao.update(_ctx(name="x")) == INVALID_INPUT
    assert dao.update(_ctx(id="nope", name="x")) == NOT_FOUND
    assert dao.update(_ctx(id=one.id, name="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, code="abc")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="t_two")) == CONFLICT
    assert dao.update(_ctx(id=one.id, code="T2")) == CONFLICT


def test_the_code_cannot_change_while_a_location_holds_an_env_var_name_built_from_it(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao).resp.records[0]
    _add_location(data_dir, row.id, env_var="LOCAL_DATA_PATH_T1")
    assert dao.update(_ctx(id=row.id, code="T2")) == CONFLICT
    assert dao.update(_ctx(id=row.id, code="T1")) == SUCCESS  # the same code is not a change
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS
    plain = _create(dao, name="t_plain", code="T3").resp.records[0]
    _add_location(data_dir, plain.id, path="https://example.com/file")  # a path needs no code
    assert dao.update(_ctx(id=plain.id, code="T4")) == SUCCESS


def test_delete_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    row = _create(dao).resp.records[0]
    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT


def test_a_dataset_in_use_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    with_location = _create(dao, name="t_loc", code="T1").resp.records[0]
    with_link = _create(dao, name="t_link", code="T2").resp.records[0]
    _add_location(data_dir, with_location.id, path="https://example.com/file")
    _add_link(data_dir, with_link.id)
    assert dao.delete(_ctx(id=with_location.id)) == CONFLICT
    assert dao.delete(_ctx(id=with_link.id)) == CONFLICT
    assert _mine(dao) == ["t_link", "t_loc"]
    with _admin_db(data_dir) as db:
        db.execute("delete from datasets_location where dataset_id = ?", (with_location.id,))
        db.execute("delete from mios_datasets where dataset_id = ?", (with_link.id,))
    assert dao.delete(_ctx(id=with_location.id)) == SUCCESS
    assert dao.delete(_ctx(id=with_link.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    # Simulates the race: another writer inserts the same name or code after our SELECT, so only the constraint catches it.
    dao = DaoObjectsFactory.get_dataset_dao()
    _create(dao, name="t_taken", code="T1")
    other = _create(dao, name="t_other", code="T2").resp.records[0]
    monkeypatch.setattr(dao_impl, "_taken_query", lambda req: select(DatasetModel.id).where(false()))
    assert dao.create(_ctx(name="t_taken", code="T9")) == CONFLICT
    assert dao.create(_ctx(name="t_new", code="T1")) == CONFLICT
    assert dao.update(_ctx(id=other.id, name="t_taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, code="T1")) == CONFLICT
    assert _mine(dao) == ["t_other", "t_taken"]


def test_a_shared_transaction_can_be_rolled_back_or_committed(data_dir):
    dao = DaoObjectsFactory.get_dataset_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    gone = DatasetCtx(transaction=rolled_back, req=DatasetReq(name="t_gone", code="T1"))
    assert dao.create(gone) == SUCCESS
    assert dao.get(DatasetCtx(transaction=rolled_back, req=DatasetReq(name="t_gone"))) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert dao.get(_ctx(name="t_gone")) == NOT_FOUND

    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    assert dao.create(DatasetCtx(transaction=committed, req=DatasetReq(name="t_kept", code="T2"))) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == NOT_FOUND  # not visible outside before the commit
    assert transactions.commit(committed) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == SUCCESS
```

In `tests/test_singletons.py` add the imports
`from app.core.dao.dataset_dao import DatasetDao` and `from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao`,
add `(DaoObjectsFactory.get_dataset_dao, DatasetDao),` to the tuple in `test_factories_return_the_same_object_typed_as_the_interface`, and add `assert SqlAlchemyDatasetDao() is SqlAlchemyDatasetDao()` to `test_the_classes_themselves_are_singletons`.

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_dataset_dao.py tests/test_singletons.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'app.core.common.dtos.dataset_dtos'`.

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/dataset_dtos.py`:

```python
"""Ctx, Req and Resp for the datasets table (the catalog of datasets, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class DatasetRecord:
    id: str
    name: str
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetReq:
    """A field left as None means "not given". id (or, for get, name) identifies one row."""

    id: str | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None


@dataclass
class DatasetResp:
    records: list[DatasetRecord] = field(default_factory=list)


@dataclass
class DatasetCtx(TransactionalCtx):
    req: DatasetReq = field(default_factory=DatasetReq)
    resp: DatasetResp = field(default_factory=DatasetResp)
```

- [ ] **Step 4: Add the interface**

Create `app/core/dao/dataset_dao.py`:

```python
"""Interface of the DAO for the datasets table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_dtos import DatasetCtx
from app.core.common.singleton import SingletonMeta


class DatasetDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DatasetCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    Names are trimmed and case sensitive. The code is 1 to 15 characters of A-Z and 0-9 and builds the local env var
    name LOCAL_DATA_PATH_<code> (D57). A CONFLICT caused by two writers taking the same name or code at once comes
    from the database constraint; inside a shared transaction the session is then unusable and the owner must
    roll back."""

    @abstractmethod
    def create(self, ctx: DatasetCtx) -> int:
        """Needs req.name (up to 100 characters) and req.code. Optional: description. INVALID_INPUT for a missing or
        unacceptable field, CONFLICT if the name or the code is taken."""

    @abstractmethod
    def get(self, ctx: DatasetCtx) -> int:
        """Needs req.id or req.name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is no such
        row."""

    @abstractmethod
    def list(self, ctx: DatasetCtx) -> int:
        """Every dataset, ordered by name."""

    @abstractmethod
    def update(self, ctx: DatasetCtx) -> int:
        """Needs req.id. Changes the given name, code and description and sets updated_at. NOT_FOUND if there is no
        such row, INVALID_INPUT for an unacceptable field, CONFLICT if the new name or code belongs to another row, or
        if the code changes while a location of the dataset holds an env var name built from the old code."""

    @abstractmethod
    def delete(self, ctx: DatasetCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a location or a
        mios_datasets row still uses the dataset (no foreign key: this DAO keeps the rule, D57)."""
```

- [ ] **Step 5: Add the implementation**

Create `app/core/dao/impl/sqlalchemy_dataset_dao.py`:

```python
"""DatasetDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads DatasetLocationModel and MioDatasetModel to keep the in-use rules (no foreign keys, D57)."""

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetRecord, DatasetReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

NAME_MAX = 100
CODE_PATTERN = re.compile(r"[A-Z0-9]{1,15}")


def _to_record(row: DatasetModel) -> DatasetRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return DatasetRecord(
        id=row.id,
        name=row.name,
        code=row.code,
        description=row.description,
        created_at=created,
        updated_at=updated,
    )


def _name_of(req: DatasetReq) -> str | None:
    """The name without leading or trailing spaces. Names are case sensitive."""
    return None if req.name is None else req.name.strip()


def _has_invalid_field(req: DatasetReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    name = _name_of(req)
    if name is not None and (not name or len(name) > NAME_MAX):
        return True
    if req.code is not None and (not isinstance(req.code, str) or CODE_PATTERN.fullmatch(req.code) is None):
        return True
    return False


def _taken_query(req: DatasetReq) -> Select:
    """Ids of rows that already use the given name or the given code."""
    taken = []
    if _name_of(req) is not None:
        taken.append(DatasetModel.name == _name_of(req))
    if req.code is not None:
        taken.append(DatasetModel.code == req.code)
    return select(DatasetModel.id).where(or_(*taken))


class SqlAlchemyDatasetDao(DatasetDao):
    def create(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not (_name_of(req) and req.code) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.scalars(_taken_query(req)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = DatasetModel(
                    id=str(uuid4()),
                    name=_name_of(req),
                    code=req.code,
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name or code at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets create failed")
            return FAILURE

    def get(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if req.id:
                    row = session.get(DatasetModel, req.id)
                else:
                    row = session.scalars(select(DatasetModel).where(DatasetModel.name == _name_of(req))).first()
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("datasets get failed")
            return FAILURE

    def list(self, ctx: DatasetCtx) -> int:
        try:
            with unit_of_work(ctx) as session:
                query = select(DatasetModel).order_by(DatasetModel.name)
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("datasets list failed")
            return FAILURE

    def update(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                changed = DatasetReq(
                    name=_name_of(req) if _name_of(req) != row.name else None,
                    code=req.code if req.code != row.code else None,
                )
                if changed.name is not None or changed.code is not None:
                    if session.scalars(_taken_query(changed).where(DatasetModel.id != row.id)).first() is not None:
                        return CONFLICT
                if changed.code is not None:
                    holds_env_var = select(DatasetLocationModel.id).where(
                        DatasetLocationModel.dataset_id == row.id,
                        DatasetLocationModel.local_env_var_name.is_not(None),
                    )
                    if session.scalars(holds_env_var).first() is not None:
                        return CONFLICT
                if changed.name is not None:
                    row.name = changed.name
                if changed.code is not None:
                    row.code = changed.code
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name or code at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets update failed")
            return FAILURE

    def delete(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                has_location = select(DatasetLocationModel.id).where(DatasetLocationModel.dataset_id == row.id)
                has_link = select(MioDatasetModel.id).where(MioDatasetModel.dataset_id == row.id)
                if session.scalars(has_location).first() is not None or session.scalars(has_link).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("datasets delete failed")
            return FAILURE
```

Note for the race test: `_taken_query(changed)` is replaced by the test's lambda (it ignores its argument and returns a select with `where(false())`); `.where(DatasetModel.id != row.id)` is then added to that select, which is still valid.

- [ ] **Step 6: Register the singleton**

In `app/core/dao/objects_factory.py` add the import `from app.core.dao.dataset_dao import DatasetDao` (after the `app_wf_exec_log_dao` import, keeping alphabetical order with `data_ingest_dao`: put it after `data_ingest_dao`) and this method after `get_app_wf_exec_log_dao`:

```python
    @staticmethod
    def get_dataset_dao() -> DatasetDao:
        from app.core.dao.impl.sqlalchemy_dataset_dao import SqlAlchemyDatasetDao

        return SqlAlchemyDatasetDao()
```

- [ ] **Step 7: Run them and see them pass**

Run: `uv run pytest tests/test_dataset_dao.py tests/test_singletons.py tests/test_ctx_only_signatures.py -v && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 86` with summary `DatasetDao` and files `app/core/common/dtos/dataset_dtos.py app/core/dao/dataset_dao.py app/core/dao/impl/sqlalchemy_dataset_dao.py app/core/dao/objects_factory.py tests/test_dataset_dao.py tests/test_singletons.py`.

---

### Task 5: `MioDao`

**Files:**
- Create: `app/core/common/dtos/mio_dtos.py`, `app/core/dao/mio_dao.py`, `app/core/dao/impl/sqlalchemy_mio_dao.py`
- Modify: `app/core/dao/objects_factory.py`, `tests/test_singletons.py`
- Test: `tests/test_mio_dao.py`

**Interfaces:**
- Produces: `MioReq(id, name, description)`, `MioResp`, `MioCtx`, `MioRecord(id, name, description, created_at, updated_at)`; `MioDao.create/get/list/update/delete(ctx) -> int`; `DaoObjectsFactory.get_mio_dao() -> MioDao`; module function `sqlalchemy_mio_dao._taken_query(req: MioReq) -> Select`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mio_dao.py`:

```python
import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_dao as dao_impl
from app.core.dao.impl.models import MioModel
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> MioCtx:
    return MioCtx(req=MioReq(**fields))


def _create(dao, name="t_one", **more) -> MioCtx:
    ctx = _ctx(name=name, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _add_link(data_dir, mio_id):
    """A link written directly: the link DAO comes in a later task."""
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, ?, 'some-dataset', 'some-location', '2026-01-01 00:00:00')",
            (f"link-{mio_id}", mio_id),
        )


def _mine(dao) -> list:
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    return [r.name for r in listed.resp.records if r.name.lower().startswith("t_")]


def test_create_returns_the_row(data_dir):
    row = _create(DaoObjectsFactory.get_mio_dao(), name="  t_one  ", description="about").resp.records[0]
    assert len(row.id) == 36
    assert (row.name, row.description) == ("t_one", "about")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_create_accepts_a_100_character_name(data_dir):
    assert len(_create(DaoObjectsFactory.get_mio_dao(), name="n" * 100).resp.records[0].name) == 100


@pytest.mark.parametrize("name", [None, "", "   ", "n" * 101])
def test_create_rejects_a_missing_or_unacceptable_name(data_dir, name):
    assert DaoObjectsFactory.get_mio_dao().create(_ctx(name=name)) == INVALID_INPUT


def test_names_are_trimmed_and_case_sensitive(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_one")
    assert dao.create(_ctx(name=" t_one ")) == CONFLICT
    assert dao.create(_ctx(name="T_ONE")) == SUCCESS
    assert sorted(_mine(dao)) == ["T_ONE", "t_one"]


def test_get_by_id_or_by_name_and_the_id_wins(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    one = _create(dao, name="t_one").resp.records[0]
    two = _create(dao, name="t_two").resp.records[0]
    by_id, by_name, both = _ctx(id=one.id), _ctx(name=" t_two "), _ctx(id=one.id, name="t_two")
    assert dao.get(by_id) == SUCCESS and by_id.resp.records[0].id == one.id
    assert dao.get(by_name) == SUCCESS and by_name.resp.records[0].id == two.id
    assert dao.get(both) == SUCCESS and both.resp.records[0].id == one.id
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx(name="nope")) == NOT_FOUND


def test_list_is_ordered_by_name_and_includes_the_four_seeded_mios(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_b")
    _create(dao, name="t_a")
    listed = _ctx()
    assert dao.list(listed) == SUCCESS
    names = [r.name for r in listed.resp.records]
    assert names == sorted(names)
    assert sum(name.startswith("Customer complaints ") for name in names) == 4
    assert _mine(dao) == ["t_a", "t_b"]


def test_update_changes_only_the_given_fields(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao, description="before").resp.records[0]
    described = _ctx(id=row.id, description="after")
    assert dao.update(described) == SUCCESS
    assert (described.resp.records[0].name, described.resp.records[0].description) == ("t_one", "after")
    assert described.resp.records[0].created_at == row.created_at
    renamed = _ctx(id=row.id, name="  t_renamed ")
    assert dao.update(renamed) == SUCCESS and renamed.resp.records[0].name == "t_renamed"
    assert renamed.resp.records[0].description == "after"
    assert dao.update(_ctx(id=row.id, name="t_renamed")) == SUCCESS  # its own name is not a conflict


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    one = _create(dao, name="t_one").resp.records[0]
    _create(dao, name="t_two")
    assert dao.update(_ctx(name="x")) == INVALID_INPUT
    assert dao.update(_ctx(id="nope", name="x")) == NOT_FOUND
    assert dao.update(_ctx(id=one.id, name="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="n" * 101)) == INVALID_INPUT
    assert dao.update(_ctx(id=one.id, name="t_two")) == CONFLICT


def test_delete_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao).resp.records[0]
    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT


def test_a_mio_with_a_link_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    row = _create(dao).resp.records[0]
    _add_link(data_dir, row.id)
    assert dao.delete(_ctx(id=row.id)) == CONFLICT
    assert dao.get(_ctx(id=row.id)) == SUCCESS
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute("delete from mios_datasets where mio_id = ?", (row.id,))
    assert dao.delete(_ctx(id=row.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_mio_dao()
    _create(dao, name="t_taken")
    other = _create(dao, name="t_other").resp.records[0]
    monkeypatch.setattr(dao_impl, "_taken_query", lambda req: select(MioModel.id).where(false()))
    assert dao.create(_ctx(name="t_taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, name="t_taken")) == CONFLICT
    assert sorted(_mine(dao)) == ["t_other", "t_taken"]


def test_a_shared_transaction_can_be_rolled_back_or_committed(data_dir):
    dao = DaoObjectsFactory.get_mio_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    rolled_back = TransactionCtx()
    assert transactions.begin(rolled_back) == SUCCESS
    assert dao.create(MioCtx(transaction=rolled_back, req=MioReq(name="t_gone"))) == SUCCESS
    assert dao.get(MioCtx(transaction=rolled_back, req=MioReq(name="t_gone"))) == SUCCESS
    assert transactions.rollback(rolled_back) == SUCCESS
    assert dao.get(_ctx(name="t_gone")) == NOT_FOUND

    committed = TransactionCtx()
    assert transactions.begin(committed) == SUCCESS
    assert dao.create(MioCtx(transaction=committed, req=MioReq(name="t_kept"))) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == NOT_FOUND
    assert transactions.commit(committed) == SUCCESS
    assert dao.get(_ctx(name="t_kept")) == SUCCESS
```

In `tests/test_singletons.py` add imports `from app.core.dao.mio_dao import MioDao` and `from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao`, add `(DaoObjectsFactory.get_mio_dao, MioDao),` to the tuple, and `assert SqlAlchemyMioDao() is SqlAlchemyMioDao()` to the classes test.

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_mio_dao.py tests/test_singletons.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'app.core.common.dtos.mio_dtos'`.

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/mio_dtos.py`:

```python
"""Ctx, Req and Resp for the mios table (managed information objects, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioRecord:
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class MioReq:
    """A field left as None means "not given". id (or, for get, name) identifies one row."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


@dataclass
class MioResp:
    records: list[MioRecord] = field(default_factory=list)


@dataclass
class MioCtx(TransactionalCtx):
    req: MioReq = field(default_factory=MioReq)
    resp: MioResp = field(default_factory=MioResp)
```

- [ ] **Step 4: Add the interface**

Create `app/core/dao/mio_dao.py`:

```python
"""Interface of the DAO for the mios table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_dtos import MioCtx
from app.core.common.singleton import SingletonMeta


class MioDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    Names are trimmed and case sensitive, and are labels for people: no code reads a name or a description to choose
    data (D57). The data of a MIO is what mios_datasets links."""

    @abstractmethod
    def create(self, ctx: MioCtx) -> int:
        """Needs req.name (up to 100 characters). Optional: description. INVALID_INPUT for a missing or unacceptable
        name, CONFLICT if the name is taken."""

    @abstractmethod
    def get(self, ctx: MioCtx) -> int:
        """Needs req.id or req.name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is no such
        row."""

    @abstractmethod
    def list(self, ctx: MioCtx) -> int:
        """Every MIO, ordered by name."""

    @abstractmethod
    def update(self, ctx: MioCtx) -> int:
        """Needs req.id. Changes the given name and description and sets updated_at. NOT_FOUND if there is no such
        row, INVALID_INPUT for an unacceptable name, CONFLICT if the new name belongs to another row."""

    @abstractmethod
    def delete(self, ctx: MioCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a mios_datasets
        row still links the MIO (no foreign key: this DAO keeps the rule, D57)."""
```

- [ ] **Step 5: Add the implementation**

Create `app/core/dao/impl/sqlalchemy_mio_dao.py`:

```python
"""MioDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioDatasetModel to keep the in-use rule (no foreign keys, D57)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.mio_dtos import MioCtx, MioRecord, MioReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import MioDatasetModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_dao import MioDao

log = logging.getLogger(__name__)

NAME_MAX = 100


def _to_record(row: MioModel) -> MioRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return MioRecord(id=row.id, name=row.name, description=row.description, created_at=created, updated_at=updated)


def _name_of(req: MioReq) -> str | None:
    """The name without leading or trailing spaces. Names are case sensitive."""
    return None if req.name is None else req.name.strip()


def _has_invalid_field(req: MioReq) -> bool:
    name = _name_of(req)
    return name is not None and (not name or len(name) > NAME_MAX)


def _taken_query(req: MioReq) -> Select:
    """Ids of rows that already use the given name."""
    return select(MioModel.id).where(MioModel.name == _name_of(req))


class SqlAlchemyMioDao(MioDao):
    def create(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not _name_of(req) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.scalars(_taken_query(req)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = MioModel(
                    id=str(uuid4()),
                    name=_name_of(req),
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios create failed")
            return FAILURE

    def get(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if req.id:
                    row = session.get(MioModel, req.id)
                else:
                    row = session.scalars(select(MioModel).where(MioModel.name == _name_of(req))).first()
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios get failed")
            return FAILURE

    def list(self, ctx: MioCtx) -> int:
        try:
            with unit_of_work(ctx) as session:
                query = select(MioModel).order_by(MioModel.name)
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios list failed")
            return FAILURE

    def update(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioModel, req.id)
                if row is None:
                    return NOT_FOUND
                new_name = _name_of(req) if _name_of(req) != row.name else None
                if new_name is not None:
                    if session.scalars(_taken_query(req).where(MioModel.id != row.id)).first() is not None:
                        return CONFLICT
                    row.name = new_name
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same name at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios update failed")
            return FAILURE

    def delete(self, ctx: MioCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioModel, req.id)
                if row is None:
                    return NOT_FOUND
                has_link = select(MioDatasetModel.id).where(MioDatasetModel.mio_id == row.id)
                if session.scalars(has_link).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios delete failed")
            return FAILURE
```

- [ ] **Step 6: Register the singleton**

In `app/core/dao/objects_factory.py` add `from app.core.dao.mio_dao import MioDao` (after the `data_ingest_dao`/`dataset_dao` imports, before `system_datasets_dao`) and this method after `get_dataset_dao`:

```python
    @staticmethod
    def get_mio_dao() -> MioDao:
        from app.core.dao.impl.sqlalchemy_mio_dao import SqlAlchemyMioDao

        return SqlAlchemyMioDao()
```

- [ ] **Step 7: Run them and see them pass**

Run: `uv run pytest tests/test_mio_dao.py tests/test_singletons.py tests/test_ctx_only_signatures.py -v && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.`

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 86` with summary `MioDao` and files `app/core/common/dtos/mio_dtos.py app/core/dao/mio_dao.py app/core/dao/impl/sqlalchemy_mio_dao.py app/core/dao/objects_factory.py tests/test_mio_dao.py tests/test_singletons.py`.

---

### Task 6: `DatasetLocationDao`

**Files:**
- Create: `app/core/common/dtos/dataset_location_dtos.py`, `app/core/dao/dataset_location_dao.py`, `app/core/dao/impl/sqlalchemy_dataset_location_dao.py`
- Modify: `app/core/dao/objects_factory.py`, `tests/test_singletons.py`
- Test: `tests/test_dataset_location_dao.py`

**Interfaces:**
- Consumes: `DatasetLocationType.values()` (Task 1); `DatasetModel`, `DatasetLocationModel`, `MioDatasetModel` (Task 2); `DatasetDao` through the factory in tests (Task 4).
- Produces: `DatasetLocationReq(id, dataset_id, location_type, path, local_env_var_name, credentials_ref, description)`, `DatasetLocationResp`, `DatasetLocationCtx`, `DatasetLocationRecord(id, dataset_id, location_type, path, local_env_var_name, credentials_ref, description, created_at, updated_at)`; `DatasetLocationDao.create/get/list/update/delete(ctx) -> int`; `DaoObjectsFactory.get_dataset_location_dao()`; module function `sqlalchemy_dataset_location_dao._same_place_query(merged: DatasetLocationReq) -> Select`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dataset_location_dao.py`:

```python
import sqlite3

import pytest
from sqlalchemy import false, select

from app.core.common.app_types_constants import DatasetLocationType
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_dataset_location_dao as dao_impl
from app.core.dao.impl.models import DatasetLocationModel
from app.core.dao.objects_factory import DaoObjectsFactory

URL = "https://example.com/file.csv"


def _dataset(name="t_ds", code="T1") -> str:
    ctx = DatasetCtx(req=DatasetReq(name=name, code=code))
    assert DaoObjectsFactory.get_dataset_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ctx(**fields) -> DatasetLocationCtx:
    return DatasetLocationCtx(req=DatasetLocationReq(**fields))


def _create(dao, dataset_id, location_type="http", path=URL, **more) -> DatasetLocationCtx:
    ctx = _ctx(dataset_id=dataset_id, location_type=location_type, path=path, **more)
    assert dao.create(ctx) == SUCCESS
    return ctx


def _add_link(data_dir, location_id):
    """A link written directly: the link DAO comes in a later task."""
    with sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite") as db:
        db.execute(
            "insert into mios_datasets (id, mio_id, dataset_id, dataset_location_id, created_at)"
            " values (?, 'some-mio', 'some-dataset', ?, '2026-01-01 00:00:00')",
            (f"link-{location_id}", location_id),
        )


def test_create_an_http_location_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    row = _create(dao, dataset_id, path="  " + URL + "  ", description="d", credentials_ref="aws_prod.key-1").resp.records[0]
    assert len(row.id) == 36
    assert (row.dataset_id, row.location_type, row.path) == (dataset_id, "http", URL)
    assert (row.local_env_var_name, row.credentials_ref, row.description) == (None, "aws_prod.key-1", "d")
    assert row.created_at.tzinfo is not None and row.created_at == row.updated_at


def test_a_local_location_has_a_path_or_an_env_var_name(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    with_path = _create(dao, dataset_id, location_type="local", path="/data/files").resp.records[0]
    assert (with_path.path, with_path.local_env_var_name) == ("/data/files", None)
    with_env = _create(dao, dataset_id, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1")
    assert (with_env.resp.records[0].path, with_env.resp.records[0].local_env_var_name) == (None, "LOCAL_DATA_PATH_T1")


@pytest.mark.parametrize("location_type", DatasetLocationType.values())
def test_every_location_type_is_accepted_with_a_path(data_dir, location_type):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    row = _create(dao, _dataset(), location_type=location_type, path="somewhere/else").resp.records[0]
    assert row.location_type == location_type


def test_create_rejects_the_wrong_shape(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    other_code = "LOCAL_DATA_PATH_T2"
    bad = [
        dict(location_type="local", path="/a", local_env_var_name="LOCAL_DATA_PATH_T1"),  # both
        dict(location_type="local"),  # neither
        dict(location_type="http", local_env_var_name="LOCAL_DATA_PATH_T1"),  # env var for a type that is not local
        dict(location_type="http"),  # a non-local type needs a path
        dict(location_type="local", local_env_var_name=other_code),  # the name is built from another dataset's code
        dict(location_type="local", local_env_var_name="LOCAL_DATA_PATH_"),
        dict(location_type="local", local_env_var_name="MY_PATH"),
        dict(location_type="dropbox", path="/a"),
        dict(location_type=None, path="/a"),
        dict(location_type="http", path="   "),
        dict(location_type="http", path="p" * 1001),
        dict(location_type="http", path=5),
    ]
    for fields in bad:
        assert dao.create(_ctx(dataset_id=dataset_id, **fields)) == INVALID_INPUT, fields
    assert dao.create(_ctx(location_type="http", path="/a")) == INVALID_INPUT  # no dataset_id
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path="p" * 1000)) == SUCCESS


def test_create_for_a_dataset_that_does_not_exist_is_not_found(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    assert dao.create(_ctx(dataset_id="nope", location_type="http", path=URL)) == NOT_FOUND


@pytest.mark.parametrize("credentials_ref", ["key=abc", "https://host/x", "a b", "", "x" * 101, "AKIA SECRET", "a/b", 5])
def test_a_credentials_reference_that_is_not_a_plain_name_is_rejected(data_dir, credentials_ref):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path=URL, credentials_ref=credentials_ref)) == INVALID_INPUT
    row = _create(dao, dataset_id).resp.records[0]
    assert dao.update(_ctx(id=row.id, credentials_ref=credentials_ref)) == INVALID_INPUT


def test_a_credentials_reference_of_100_characters_is_accepted(data_dir):
    assert _create(DaoObjectsFactory.get_dataset_location_dao(), _dataset(), credentials_ref="x" * 100).resp.records


def test_duplicates_are_conflicts(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    first, second = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    _create(dao, first)
    assert dao.create(_ctx(dataset_id=first, location_type="http", path=URL)) == CONFLICT
    assert dao.create(_ctx(dataset_id=first, location_type="ftp", path=URL)) == SUCCESS  # same path, other type
    assert dao.create(_ctx(dataset_id=second, location_type="http", path=URL)) == SUCCESS  # same path, other dataset
    _create(dao, first, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1")
    again = _ctx(dataset_id=first, location_type="local", local_env_var_name="LOCAL_DATA_PATH_T1")
    assert dao.create(again) == CONFLICT


def test_get_and_list_with_filters_and_a_fixed_order(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    mine, theirs = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    env = _create(dao, mine, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1").resp.records[0]
    ftp = _create(dao, mine, location_type="ftp", path="ftp://h/f").resp.records[0]
    http_b = _create(dao, mine, path="https://b").resp.records[0]
    http_a = _create(dao, mine, path="https://a").resp.records[0]
    _create(dao, theirs, path="https://c")

    everything = _ctx(dataset_id=mine)
    assert dao.list(everything) == SUCCESS
    assert [r.id for r in everything.resp.records] == [ftp.id, http_a.id, http_b.id, env.id]
    only_http = _ctx(dataset_id=mine, location_type="http")
    assert dao.list(only_http) == SUCCESS and [r.id for r in only_http.resp.records] == [http_a.id, http_b.id]
    all_http = _ctx(location_type="http")
    assert dao.list(all_http) == SUCCESS
    assert {r.dataset_id for r in all_http.resp.records} >= {mine, theirs}

    fetched = _ctx(id=ftp.id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].path == "ftp://h/f"
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND


def test_update_changes_the_given_fields_and_path_and_env_var_name_replace_each_other(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset(code="T1")
    row = _create(dao, dataset_id, location_type="local", path="/data").resp.records[0]

    to_env = _ctx(id=row.id, local_env_var_name="LOCAL_DATA_PATH_T1")
    assert dao.update(to_env) == SUCCESS
    assert (to_env.resp.records[0].path, to_env.resp.records[0].local_env_var_name) == (None, "LOCAL_DATA_PATH_T1")
    assert to_env.resp.records[0].created_at == row.created_at

    to_path = _ctx(id=row.id, path=" /elsewhere ", description="moved", credentials_ref="my_ref")
    assert dao.update(to_path) == SUCCESS
    new = to_path.resp.records[0]
    assert (new.path, new.local_env_var_name, new.description, new.credentials_ref) == ("/elsewhere", None, "moved", "my_ref")

    to_http = _ctx(id=row.id, location_type="http", path=URL)
    assert dao.update(to_http) == SUCCESS and to_http.resp.records[0].location_type == "http"


def test_update_errors(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id, other_dataset_id = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    local_env = _create(dao, dataset_id, location_type="local", path=None, local_env_var_name="LOCAL_DATA_PATH_T1").resp.records[0]
    http = _create(dao, dataset_id).resp.records[0]
    _create(dao, dataset_id, path="https://other")

    assert dao.update(_ctx(path="x")) == INVALID_INPUT  # no id
    assert dao.update(_ctx(id="nope", path="x")) == NOT_FOUND
    assert dao.update(_ctx(id=http.id, path="/a", local_env_var_name="LOCAL_DATA_PATH_T1")) == INVALID_INPUT  # both
    assert dao.update(_ctx(id=http.id, local_env_var_name="LOCAL_DATA_PATH_T1")) == INVALID_INPUT  # http cannot have one
    assert dao.update(_ctx(id=local_env.id, location_type="http")) == INVALID_INPUT  # http with no path
    assert dao.update(_ctx(id=local_env.id, local_env_var_name="LOCAL_DATA_PATH_T2")) == INVALID_INPUT  # another dataset's code
    assert dao.update(_ctx(id=http.id, location_type="dropbox")) == INVALID_INPUT
    assert dao.update(_ctx(id=http.id, path="   ")) == INVALID_INPUT
    assert dao.update(_ctx(id=http.id, dataset_id=other_dataset_id)) == INVALID_INPUT  # a location cannot move
    assert dao.update(_ctx(id=http.id, path="https://other")) == CONFLICT
    assert dao.update(_ctx(id=http.id, dataset_id=dataset_id, path=URL)) == SUCCESS  # itself is not a conflict
    still = _ctx(id=local_env.id)
    assert dao.get(still) == SUCCESS and still.resp.records[0].local_env_var_name == "LOCAL_DATA_PATH_T1"


def test_delete_returns_the_row_and_a_location_in_use_cannot_be_deleted(data_dir):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    free = _create(dao, dataset_id, path="https://free").resp.records[0]
    used = _create(dao, dataset_id, path="https://used").resp.records[0]
    _add_link(data_dir, used.id)

    deleted = _ctx(id=free.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == free.id
    assert dao.delete(_ctx(id=free.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    assert dao.delete(_ctx(id=used.id)) == CONFLICT
    assert dao.get(_ctx(id=used.id)) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_dataset_location_dao()
    dataset_id = _dataset()
    _create(dao, dataset_id, path="https://taken")
    other = _create(dao, dataset_id, path="https://other").resp.records[0]
    monkeypatch.setattr(dao_impl, "_same_place_query", lambda merged: select(DatasetLocationModel.id).where(false()))
    assert dao.create(_ctx(dataset_id=dataset_id, location_type="http", path="https://taken")) == CONFLICT
    assert dao.update(_ctx(id=other.id, path="https://taken")) == CONFLICT
    listed = _ctx(dataset_id=dataset_id)
    assert dao.list(listed) == SUCCESS and sorted(r.path for r in listed.resp.records) == ["https://other", "https://taken"]


def test_a_location_can_join_the_transaction_that_creates_its_dataset(data_dir):
    datasets = DaoObjectsFactory.get_dataset_dao()
    dao = DaoObjectsFactory.get_dataset_location_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()

    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    made = DatasetCtx(transaction=tx, req=DatasetReq(name="t_tx", code="T1"))
    assert datasets.create(made) == SUCCESS
    new = DatasetLocationCtx(
        transaction=tx,
        req=DatasetLocationReq(dataset_id=made.resp.records[0].id, location_type="http", path=URL),
    )
    assert dao.create(new) == SUCCESS  # it sees the dataset that is not committed yet
    assert transactions.rollback(tx) == SUCCESS
    assert datasets.get(DatasetCtx(req=DatasetReq(name="t_tx"))) == NOT_FOUND
    assert dao.get(_ctx(id=new.resp.records[0].id)) == NOT_FOUND
```

In `tests/test_singletons.py` add imports `from app.core.dao.dataset_location_dao import DatasetLocationDao` and `from app.core.dao.impl.sqlalchemy_dataset_location_dao import SqlAlchemyDatasetLocationDao`, add `(DaoObjectsFactory.get_dataset_location_dao, DatasetLocationDao),` to the tuple and `assert SqlAlchemyDatasetLocationDao() is SqlAlchemyDatasetLocationDao()` to the classes test.

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_dataset_location_dao.py tests/test_singletons.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'app.core.common.dtos.dataset_location_dtos'`.

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/dataset_location_dtos.py`:

```python
"""Ctx, Req and Resp for the datasets_location table (where a dataset lives, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class DatasetLocationRecord:
    id: str
    dataset_id: str
    location_type: str
    path: str | None
    local_env_var_name: str | None
    credentials_ref: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetLocationReq:
    """A field left as None means "not given". id identifies one row (get, update, delete)."""

    id: str | None = None
    dataset_id: str | None = None
    location_type: str | None = None
    path: str | None = None
    local_env_var_name: str | None = None
    credentials_ref: str | None = None
    description: str | None = None


@dataclass
class DatasetLocationResp:
    records: list[DatasetLocationRecord] = field(default_factory=list)


@dataclass
class DatasetLocationCtx(TransactionalCtx):
    req: DatasetLocationReq = field(default_factory=DatasetLocationReq)
    resp: DatasetLocationResp = field(default_factory=DatasetLocationResp)
```

- [ ] **Step 4: Add the interface**

Create `app/core/dao/dataset_location_dao.py`:

```python
"""Interface of the DAO for the datasets_location table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx
from app.core.common.singleton import SingletonMeta


class DatasetLocationDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DatasetLocationCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    A location has a path (a literal path or a URL) or a local_env_var_name, never both and never neither. The
    local_env_var_name is only allowed for the type "local", is only a NAME (never a value), and must be exactly
    LOCAL_DATA_PATH_ plus the code of the dataset. credentials_ref is a name (letters, digits, _ . -), never a
    secret. Types are the values of DatasetLocationType (D57)."""

    @abstractmethod
    def create(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.dataset_id, req.location_type and exactly one of req.path (up to 1000 characters after
        trimming) and req.local_env_var_name. Optional: credentials_ref, description. NOT_FOUND if the dataset does
        not exist, INVALID_INPUT for a missing or unacceptable field, CONFLICT if the dataset already has that type and
        path, or that env var name."""

    @abstractmethod
    def get(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: DatasetLocationCtx) -> int:
        """Optional filters: req.dataset_id, req.location_type. Ordered by location_type, rows with a path before
        rows without, path, id."""

    @abstractmethod
    def update(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. Changes the given location_type, path, local_env_var_name, credentials_ref and description
        and sets updated_at. Giving path clears local_env_var_name and giving local_env_var_name clears path; giving
        both is INVALID_INPUT. The resulting row must follow the rules above. A req.dataset_id that is not the row's
        own is INVALID_INPUT (a location does not move). NOT_FOUND if there is no such row, CONFLICT if the result
        equals another location of the dataset."""

    @abstractmethod
    def delete(self, ctx: DatasetLocationCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row, CONFLICT if a mios_datasets
        row chose this location (no foreign key: this DAO keeps the rule, D57)."""
```

- [ ] **Step 5: Add the implementation**

Create `app/core/dao/impl/sqlalchemy_dataset_location_dao.py`:

```python
"""DatasetLocationDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads DatasetModel and MioDatasetModel to keep the parent and in-use rules (no foreign keys, D57)."""

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.app_types_constants import DatasetLocationType
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationRecord, DatasetLocationReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_location_dao import DatasetLocationDao
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel
from app.core.dao.impl.unit_of_work import unit_of_work

log = logging.getLogger(__name__)

PATH_MAX = 1000
ENV_VAR_PREFIX = "LOCAL_DATA_PATH_"
CREDENTIALS_PATTERN = re.compile(r"[A-Za-z0-9_.\-]{1,100}")


def _to_record(row: DatasetLocationModel) -> DatasetLocationRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created, updated = row.created_at, row.updated_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return DatasetLocationRecord(
        id=row.id,
        dataset_id=row.dataset_id,
        location_type=row.location_type,
        path=row.path,
        local_env_var_name=row.local_env_var_name,
        credentials_ref=row.credentials_ref,
        description=row.description,
        created_at=created,
        updated_at=updated,
    )


def _has_invalid_field(req: DatasetLocationReq) -> bool:
    """True when a field that was given is not acceptable. A field left as None is not checked here."""
    if req.location_type is not None and req.location_type not in DatasetLocationType.values():
        return True
    if req.path is not None and (
        not isinstance(req.path, str) or not req.path.strip() or len(req.path.strip()) > PATH_MAX
    ):
        return True
    if req.local_env_var_name is not None and (
        not isinstance(req.local_env_var_name, str) or not req.local_env_var_name
    ):
        return True
    if req.path is not None and req.local_env_var_name is not None:
        return True
    if req.credentials_ref is not None and (
        not isinstance(req.credentials_ref, str) or CREDENTIALS_PATTERN.fullmatch(req.credentials_ref) is None
    ):
        return True
    return False


def _result_is_invalid(merged: DatasetLocationReq) -> bool:
    """The rules for the whole row: exactly one of path and env var name, and an env var name only for "local"."""
    if (merged.path is None) == (merged.local_env_var_name is None):
        return True
    return merged.local_env_var_name is not None and merged.location_type != DatasetLocationType.LOCAL


def _same_place_query(merged: DatasetLocationReq) -> Select:
    """Ids of rows of the same dataset that have the same type and path, or the same env var name."""
    query = select(DatasetLocationModel.id).where(DatasetLocationModel.dataset_id == merged.dataset_id)
    if merged.path is not None:
        return query.where(
            DatasetLocationModel.location_type == merged.location_type, DatasetLocationModel.path == merged.path
        )
    return query.where(DatasetLocationModel.local_env_var_name == merged.local_env_var_name)


class SqlAlchemyDatasetLocationDao(DatasetLocationDao):
    def create(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not (req.dataset_id and req.location_type) or _has_invalid_field(req):
            return INVALID_INPUT
        merged = DatasetLocationReq(
            dataset_id=req.dataset_id,
            location_type=req.location_type,
            path=None if req.path is None else req.path.strip(),
            local_env_var_name=req.local_env_var_name,
            credentials_ref=req.credentials_ref,
        )
        if _result_is_invalid(merged):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                dataset = session.get(DatasetModel, req.dataset_id)
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset.code:
                    return INVALID_INPUT
                if session.scalars(_same_place_query(merged)).first() is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                row = DatasetLocationModel(
                    id=str(uuid4()),
                    dataset_id=merged.dataset_id,
                    location_type=merged.location_type,
                    path=merged.path,
                    local_env_var_name=merged.local_env_var_name,
                    credentials_ref=merged.credentials_ref,
                    description=req.description,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same place at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets_location create failed")
            return FAILURE

    def get(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("datasets_location get failed")
            return FAILURE

    def list(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        try:
            query = select(DatasetLocationModel)
            if req.dataset_id is not None:
                query = query.where(DatasetLocationModel.dataset_id == req.dataset_id)
            if req.location_type is not None:
                query = query.where(DatasetLocationModel.location_type == req.location_type)
            # SQLite and Postgres sort NULLs differently, so "rows with a path first" is spelled out.
            query = query.order_by(
                DatasetLocationModel.location_type,
                DatasetLocationModel.path.is_(None),
                DatasetLocationModel.path,
                DatasetLocationModel.id,
            )
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("datasets_location list failed")
            return FAILURE

    def update(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                if req.dataset_id is not None and req.dataset_id != row.dataset_id:
                    return INVALID_INPUT
                # The row as it would be after the update. Giving a path clears the env var name and the other way round.
                if req.path is not None:
                    path, env_var_name = req.path.strip(), None
                elif req.local_env_var_name is not None:
                    path, env_var_name = None, req.local_env_var_name
                else:
                    path, env_var_name = row.path, row.local_env_var_name
                merged = DatasetLocationReq(
                    dataset_id=row.dataset_id,
                    location_type=req.location_type if req.location_type is not None else row.location_type,
                    path=path,
                    local_env_var_name=env_var_name,
                    credentials_ref=req.credentials_ref if req.credentials_ref is not None else row.credentials_ref,
                )
                if _result_is_invalid(merged):
                    return INVALID_INPUT
                dataset = session.get(DatasetModel, row.dataset_id)
                if dataset is None:
                    return NOT_FOUND
                if merged.local_env_var_name is not None and merged.local_env_var_name != ENV_VAR_PREFIX + dataset.code:
                    return INVALID_INPUT
                if session.scalars(_same_place_query(merged).where(DatasetLocationModel.id != row.id)).first() is not None:
                    return CONFLICT
                row.location_type = merged.location_type
                row.path = merged.path
                row.local_env_var_name = merged.local_env_var_name
                row.credentials_ref = merged.credentials_ref
                if req.description is not None:
                    row.description = req.description
                row.updated_at = datetime.now(timezone.utc)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers took the same place at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("datasets_location update failed")
            return FAILURE

    def delete(self, ctx: DatasetLocationCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(DatasetLocationModel, req.id)
                if row is None:
                    return NOT_FOUND
                chosen = select(MioDatasetModel.id).where(MioDatasetModel.dataset_location_id == row.id)
                if session.scalars(chosen).first() is not None:
                    return CONFLICT
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("datasets_location delete failed")
            return FAILURE
```

- [ ] **Step 6: Register the singleton**

In `app/core/dao/objects_factory.py` add `from app.core.dao.dataset_location_dao import DatasetLocationDao` (after the `dataset_dao` import) and this method after `get_dataset_dao`:

```python
    @staticmethod
    def get_dataset_location_dao() -> DatasetLocationDao:
        from app.core.dao.impl.sqlalchemy_dataset_location_dao import SqlAlchemyDatasetLocationDao

        return SqlAlchemyDatasetLocationDao()
```

- [ ] **Step 7: Run them and see them pass**

Run: `uv run pytest tests/test_dataset_location_dao.py tests/test_singletons.py tests/test_ctx_only_signatures.py -v && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.` Two tests to watch: `test_update_errors` expects the update of `http` to `path="https://other"` to be a CONFLICT with the row `other`, and `test_get_and_list...` expects the order `ftp`, `http a`, `http b`, `local env var` (types sorted `ftp` < `http` < `local`; the env var row has no path so it is last within `local`, and it is the only `local` row).

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 86` with summary `DatasetLocationDao` and files `app/core/common/dtos/dataset_location_dtos.py app/core/dao/dataset_location_dao.py app/core/dao/impl/sqlalchemy_dataset_location_dao.py app/core/dao/objects_factory.py tests/test_dataset_location_dao.py tests/test_singletons.py`.

---

### Task 7: `MioDatasetDao`

**Files:**
- Create: `app/core/common/dtos/mio_dataset_dtos.py`, `app/core/dao/mio_dataset_dao.py`, `app/core/dao/impl/sqlalchemy_mio_dataset_dao.py`
- Modify: `app/core/dao/objects_factory.py`, `tests/test_singletons.py`
- Test: `tests/test_mio_dataset_dao.py`

**Interfaces:**
- Consumes: `DatasetDao`, `MioDao`, `DatasetLocationDao` through the factory (Tasks 4 to 6); `MioModel`, `DatasetModel`, `DatasetLocationModel`, `MioDatasetModel`.
- Produces: `MioDatasetReq(id, mio_id, dataset_id, dataset_location_id)`, `MioDatasetResp`, `MioDatasetCtx`, `MioDatasetRecord(id, mio_id, dataset_id, dataset_location_id, created_at)`; `MioDatasetDao.create/get/list/update/delete(ctx) -> int`; `DaoObjectsFactory.get_mio_dataset_dao()`; module function `sqlalchemy_mio_dataset_dao._same_link_query(req: MioDatasetReq) -> Select`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mio_dataset_dao.py`:

```python
from sqlalchemy import false, select

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_mio_dataset_dao as dao_impl
from app.core.dao.impl.models import MioDatasetModel
from app.core.dao.objects_factory import DaoObjectsFactory


def _dataset(name="t_ds", code="T1") -> str:
    ctx = DatasetCtx(req=DatasetReq(name=name, code=code))
    assert DaoObjectsFactory.get_dataset_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _location(dataset_id, path="https://example.com/a") -> str:
    ctx = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset_id, location_type="http", path=path))
    assert DaoObjectsFactory.get_dataset_location_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _mio(name="t_mio") -> str:
    ctx = MioCtx(req=MioReq(name=name))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _ctx(**fields) -> MioDatasetCtx:
    return MioDatasetCtx(req=MioDatasetReq(**fields))


def _link(dao, mio_id, dataset_id, location_id) -> MioDatasetCtx:
    ctx = _ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=location_id)
    assert dao.create(ctx) == SUCCESS
    return ctx


def test_create_returns_the_row(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    row = _link(dao, mio_id, dataset_id, location_id).resp.records[0]
    assert len(row.id) == 36
    assert (row.mio_id, row.dataset_id, row.dataset_location_id) == (mio_id, dataset_id, location_id)
    assert row.created_at.tzinfo is not None


def test_create_needs_all_three_ids(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    assert dao.create(_ctx(dataset_id=dataset_id, dataset_location_id=location_id)) == INVALID_INPUT
    assert dao.create(_ctx(mio_id=mio_id, dataset_location_id=location_id)) == INVALID_INPUT
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id)) == INVALID_INPUT


def test_every_parent_must_exist_and_the_location_must_belong_to_the_dataset(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id, other_dataset_id = _mio(), _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    location_id, other_location_id = _location(dataset_id), _location(other_dataset_id)
    assert dao.create(_ctx(mio_id="nope", dataset_id=dataset_id, dataset_location_id=location_id)) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id="nope", dataset_location_id=location_id)) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id="nope")) == NOT_FOUND
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=other_location_id)) == INVALID_INPUT


def test_a_mio_has_one_link_per_dataset_but_many_mios_can_share_a_dataset_and_a_location(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    first, second = _mio("t_first"), _mio("t_second")
    dataset_id, other_dataset_id = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    location_id, other_location_id = _location(dataset_id), _location(other_dataset_id)
    _link(dao, first, dataset_id, location_id)
    assert dao.create(_ctx(mio_id=first, dataset_id=dataset_id, dataset_location_id=location_id)) == CONFLICT
    _link(dao, second, dataset_id, location_id)  # another MIO may use the same dataset and the same location
    _link(dao, first, other_dataset_id, other_location_id)  # one MIO may use another dataset


def test_get_and_list_with_filters_in_creation_order(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    first, second = _mio("t_first"), _mio("t_second")
    a, b = _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    loc_a, loc_b = _location(a), _location(b)
    one = _link(dao, first, a, loc_a).resp.records[0]
    two = _link(dao, first, b, loc_b).resp.records[0]
    three = _link(dao, second, a, loc_a).resp.records[0]

    by_mio = _ctx(mio_id=first)
    assert dao.list(by_mio) == SUCCESS and [r.id for r in by_mio.resp.records] == [one.id, two.id]
    by_dataset = _ctx(dataset_id=a)
    assert dao.list(by_dataset) == SUCCESS and [r.id for r in by_dataset.resp.records] == [one.id, three.id]
    both = _ctx(mio_id=second, dataset_id=a)
    assert dao.list(both) == SUCCESS and [r.id for r in both.resp.records] == [three.id]

    fetched = _ctx(id=two.id)
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].dataset_location_id == loc_b
    assert dao.get(_ctx()) == INVALID_INPUT
    assert dao.get(_ctx(id="nope")) == NOT_FOUND


def test_update_may_only_change_the_chosen_location_to_another_location_of_the_same_dataset(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id, other_dataset_id = _mio(), _dataset(name="t_a", code="T1"), _dataset(name="t_b", code="T2")
    http, mirror = _location(dataset_id), _location(dataset_id, path="https://mirror.example.com/a")
    foreign = _location(other_dataset_id)
    row = _link(dao, mio_id, dataset_id, http).resp.records[0]

    moved = _ctx(id=row.id, dataset_location_id=mirror)
    assert dao.update(moved) == SUCCESS
    assert (moved.resp.records[0].dataset_location_id, moved.resp.records[0].created_at) == (mirror, row.created_at)
    assert dao.update(_ctx(id=row.id, dataset_location_id=foreign)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, dataset_location_id="nope")) == NOT_FOUND
    assert dao.update(_ctx(id=row.id)) == INVALID_INPUT  # nothing to change
    assert dao.update(_ctx(dataset_location_id=http)) == INVALID_INPUT  # no id
    assert dao.update(_ctx(id="nope", dataset_location_id=http)) == NOT_FOUND
    assert dao.update(_ctx(id=row.id, mio_id="another", dataset_location_id=http)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, dataset_id=other_dataset_id, dataset_location_id=http)) == INVALID_INPUT
    assert dao.update(_ctx(id=row.id, mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=http)) == SUCCESS


def test_delete_returns_the_row_and_frees_the_parents(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    row = _link(dao, mio_id, dataset_id, location_id).resp.records[0]
    assert DaoObjectsFactory.get_mio_dao().delete(MioCtx(req=MioReq(id=mio_id))) == CONFLICT
    assert DaoObjectsFactory.get_dataset_location_dao().delete(DatasetLocationCtx(req=DatasetLocationReq(id=location_id))) == CONFLICT

    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].id == row.id
    assert dao.delete(_ctx(id=row.id)) == NOT_FOUND
    assert dao.delete(_ctx()) == INVALID_INPUT
    assert DaoObjectsFactory.get_mio_dao().delete(MioCtx(req=MioReq(id=mio_id))) == SUCCESS
    assert DaoObjectsFactory.get_dataset_location_dao().delete(DatasetLocationCtx(req=DatasetLocationReq(id=location_id))) == SUCCESS
    assert DaoObjectsFactory.get_dataset_dao().delete(DatasetCtx(req=DatasetReq(id=dataset_id))) == SUCCESS


def test_a_duplicate_that_slips_past_the_pre_check_is_a_conflict(data_dir, monkeypatch):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    mio_id, dataset_id = _mio(), _dataset()
    location_id = _location(dataset_id)
    _link(dao, mio_id, dataset_id, location_id)
    monkeypatch.setattr(dao_impl, "_same_link_query", lambda req: select(MioDatasetModel.id).where(false()))
    assert dao.create(_ctx(mio_id=mio_id, dataset_id=dataset_id, dataset_location_id=location_id)) == CONFLICT
    listed = _ctx(mio_id=mio_id)
    assert dao.list(listed) == SUCCESS and len(listed.resp.records) == 1


def test_a_link_can_join_the_transaction_that_creates_its_parents(data_dir):
    dao = DaoObjectsFactory.get_mio_dataset_dao()
    transactions = DaoObjectsFactory.get_transaction_dao()
    tx = TransactionCtx()
    assert transactions.begin(tx) == SUCCESS
    mio = MioCtx(transaction=tx, req=MioReq(name="t_tx"))
    dataset = DatasetCtx(transaction=tx, req=DatasetReq(name="t_tx_ds", code="T1"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    assert DaoObjectsFactory.get_dataset_dao().create(dataset) == SUCCESS
    place = DatasetLocationCtx(
        transaction=tx,
        req=DatasetLocationReq(dataset_id=dataset.resp.records[0].id, location_type="http", path="https://x"),
    )
    assert DaoObjectsFactory.get_dataset_location_dao().create(place) == SUCCESS
    link = MioDatasetCtx(
        transaction=tx,
        req=MioDatasetReq(
            mio_id=mio.resp.records[0].id,
            dataset_id=dataset.resp.records[0].id,
            dataset_location_id=place.resp.records[0].id,
        ),
    )
    assert dao.create(link) == SUCCESS
    assert transactions.rollback(tx) == SUCCESS
    assert dao.get(_ctx(id=link.resp.records[0].id)) == NOT_FOUND
    assert DaoObjectsFactory.get_mio_dao().get(MioCtx(req=MioReq(name="t_tx"))) == NOT_FOUND
```

In `tests/test_singletons.py` add imports `from app.core.dao.mio_dataset_dao import MioDatasetDao` and `from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao`, add `(DaoObjectsFactory.get_mio_dataset_dao, MioDatasetDao),` to the tuple and `assert SqlAlchemyMioDatasetDao() is SqlAlchemyMioDatasetDao()` to the classes test.

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_mio_dataset_dao.py tests/test_singletons.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'app.core.common.dtos.mio_dataset_dtos'`.

- [ ] **Step 3: Add the DTOs**

Create `app/core/common/dtos/mio_dataset_dtos.py`:

```python
"""Ctx, Req and Resp for the mios_datasets table (which datasets a MIO uses and where, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioDatasetRecord:
    id: str
    mio_id: str
    dataset_id: str
    dataset_location_id: str
    created_at: datetime


@dataclass
class MioDatasetReq:
    """A field left as None means "not given". id identifies one row (get, update, delete)."""

    id: str | None = None
    mio_id: str | None = None
    dataset_id: str | None = None
    dataset_location_id: str | None = None


@dataclass
class MioDatasetResp:
    records: list[MioDatasetRecord] = field(default_factory=list)


@dataclass
class MioDatasetCtx(TransactionalCtx):
    req: MioDatasetReq = field(default_factory=MioDatasetReq)
    resp: MioDatasetResp = field(default_factory=MioDatasetResp)
```

- [ ] **Step 4: Add the interface**

Create `app/core/dao/mio_dataset_dao.py`:

```python
"""Interface of the DAO for the mios_datasets table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx
from app.core.common.singleton import SingletonMeta


class MioDatasetDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one MioDatasetCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    A row says "this MIO uses this dataset, read from this location of it". A MIO has at most one row per dataset;
    many MIOs may share the same dataset and the same location (D57). This is the only link between a MIO and its
    data: nothing is derived from the MIO's name."""

    @abstractmethod
    def create(self, ctx: MioDatasetCtx) -> int:
        """Needs req.mio_id, req.dataset_id and req.dataset_location_id. INVALID_INPUT if one is missing or the
        location belongs to another dataset, NOT_FOUND if the MIO, the dataset or the location does not exist,
        CONFLICT if the MIO already uses the dataset."""

    @abstractmethod
    def get(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def list(self, ctx: MioDatasetCtx) -> int:
        """Optional filters: req.mio_id, req.dataset_id. Ordered by created_at, id."""

    @abstractmethod
    def update(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id and req.dataset_location_id: only the chosen location can change, and it must belong to the
        row's dataset (INVALID_INPUT otherwise). A req.mio_id or req.dataset_id that is not the row's own is
        INVALID_INPUT. NOT_FOUND if the row or the new location does not exist."""

    @abstractmethod
    def delete(self, ctx: MioDatasetCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row."""
```

- [ ] **Step 5: Add the implementation**

Create `app/core/dao/impl/sqlalchemy_mio_dataset_dao.py`:

```python
"""MioDatasetDao on SQLAlchemy. Works on SQLite and, unchanged, on Postgres and similar databases.

It reads MioModel, DatasetModel and DatasetLocationModel to keep the parent rules (no foreign keys, D57)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetRecord, MioDatasetReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import DatasetLocationModel, DatasetModel, MioDatasetModel, MioModel
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.mio_dataset_dao import MioDatasetDao

log = logging.getLogger(__name__)


def _to_record(row: MioDatasetModel) -> MioDatasetRecord:
    # SQLite hands timestamps back without a time zone; they were stored as UTC.
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioDatasetRecord(
        id=row.id,
        mio_id=row.mio_id,
        dataset_id=row.dataset_id,
        dataset_location_id=row.dataset_location_id,
        created_at=created,
    )


def _same_link_query(req: MioDatasetReq) -> Select:
    """Ids of rows where the MIO already uses the dataset."""
    return select(MioDatasetModel.id).where(
        MioDatasetModel.mio_id == req.mio_id, MioDatasetModel.dataset_id == req.dataset_id
    )


class SqlAlchemyMioDatasetDao(MioDatasetDao):
    def create(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.dataset_id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                if session.get(MioModel, req.mio_id) is None or session.get(DatasetModel, req.dataset_id) is None:
                    return NOT_FOUND
                location = session.get(DatasetLocationModel, req.dataset_location_id)
                if location is None:
                    return NOT_FOUND
                if location.dataset_id != req.dataset_id:
                    return INVALID_INPUT
                if session.scalars(_same_link_query(req)).first() is not None:
                    return CONFLICT
                row = MioDatasetModel(
                    id=str(uuid4()),
                    mio_id=req.mio_id,
                    dataset_id=req.dataset_id,
                    dataset_location_id=req.dataset_location_id,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except IntegrityError:
            # Two writers linked the same MIO and dataset at once; the unique constraint decided.
            return CONFLICT
        except Exception:
            log.exception("mios_datasets create failed")
            return FAILURE

    def get(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets get failed")
            return FAILURE

    def list(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        try:
            query = select(MioDatasetModel)
            if req.mio_id is not None:
                query = query.where(MioDatasetModel.mio_id == req.mio_id)
            if req.dataset_id is not None:
                query = query.where(MioDatasetModel.dataset_id == req.dataset_id)
            query = query.order_by(MioDatasetModel.created_at, MioDatasetModel.id)
            with unit_of_work(ctx) as session:
                ctx.resp.records = [_to_record(row) for row in session.scalars(query)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets list failed")
            return FAILURE

    def update(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                if (req.mio_id is not None and req.mio_id != row.mio_id) or (
                    req.dataset_id is not None and req.dataset_id != row.dataset_id
                ):
                    return INVALID_INPUT
                location = session.get(DatasetLocationModel, req.dataset_location_id)
                if location is None:
                    return NOT_FOUND
                if location.dataset_id != row.dataset_id:
                    return INVALID_INPUT
                row.dataset_location_id = req.dataset_location_id
                session.flush()
                ctx.resp.records = [_to_record(row)]
            return SUCCESS
        except Exception:
            log.exception("mios_datasets update failed")
            return FAILURE

    def delete(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(MioDatasetModel, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(row)]
                session.delete(row)
                session.flush()
            return SUCCESS
        except Exception:
            log.exception("mios_datasets delete failed")
            return FAILURE
```

- [ ] **Step 6: Register the singleton**

In `app/core/dao/objects_factory.py` add `from app.core.dao.mio_dataset_dao import MioDatasetDao` (after the `mio_dao` import) and this method after `get_mio_dao`:

```python
    @staticmethod
    def get_mio_dataset_dao() -> MioDatasetDao:
        from app.core.dao.impl.sqlalchemy_mio_dataset_dao import SqlAlchemyMioDatasetDao

        return SqlAlchemyMioDatasetDao()
```

Keep the factory's methods in one consistent order (alphabetical by name is fine) and its imports sorted.

- [ ] **Step 7: Run them and see them pass**

Run: `uv run pytest tests/test_mio_dataset_dao.py tests/test_singletons.py tests/test_ctx_only_signatures.py -v && uv run lint-imports`
Expected: all PASS; `Contracts: 7 kept, 0 broken.` The ordering test relies on `created_at` increasing between the three `_link` calls; if two rows get an equal timestamp on a fast machine the `id` tie-break is random, so if `test_get_and_list_with_filters_in_creation_order` fails intermittently, add a `time.sleep(0.002)` between the three `_link` calls in that test (do not change the DAO).

- [ ] **Step 8: Commit**

Run `/ccaa-commit-push 86` with summary `MioDatasetDao` and files `app/core/common/dtos/mio_dataset_dtos.py app/core/dao/mio_dataset_dao.py app/core/dao/impl/sqlalchemy_mio_dataset_dao.py app/core/dao/objects_factory.py tests/test_mio_dataset_dao.py tests/test_singletons.py`.

---

### Task 8: the seed through the DAOs, Postgres, and the design note

**Files:**
- Create: `tests/test_catalog_flow.py`
- Modify: `tests/test_postgres.py`, `DESIGN.md`

**Interfaces:**
- Consumes: all four DAOs through `DaoObjectsFactory`; the seed from Task 3.

- [ ] **Step 1: Write the tests**

Create `tests/test_catalog_flow.py`:

```python
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import CONFLICT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SEED_MIO_NAMES = [f"Customer complaints {months} months 2026" for months in (3, 6, 9, 12)]


def _seed_dataset():
    ctx = DatasetCtx(req=DatasetReq(name="cfpb_consumer_complaints"))
    assert DaoObjectsFactory.get_dataset_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def _links_of(mio_id):
    ctx = MioDatasetCtx(req=MioDatasetReq(mio_id=mio_id))
    assert DaoObjectsFactory.get_mio_dataset_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def test_the_seed_can_be_read_through_the_daos(data_dir):
    dataset = _seed_dataset()
    assert dataset.code == "CFPB"

    places = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert DaoObjectsFactory.get_dataset_location_dao().list(places) == SUCCESS
    by_type = {p.location_type: p for p in places.resp.records}
    assert sorted(by_type) == ["http", "local"]
    assert by_type["http"].path == "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
    assert by_type["http"].credentials_ref is None
    assert (by_type["local"].path, by_type["local"].local_env_var_name) == (None, "LOCAL_DATA_PATH_CFPB")

    for name in SEED_MIO_NAMES:
        mio = MioCtx(req=MioReq(name=name))
        assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
        links = _links_of(mio.resp.records[0].id)
        assert [(link.dataset_id, link.dataset_location_id) for link in links] == [(dataset.id, by_type["http"].id)]


def test_a_mio_name_decides_nothing_about_its_data(data_dir):
    dataset = _seed_dataset()
    mios = DaoObjectsFactory.get_mio_dao()
    before = MioCtx(req=MioReq(name="Customer complaints 3 months 2026"))
    assert mios.get(before) == SUCCESS
    mio_id = before.resp.records[0].id
    links_before = [(link.dataset_id, link.dataset_location_id) for link in _links_of(mio_id)]

    renamed = MioCtx(req=MioReq(id=mio_id, name="Something unrelated", description="no window here"))
    assert mios.update(renamed) == SUCCESS
    assert [(link.dataset_id, link.dataset_location_id) for link in _links_of(mio_id)] == links_before

    # A new MIO with any name reuses the same dataset and the same location.
    http_id = links_before[0][1]
    fresh = MioCtx(req=MioReq(name="Customer complaints 100 years"))
    assert mios.create(fresh) == SUCCESS
    link = MioDatasetCtx(
        req=MioDatasetReq(mio_id=fresh.resp.records[0].id, dataset_id=dataset.id, dataset_location_id=http_id)
    )
    assert DaoObjectsFactory.get_mio_dataset_dao().create(link) == SUCCESS


def test_the_catalog_is_taken_apart_from_the_links_to_the_dataset(data_dir):
    datasets = DaoObjectsFactory.get_dataset_dao()
    locations = DaoObjectsFactory.get_dataset_location_dao()
    mios = DaoObjectsFactory.get_mio_dao()
    links = DaoObjectsFactory.get_mio_dataset_dao()
    dataset = _seed_dataset()
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == CONFLICT  # locations and links use it

    for name in SEED_MIO_NAMES:
        mio = MioCtx(req=MioReq(name=name))
        assert mios.get(mio) == SUCCESS
        mio_id = mio.resp.records[0].id
        assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == CONFLICT  # its link is still there
        for link in _links_of(mio_id):
            assert links.delete(MioDatasetCtx(req=MioDatasetReq(id=link.id))) == SUCCESS
        assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == SUCCESS

    places = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert locations.list(places) == SUCCESS
    for place in places.resp.records:
        assert locations.delete(DatasetLocationCtx(req=DatasetLocationReq(id=place.id))) == SUCCESS
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == SUCCESS
```

Append to `tests/test_postgres.py` (add `from sqlalchemy.exc import IntegrityError` below the existing `from sqlalchemy import ...` line, and `from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq`, `from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq`, `from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq` and `from app.core.common.dtos.mio_dtos import MioCtx, MioReq` to the imports, keeping them sorted):

```python
def test_catalog_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert {"datasets", "datasets_location", "mios", "mios_datasets"} <= _admin_tables()
    engine = create_engine(URL)
    with engine.connect() as c:
        seeded = c.execute(text(f"select count(*) from {SCHEMA_ADMIN}.mios")).scalar()
    assert seeded == 4

    datasets = DaoObjectsFactory.get_dataset_dao()
    locations = DaoObjectsFactory.get_dataset_location_dao()
    mios = DaoObjectsFactory.get_mio_dao()
    links = DaoObjectsFactory.get_mio_dataset_dao()

    made = DatasetCtx(req=DatasetReq(name="t_ds", code="T1"))
    assert datasets.create(made) == SUCCESS
    dataset = made.resp.records[0]
    assert dataset.created_at.tzinfo is not None
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_ds", code="T9"))) == CONFLICT
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_other", code="T1"))) == CONFLICT
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_other", code="CFPB"))) == CONFLICT  # the seed's code

    http = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id, location_type="http", path="https://x"))
    env = DatasetLocationCtx(
        req=DatasetLocationReq(dataset_id=dataset.id, location_type="local", local_env_var_name="LOCAL_DATA_PATH_T1")
    )
    assert locations.create(http) == SUCCESS and locations.create(env) == SUCCESS
    assert locations.create(DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id, location_type="http", path="https://x"))) == CONFLICT
    both = DatasetLocationReq(dataset_id=dataset.id, location_type="local", path="/a", local_env_var_name="LOCAL_DATA_PATH_T1")
    assert locations.create(DatasetLocationCtx(req=both)) == INVALID_INPUT
    listed = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert locations.list(listed) == SUCCESS
    assert [r.location_type for r in listed.resp.records] == ["http", "local"]  # the same order as on SQLite

    # The check constraint holds in the database itself, not only in the DAO.
    with pytest.raises(IntegrityError, match="ck_datasets_location_path_xor_env"):
        with engine.begin() as c:
            c.execute(
                text(
                    f"insert into {SCHEMA_ADMIN}.datasets_location (id, dataset_id, location_type, path, local_env_var_name,"
                    " created_at, updated_at) values ('x', :d, 'local', 'p', 'E', now(), now())"
                ),
                {"d": dataset.id},
            )
    engine.dispose()

    mio = MioCtx(req=MioReq(name="t_mio"))
    assert mios.create(mio) == SUCCESS
    link = MioDatasetCtx(
        req=MioDatasetReq(mio_id=mio.resp.records[0].id, dataset_id=dataset.id, dataset_location_id=http.resp.records[0].id)
    )
    assert links.create(link) == SUCCESS
    assert links.create(MioDatasetCtx(req=link.req)) == CONFLICT
    assert mios.delete(MioCtx(req=MioReq(id=mio.resp.records[0].id))) == CONFLICT
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == CONFLICT
    assert links.delete(MioDatasetCtx(req=MioDatasetReq(id=link.resp.records[0].id))) == SUCCESS
    assert mios.delete(MioCtx(req=MioReq(id=mio.resp.records[0].id))) == SUCCESS

    command.downgrade(postgres, "0004")
    assert not {"datasets", "datasets_location", "mios", "mios_datasets"} & _admin_tables()
    command.upgrade(postgres, "head")
    assert {"datasets", "datasets_location", "mios", "mios_datasets"} <= _admin_tables()
```

- [ ] **Step 2: Run the SQLite tests**

Run: `uv run pytest tests/test_catalog_flow.py -v`
Expected: all PASS (the implementation exists; these tests lock the behavior).

- [ ] **Step 3: Run the whole suite on a real Postgres**

Run, from the repository root as the app root's path is needed for `uv run`:

```bash
docker run -d --name cca-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:16
sleep 6
cd Middleware/ConsumerComplaintsHandsOn
CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55432/postgres uv run pytest -v
docker rm -f cca-pg
```

Expected: the whole suite passes (the Postgres tests no longer skipped). Postgres names the violated check constraint in its error, which is what the `match=` in the test relies on. If `docker` is not available, say so in the report and rely on CI's Postgres service.

- [ ] **Step 4: Mark the catalog as built in the design**

In `DESIGN.md`, in the section `#### The catalog (D49)`, directly after the bullet that starts `- **Open:** which of a MIO's dataset locations a download uses`, add the bullet:

```
- **Built (story #86, M02-0036):** the four tables (migration `0005`), the seed (migration `0006`) and one DAO each: `DatasetDao`, `DatasetLocationDao`, `MioDao` and `MioDatasetDao`. No endpoint reads them yet.
```

- [ ] **Step 5: Run everything**

Run: `uv run lint-imports && uv run pytest`
Expected: `Contracts: 7 kept, 0 broken.`; all tests PASS (Postgres tests skipped without the variable).

- [ ] **Step 6: Commit**

Run `/ccaa-commit-push 86` with summary `catalog flow tests, Postgres test and design note` and files `tests/test_catalog_flow.py tests/test_postgres.py DESIGN.md`.

---

## Self-Review (done)

1. **Spec coverage:** tables and constraints (Task 2); `DatasetLocationType` (Task 1); seed with fixed ids, no machine path, `LOCAL_DATA_PATH_CFPB` row (Task 3); `DatasetDao` with code rule, env-var-code freeze, in-use delete (Task 4); `MioDao` (Task 5); `DatasetLocationDao` with path/env exclusivity, name = prefix + code, credentials name rule, duplicate rules, ordering, in-use delete (Task 6); `MioDatasetDao` with parent and same-dataset rules, many MIOs sharing one dataset and location (Task 7); no semantic matching test, seed read through DAOs, Postgres, `DESIGN.md` note (Task 8); singletons registered per DAO (Tasks 4 to 7). Not covered by design: a delete racing a create can leave an orphan (accepted in the spec).
2. **Placeholders:** none; every code step has full code. Two conditional fixes are written as concrete instructions with a cause (Task 4 step 7, Task 7 step 7, Task 8 step 3).
3. **Types and names:** `_taken_query` (Dataset takes `DatasetReq`, Mio takes `MioReq`), `_same_place_query(merged: DatasetLocationReq)`, `_same_link_query(req: MioDatasetReq)`, `ENV_VAR_PREFIX`, factory names `get_dataset_dao`, `get_mio_dao`, `get_dataset_location_dao`, `get_mio_dataset_dao`, and DTO field names match across the interfaces, implementations and tests.
