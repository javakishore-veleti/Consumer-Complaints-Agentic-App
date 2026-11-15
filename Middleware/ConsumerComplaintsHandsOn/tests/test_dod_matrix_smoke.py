"""DoD matrix (M03-0013): pin SQLite / Postgres / Mongo smoke entrypoints."""


def test_dod_matrix_smoke_entrypoints_exist():
    from tests import test_e2e_happy_path_smoke as sqlite_mod
    from tests import test_mongodb_operational_store as mongo_mod
    from tests import test_postgres as pg_mod

    assert callable(sqlite_mod.test_happy_path_start_callback_mios_status)
    assert callable(pg_mod.test_start_workflow_and_callback_persist_on_postgres)
    assert callable(mongo_mod.test_start_workflow_and_callback_persist_on_mongo)
