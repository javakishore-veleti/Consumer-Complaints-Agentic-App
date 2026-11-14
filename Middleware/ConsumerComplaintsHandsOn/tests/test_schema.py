import sqlite3

from app.core.common.config import ALL_SCHEMAS


def test_schema_names():
    assert ALL_SCHEMAS == ("consumer_comp_db", "consumer_compl_intellect_db", "consumer_comp_users_db")


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
