import json
import sqlite3

import pytest
from alembic import command
from alembic.config import Config

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT

DOWNLOAD_CFPB_ALL_WORKFLOW_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
FILTER_CFPB_3_MONTHS_WORKFLOW_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"
INGEST_CFPB_ALL_WORKFLOW_ID = "0064095f-9f8e-5f09-94cf-3b4fe28e2b33"
INDEX_CFPB_ALL_WORKFLOW_ID = "120e90d3-f61d-5fd4-a8c4-2a1aba9e9ba6"
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
MIOS_WORKFLOWS_ALL_DOWNLOAD_ID = "c23808b9-4e57-5a5b-b301-78dec5ac839e"
MIOS_WORKFLOWS_3M_FILTER_ID = "edd79fde-5736-5655-9d00-c52bfe172c1f"
MIOS_WORKFLOWS_ALL_INGEST_ID = "251b44d2-9aea-5d9d-b1a0-0816e8db3f80"
MIOS_WORKFLOWS_ALL_INDEX_ID = "ee28b7aa-b4cf-5611-bf07-080fb3b53864"
APP_ENDPOINT_INDEX_ID = "af151640-ce3a-5995-a390-fa1ec5212aaf"
INDEX_CFPB_PGVECTOR_WORKFLOW_ID = "68a0fa8a-825c-53f1-864f-5db167a339a0"
MIOS_WORKFLOWS_ALL_INDEX_PG_ID = "494ff42b-a7e7-5e90-8430-74b81a52dff1"
APP_ENDPOINT_INDEX_PG_ID = "2e6bd178-2900-5ea2-80ed-507f486a2133"
INDEX_CFPB_CHROMA_WORKFLOW_ID = "87100dc6-f634-5bde-8539-d7175ca194ac"
INDEX_CFPB_REDIS_WORKFLOW_ID = "474e4e9a-5743-54c2-99f6-5ec860aa8c38"
MIOS_WORKFLOWS_ALL_INDEX_CHROMA_ID = "2a43462f-e29d-506c-9422-1a39dfdc16eb"
MIOS_WORKFLOWS_ALL_INDEX_REDIS_ID = "cc9d2cc5-088a-5d57-8227-4c2d2ef1cbc9"
APP_ENDPOINT_INDEX_CHROMA_ID = "1046ad4a-b4fd-509b-9bc3-9e8501ef86c0"
APP_ENDPOINT_INDEX_REDIS_ID = "bc449f1d-4055-5514-8794-c2ca504ebd99"


def test_schema_names():
    assert ALL_SCHEMAS == (
        "consumer_comp_db",
        "consumer_compl_intellect_db",
        "consumer_comp_users_db",
        "consumer_comp_admin_db",
    )


def test_migration_creates_all_schemas_and_drops_retired_complaints_tables(data_dir):
    for schema in ALL_SCHEMAS:
        assert (data_dir / f"{schema}.sqlite").exists()

    with sqlite3.connect(data_dir / "consumer_comp_db.sqlite") as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    assert "data_ingest_log" not in tables
    assert "system_datasets" not in tables


