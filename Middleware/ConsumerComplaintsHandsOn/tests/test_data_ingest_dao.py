from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def _ctx(**fields) -> DataIngestCtx:
    return DataIngestCtx(req=DataIngestReq(**fields))


def test_create_then_get(data_dir):
    dao = DaoObjectsFactory.get_data_ingest_dao()
    created = _ctx(purpose="download_3_months")
    assert dao.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.status == "requested"
    assert row.requested_at is not None and row.requested_at.tzinfo is not None
    assert row.started_at is None and row.finished_at is None

    fetched = _ctx(id=row.id)
    assert dao.get(fetched) == SUCCESS
    assert fetched.resp.records[0] == row


def test_create_needs_purpose(data_dir):
    assert DaoObjectsFactory.get_data_ingest_dao().create(_ctx()) == INVALID_INPUT


def test_get_missing_and_missing_id(data_dir):
    dao = DaoObjectsFactory.get_data_ingest_dao()
    assert dao.get(_ctx(id="nope")) == NOT_FOUND
    assert dao.get(_ctx()) == INVALID_INPUT


def test_update_sets_timestamps_from_status(data_dir):
    dao = DaoObjectsFactory.get_data_ingest_dao()
    created = _ctx(purpose="download_all")
    dao.create(created)
    log_id = created.resp.records[0].id

    started = _ctx(id=log_id, status="started", run_id="run-1")
    assert dao.update(started) == SUCCESS
    assert started.resp.records[0].started_at is not None
    assert started.resp.records[0].finished_at is None
    assert started.resp.records[0].run_id == "run-1"

    failed = _ctx(id=log_id, status="failed", message="boom")
    assert dao.update(failed) == SUCCESS
    row = failed.resp.records[0]
    assert row.finished_at is not None
    assert row.message == "boom"
    assert row.run_id == "run-1"  # fields not given are left alone


def test_update_missing(data_dir):
    assert DaoObjectsFactory.get_data_ingest_dao().update(_ctx(id="nope", status="started")) == NOT_FOUND


def test_list_filters_and_paging(data_dir):
    dao = DaoObjectsFactory.get_data_ingest_dao()
    for purpose in ("download_3_months", "download_all", "download_all"):
        dao.create(_ctx(purpose=purpose))

    everything = _ctx()
    assert dao.list(everything) == SUCCESS
    assert len(everything.resp.records) == 3

    only_all = _ctx(purpose="download_all")
    dao.list(only_all)
    assert [r.purpose for r in only_all.resp.records] == ["download_all", "download_all"]

    none_started = _ctx(status="started")
    dao.list(none_started)
    assert none_started.resp.records == []

    page = _ctx(limit=1, offset=1)
    dao.list(page)
    assert len(page.resp.records) == 1


def test_delete(data_dir):
    dao = DaoObjectsFactory.get_data_ingest_dao()
    created = _ctx(purpose="download_all")
    dao.create(created)
    log_id = created.resp.records[0].id

    deleted = _ctx(id=log_id)
    assert dao.delete(deleted) == SUCCESS
    assert deleted.resp.records[0].id == log_id
    assert dao.get(_ctx(id=log_id)) == NOT_FOUND
    assert dao.delete(_ctx(id=log_id)) == NOT_FOUND
