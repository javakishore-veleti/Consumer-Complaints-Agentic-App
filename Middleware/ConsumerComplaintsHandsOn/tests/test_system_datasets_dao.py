from app.core.common.dtos.system_datasets_dtos import SystemDatasetsCtx, SystemDatasetsReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(req: SystemDatasetsReq) -> SystemDatasetsCtx:
    return SystemDatasetsCtx(req=req)


def test_list_returns_the_four_seeded_rows_in_order(data_dir):
    listed = _ctx(SystemDatasetsReq())
    assert DaoObjectsFactory.get_system_datasets_dao().list(listed) == SUCCESS
    assert [(r.dataset, r.stage, r.status) for r in listed.resp.records] == [
        ("3_months", "db_ingest", "not_started"),
        ("3_months", "download", "not_started"),
        ("all", "db_ingest", "not_started"),
        ("all", "download", "not_started"),
    ]
    assert all(r.updated_at.tzinfo is not None for r in listed.resp.records)


def test_list_filters(data_dir):
    dao = DaoObjectsFactory.get_system_datasets_dao()
    by_dataset = _ctx(SystemDatasetsReq(dataset="all"))
    assert dao.list(by_dataset) == SUCCESS and len(by_dataset.resp.records) == 2
    by_stage = _ctx(SystemDatasetsReq(stage="download"))
    assert dao.list(by_stage) == SUCCESS and {r.dataset for r in by_stage.resp.records} == {"3_months", "all"}


def test_get_update_and_the_time_it_changed(data_dir):
    dao = DaoObjectsFactory.get_system_datasets_dao()
    before = _ctx(SystemDatasetsReq(dataset="3_months", stage="download"))
    assert dao.get(before) == SUCCESS
    updated = _ctx(SystemDatasetsReq(dataset="3_months", stage="download", status="running", last_log_id="abc"))
    assert dao.update(updated) == SUCCESS
    row = updated.resp.records[0]
    assert (row.status, row.last_log_id) == ("running", "abc")
    assert row.updated_at >= before.resp.records[0].updated_at
    other = _ctx(SystemDatasetsReq(dataset="all", stage="download"))
    assert dao.get(other) == SUCCESS and other.resp.records[0].status == "not_started"  # only one row changed


def test_missing_and_invalid_input(data_dir):
    dao = DaoObjectsFactory.get_system_datasets_dao()
    assert dao.get(_ctx(SystemDatasetsReq(dataset="nope", stage="download"))) == NOT_FOUND
    assert dao.get(_ctx(SystemDatasetsReq(dataset="all"))) == INVALID_INPUT
    assert dao.update(_ctx(SystemDatasetsReq(dataset="nope", stage="download", status="running"))) == NOT_FOUND
    assert dao.update(_ctx(SystemDatasetsReq(dataset="all", stage="download", status="bogus"))) == INVALID_INPUT
    assert dao.create(_ctx(SystemDatasetsReq(dataset="x"))) == INVALID_INPUT
    assert dao.create(_ctx(SystemDatasetsReq(dataset="x", stage="y", status="bogus"))) == INVALID_INPUT


def test_create_and_delete(data_dir):
    dao = DaoObjectsFactory.get_system_datasets_dao()
    created = _ctx(SystemDatasetsReq(dataset="6_months", stage="download"))
    assert dao.create(created) == SUCCESS and created.resp.records[0].status == "not_started"
    assert dao.create(_ctx(SystemDatasetsReq(dataset="6_months", stage="download"))) == CONFLICT
    deleted = _ctx(SystemDatasetsReq(dataset="6_months", stage="download"))
    assert dao.delete(deleted) == SUCCESS and deleted.resp.records[0].dataset == "6_months"
    assert dao.get(_ctx(SystemDatasetsReq(dataset="6_months", stage="download"))) == NOT_FOUND