def test_migration_0010_runs_down_and_up(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0009")
    with sqlite3.connect(data_dir / "consumer_comp_db.sqlite") as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        rows = db.execute(
            "select dataset, stage, status, last_log_id from system_datasets order by dataset, stage"
        ).fetchall()
    assert {"data_ingest_log", "system_datasets"} <= tables
    assert rows == [
        ("3_months", "db_ingest", "not_started", None),
        ("3_months", "download", "not_started", None),
        ("all", "db_ingest", "not_started", None),
        ("all", "download", "not_started", None),
    ]
    command.upgrade(config, "head")
    with sqlite3.connect(data_dir / "consumer_comp_db.sqlite") as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    assert "data_ingest_log" not in tables
    assert "system_datasets" not in tables


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
        "mios_ingest_log_id",
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


HTTP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
SEED_MIO_NAMES = ["Customer complaints all 2026"] + [
    f"Customer complaints {months} months 2026" for months in (3, 6, 9, 12)
]


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
    assert len(links) == 5 and len({link[0] for link in links}) == 5
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
        assert db.execute("select count(*) from mios").fetchone()[0] == 5


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


def test_download_cfpb_all_workflow_is_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'download_cfpb_all'"
        ).fetchone()
    assert row is not None
    assert row[0] == DOWNLOAD_CFPB_ALL_WORKFLOW_ID
    assert row[1:4] == ("download_cfpb_all", "apache_airflow", "download_cfpb_all")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config["dataset_code"] == "CFPB"
    assert config.get("source_mode") == "split"
    assert config.get("source_filename_glob") == "complaints_part_*.csv.zip"
    assert config.get("stage_from_env") == "CCA_CFPB_SPLIT_SOURCE_PATH"
    assert config.get("app_endpoint_name") == "cfpb_stage_split_to_local"
    assert row[5] in (1, True)


def test_migration_0008_removes_the_download_cfpb_all_seed_on_the_way_down(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0007")
    with _admin_db(data_dir) as db:
        assert (
            db.execute(
                "select count(*) from app_workflows where workflow_name = 'download_cfpb_all'"
            ).fetchone()[0]
            == 0
        )
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert (
            db.execute(
                "select id from app_workflows where workflow_name = 'download_cfpb_all'"
            ).fetchone()[0]
            == DOWNLOAD_CFPB_ALL_WORKFLOW_ID
        )


def test_filter_cfpb_3_months_workflow_is_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'filter_cfpb_3_months'"
        ).fetchone()
    assert row is not None
    assert row[0] == FILTER_CFPB_3_MONTHS_WORKFLOW_ID
    assert row[1:4] == ("filter_cfpb_3_months", "apache_airflow", "filter_cfpb_3_months")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "months": 3,
        "source_filename": "complaints.csv.zip",
        "output_filename": "complaints_3_months.csv.zip",
        "date_column": "Date received",
    }
    assert row[5] in (1, True)


