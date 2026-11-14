import sqlite3

from alembic import command
from alembic.config import Config

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT


def test_schema_names():
    assert ALL_SCHEMAS == (
        "consumer_comp_db",
        "consumer_compl_intellect_db",
        "consumer_comp_users_db",
        "consumer_comp_admin_db",
    )


def test_migration_creates_all_schemas_and_the_table_in_the_complaints_schema(data_dir):
    for schema in ALL_SCHEMAS:
        assert (data_dir / f"{schema}.sqlite").exists()

    with sqlite3.connect(data_dir / "consumer_comp_db.sqlite") as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    assert "data_ingest_log" in tables


def test_system_datasets_is_seeded_with_one_not_started_row_per_dataset_and_stage(data_dir):
    with sqlite3.connect(data_dir / "consumer_comp_db.sqlite") as db:
        rows = db.execute("select dataset, stage, status, last_log_id from system_datasets order by dataset, stage").fetchall()
    assert rows == [
        ("3_months", "db_ingest", "not_started", None),
        ("3_months", "download", "not_started", None),
        ("all", "db_ingest", "not_started", None),
        ("all", "download", "not_started", None),
    ]


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
