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