def test_migration_0009_removes_the_filter_cfpb_3_months_seed_on_the_way_down(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0008")
    with _admin_db(data_dir) as db:
        assert (
            db.execute(
                "select count(*) from app_workflows where workflow_name = 'filter_cfpb_3_months'"
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "select id from app_workflows where workflow_name = 'download_cfpb_all'"
            ).fetchone()[0]
            == DOWNLOAD_CFPB_ALL_WORKFLOW_ID
        )
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert (
            db.execute(
                "select id from app_workflows where workflow_name = 'filter_cfpb_3_months'"
            ).fetchone()[0]
            == FILTER_CFPB_3_MONTHS_WORKFLOW_ID
        )


def test_mios_workflows_table_exists_with_columns_and_no_foreign_keys(data_dir):
    with _admin_db(data_dir) as db:
        columns = _columns(db, "mios_workflows")
        indexes = {r[1] for r in db.execute("pragma index_list(mios_workflows)")}
        foreign_keys = db.execute("pragma foreign_key_list(mios_workflows)").fetchall()
        sql = _table_sql(db, "mios_workflows")
    assert columns == {
        "id": ("VARCHAR(36)", 1),
        "mio_id": ("VARCHAR(36)", 1),
        "workflow_id": ("VARCHAR(36)", 1),
        "created_at": ("DATETIME", 1),
    }
    assert "uq_mios_workflows_mio_workflow" in sql
    assert "ix_mios_workflows_mio_id" in indexes
    assert "ix_mios_workflows_workflow_id" in indexes
    assert foreign_keys == []


def test_mios_workflows_seed_binds_all_and_3_months_only(data_dir):
    with _admin_db(data_dir) as db:
        assert db.execute("select id, name from mios where name = 'Customer complaints all 2026'").fetchone() == (
            ALL_MIO_ID,
            "Customer complaints all 2026",
        )
        rows = db.execute(
            "select id, mio_id, workflow_id from mios_workflows order by mio_id, workflow_id"
        ).fetchall()
        unbound = db.execute(
            "select m.name from mios m"
            " left join mios_workflows mw on mw.mio_id = m.id"
            " where mw.id is null order by m.name"
        ).fetchall()
    assert rows == [
        (MIOS_WORKFLOWS_ALL_INGEST_ID, ALL_MIO_ID, INGEST_CFPB_ALL_WORKFLOW_ID),
        (MIOS_WORKFLOWS_ALL_INDEX_ID, ALL_MIO_ID, INDEX_CFPB_ALL_WORKFLOW_ID),
        (MIOS_WORKFLOWS_ALL_INDEX_REDIS_ID, ALL_MIO_ID, INDEX_CFPB_REDIS_WORKFLOW_ID),
        (MIOS_WORKFLOWS_ALL_INDEX_PG_ID, ALL_MIO_ID, INDEX_CFPB_PGVECTOR_WORKFLOW_ID),
        (MIOS_WORKFLOWS_ALL_INDEX_CHROMA_ID, ALL_MIO_ID, INDEX_CFPB_CHROMA_WORKFLOW_ID),
        (MIOS_WORKFLOWS_ALL_DOWNLOAD_ID, ALL_MIO_ID, DOWNLOAD_CFPB_ALL_WORKFLOW_ID),
        (MIOS_WORKFLOWS_3M_FILTER_ID, MIO_3_MONTHS_ID, FILTER_CFPB_3_MONTHS_WORKFLOW_ID),
    ]
    assert [r[0] for r in unbound] == [
        "Customer complaints 12 months 2026",
        "Customer complaints 6 months 2026",
        "Customer complaints 9 months 2026",
    ]


def test_ingest_cfpb_all_workflow_is_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'ingest_cfpb_all'"
        ).fetchone()
    assert row is not None
    assert row[0] == INGEST_CFPB_ALL_WORKFLOW_ID
    assert row[1:4] == ("ingest_cfpb_all", "apache_airflow", "ingest_cfpb_all")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "source_filename_glob": "complaints_part_*.csv.zip",
        "batch_size": 500,
        "app_endpoint_name": "cfpb_ingest_local_to_mongo",
    }
    assert row[5] in (1, True)


def test_migration_0011_removes_mios_workflows_and_all_mio_on_the_way_down(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0010")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'mios_workflows'").fetchall() == []
        assert (
            db.execute("select count(*) from mios where name = 'Customer complaints all 2026'").fetchone()[0] == 0
        )
        assert db.execute("select count(*) from mios").fetchone()[0] == 4
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'mios_workflows'").fetchall() != []
        assert db.execute("select id from mios where name = 'Customer complaints all 2026'").fetchone()[0] == ALL_MIO_ID
        assert db.execute("select count(*) from mios_workflows").fetchone()[0] == 7


APP_ENDPOINT_SOURCE_ID = "ccbce57d-bd9f-56fe-a258-fa2deb9dd393"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"


def test_app_endpoints_table_exists_with_xor_and_no_foreign_keys(data_dir):
    with _admin_db(data_dir) as db:
        columns = _columns(db, "app_endpoints")
        indexes = {r[1] for r in db.execute("pragma index_list(app_endpoints)")}
        foreign_keys = db.execute("pragma foreign_key_list(app_endpoints)").fetchall()
        sql = _table_sql(db, "app_endpoints")
    assert "id" in columns and "name" in columns and "category" in columns
    assert "uq_app_endpoints_name" in sql
    assert "ck_app_endpoints_from_xor" in sql
    assert "ck_app_endpoints_to_xor" in sql
    assert "ix_app_endpoints_category" in indexes
    assert foreign_keys == []


def test_app_endpoints_seed_cfpb_source_http_to_local(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, name, category, from_dataset_location_id, to_dataset_location_id, enabled"
            " from app_endpoints"
        ).fetchone()
    assert row == (
        APP_ENDPOINT_SOURCE_ID,
        "cfpb_source_http_to_local",
        "source",
        HTTP_LOCATION_ID,
        LOCAL_LOCATION_ID,
        1,
    )


def test_migration_0012_removes_app_endpoints_on_the_way_down(data_dir):
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "0011")
    with _admin_db(data_dir) as db:
        assert db.execute("select name from sqlite_master where name = 'app_endpoints'").fetchall() == []
    command.upgrade(config, "head")
    with _admin_db(data_dir) as db:
        assert db.execute("select count(*) from app_endpoints").fetchone()[0] == 7


def test_index_cfpb_all_workflow_is_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'index_cfpb_all'"
        ).fetchone()
        bind = db.execute(
            "select id, mio_id, workflow_id from mios_workflows where id = ?",
            (MIOS_WORKFLOWS_ALL_INDEX_ID,),
        ).fetchone()
        ep = db.execute(
            "select id, name, category, from_env_var_name, to_env_var_name, enabled"
            " from app_endpoints where name = 'cfpb_index_mongo_to_vectors'"
        ).fetchone()
    assert row is not None
    assert row[0] == INDEX_CFPB_ALL_WORKFLOW_ID
    assert row[1:4] == ("index_cfpb_all", "apache_airflow", "index_cfpb_all")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "batch_size": 500,
        "app_endpoint_name": "cfpb_index_mongo_to_vectors",
    }
    assert row[5] in (1, True)
    assert bind == (MIOS_WORKFLOWS_ALL_INDEX_ID, ALL_MIO_ID, INDEX_CFPB_ALL_WORKFLOW_ID)
    assert ep == (
        APP_ENDPOINT_INDEX_ID,
        "cfpb_index_mongo_to_vectors",
        "index",
        "CCA_MONGO_COMPLAINTS_URL",
        "CCA_VECTOR_STORE_PATH",
        1,
    )


def test_app_endpoints_seed_cfpb_stage_split_to_local(data_dir):
    with _admin_db(data_dir) as db:
        ep = db.execute(
            "select id, name, category, from_env_var_name, to_env_var_name, enabled"
            " from app_endpoints where name = 'cfpb_stage_split_to_local'"
        ).fetchone()
    assert ep == (
        "763c400e-09e1-59a5-92ed-ed910df667ac",
        "cfpb_stage_split_to_local",
        "source",
        "CCA_CFPB_SPLIT_SOURCE_PATH",
        "LOCAL_DATA_PATH_CFPB",
        1,
    )


def test_index_cfpb_pgvector_workflow_and_endpoint_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'index_cfpb_pgvector'"
        ).fetchone()
        bind = db.execute(
            "select id, mio_id, workflow_id from mios_workflows where id = ?",
            (MIOS_WORKFLOWS_ALL_INDEX_PG_ID,),
        ).fetchone()
        ep = db.execute(
            "select id, name, category, from_env_var_name, to_env_var_name, enabled"
            " from app_endpoints where name = 'cfpb_index_mongo_to_pgvector'"
        ).fetchone()
    assert row is not None
    assert row[0] == INDEX_CFPB_PGVECTOR_WORKFLOW_ID
    assert row[1:4] == ("index_cfpb_pgvector", "apache_airflow", "index_cfpb_pgvector")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "batch_size": 500,
        "vector_backend": "pgvector",
        "app_endpoint_name": "cfpb_index_mongo_to_pgvector",
    }
    assert row[5] in (1, True)
    assert bind == (MIOS_WORKFLOWS_ALL_INDEX_PG_ID, ALL_MIO_ID, INDEX_CFPB_PGVECTOR_WORKFLOW_ID)
    assert ep == (
        APP_ENDPOINT_INDEX_PG_ID,
        "cfpb_index_mongo_to_pgvector",
        "index",
        "CCA_MONGO_COMPLAINTS_URL",
        "CCA_PGVECTOR_URL",
        1,
    )



def test_index_cfpb_chroma_workflow_and_endpoint_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'index_cfpb_chroma'"
        ).fetchone()
        bind = db.execute(
            "select id, mio_id, workflow_id from mios_workflows where id = ?",
            (MIOS_WORKFLOWS_ALL_INDEX_CHROMA_ID,),
        ).fetchone()
        ep = db.execute(
            "select id, name, category, from_env_var_name, to_env_var_name, enabled"
            " from app_endpoints where name = 'cfpb_index_mongo_to_chroma'"
        ).fetchone()
    assert row is not None
    assert row[0] == INDEX_CFPB_CHROMA_WORKFLOW_ID
    assert row[1:4] == ("index_cfpb_chroma", "apache_airflow", "index_cfpb_chroma")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "batch_size": 500,
        "vector_backend": "chroma",
        "app_endpoint_name": "cfpb_index_mongo_to_chroma",
    }
    assert row[5] in (1, True)
    assert bind == (MIOS_WORKFLOWS_ALL_INDEX_CHROMA_ID, ALL_MIO_ID, INDEX_CFPB_CHROMA_WORKFLOW_ID)
    assert ep == (
        APP_ENDPOINT_INDEX_CHROMA_ID,
        "cfpb_index_mongo_to_chroma",
        "index",
        "CCA_MONGO_COMPLAINTS_URL",
        "CCA_CHROMA_URL",
        1,
    )


def test_index_cfpb_redis_workflow_and_endpoint_seeded(data_dir):
    with _admin_db(data_dir) as db:
        row = db.execute(
            "select id, workflow_name, engine_type, engine_workflow_id, config, enabled"
            " from app_workflows where workflow_name = 'index_cfpb_redis'"
        ).fetchone()
        bind = db.execute(
            "select id, mio_id, workflow_id from mios_workflows where id = ?",
            (MIOS_WORKFLOWS_ALL_INDEX_REDIS_ID,),
        ).fetchone()
        ep = db.execute(
            "select id, name, category, from_env_var_name, to_env_var_name, enabled"
            " from app_endpoints where name = 'cfpb_index_mongo_to_redis'"
        ).fetchone()
    assert row is not None
    assert row[0] == INDEX_CFPB_REDIS_WORKFLOW_ID
    assert row[1:4] == ("index_cfpb_redis", "apache_airflow", "index_cfpb_redis")
    config = row[4] if isinstance(row[4], dict) else json.loads(row[4])
    assert config == {
        "dataset_code": "CFPB",
        "batch_size": 500,
        "vector_backend": "redis",
        "app_endpoint_name": "cfpb_index_mongo_to_redis",
    }
    assert row[5] in (1, True)
    assert bind == (MIOS_WORKFLOWS_ALL_INDEX_REDIS_ID, ALL_MIO_ID, INDEX_CFPB_REDIS_WORKFLOW_ID)
    assert ep == (
        APP_ENDPOINT_INDEX_REDIS_ID,
        "cfpb_index_mongo_to_redis",
        "index",
        "CCA_MONGO_COMPLAINTS_URL",
        "CCA_REDIS_URL",
        1,
    )



def test_mios_acl_seeded_for_all_and_3_months(data_dir):

    with _admin_db(data_dir) as db:
        rows = db.execute(
            "select id, mio_id, audience from mios_acl order by mio_id, audience"
        ).fetchall()
        sql = _table_sql(db, "mios_acl")
    assert "uq_mios_acl_mio_audience" in sql
    assert "ck_mios_acl_audience" in sql
    assert rows == [
        ("814a15b9-246b-5f8f-baef-a3f75a946a72", ALL_MIO_ID, "internal"),
        ("c57c33d4-f3c6-50a9-b614-5f095d4d7134", MIO_3_MONTHS_ID, "internal"),
    ]
