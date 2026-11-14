from app.core.common.dataset_constants import USECASE_DOWNLOAD_3_MONTHS, USECASE_DOWNLOAD_ALL, USECASE_INGEST_ALL
from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestReq
from app.core.common.dtos.dataset_status_dtos import DatasetStatusCtx, DatasetStatusReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.sqlalchemy_system_datasets_dao import SqlAlchemySystemDatasetsDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory


def _ctx(req: DatasetStatusReq) -> DatasetStatusCtx:
    return DatasetStatusCtx(req=req)


def _service():
    return ServicesObjectsFactory.get_dataset_status_service()


def _rows(data_dir):
    ctx = DatasetStatusCtx()
    assert _service().read(ctx) == SUCCESS
    return {(r.dataset, r.stage): r for r in ctx.resp.records}


def _logs(purpose):
    ctx = DataIngestCtx(req=DataIngestReq(purpose=purpose))
    assert DaoObjectsFactory.get_data_ingest_dao().list(ctx) == SUCCESS
    return ctx.resp.records


def test_request_writes_the_log_and_sets_the_dataset_running(data_dir):
    ctx = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_3_MONTHS))
    assert _service().request(ctx) == SUCCESS and ctx.resp.code == SUCCESS
    assert ctx.resp.log.status == "requested" and ctx.resp.log.purpose == USECASE_DOWNLOAD_3_MONTHS
    row = _rows(data_dir)[("3_months", "download")]
    assert (row.status, row.last_log_id) == ("running", ctx.resp.log.id)
    assert _rows(data_dir)[("all", "download")].status == "not_started"  # other rows untouched


def test_a_second_request_while_running_is_a_conflict_and_writes_nothing(data_dir):
    assert _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL))) == SUCCESS
    assert _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL))) == CONFLICT
    assert len(_logs(USECASE_DOWNLOAD_ALL)) == 1


def test_unknown_usecase_and_bad_reports_are_rejected(data_dir):
    assert _service().request(_ctx(DatasetStatusReq(usecase="bogus"))) == INVALID_INPUT
    assert _service().request(_ctx(DatasetStatusReq())) == INVALID_INPUT
    assert _service().record(_ctx(DatasetStatusReq(usecase="bogus", status="started"))) == INVALID_INPUT
    assert _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="requested"))) == INVALID_INPUT
    assert _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="started"))) == NOT_FOUND  # never requested


def test_full_run_started_then_completed(data_dir):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL)))
    started = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="started", run_id="run-1"))
    assert _service().record(started) == SUCCESS
    assert started.resp.log.started_at is not None and started.resp.log.run_id == "run-1"
    assert _rows(data_dir)[("all", "download")].status == "running"
    done = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="completed", run_id="run-1"))
    assert _service().record(done) == SUCCESS
    assert done.resp.log.finished_at is not None
    assert _rows(data_dir)[("all", "download")].status == "completed"
    # the dataset can be run again once it is not running
    assert _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL))) == SUCCESS
    assert _rows(data_dir)[("all", "download")].status == "running"
    assert len(_logs(USECASE_DOWNLOAD_ALL)) == 2


def test_failure_is_shown_with_the_message(data_dir):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_INGEST_ALL)))
    failed = _ctx(DatasetStatusReq(usecase=USECASE_INGEST_ALL, status="failed", message="disk full"))
    assert _service().record(failed) == SUCCESS
    assert failed.resp.log.message == "disk full"
    assert _rows(data_dir)[("all", "db_ingest")].status == "failed"


def test_a_repeated_report_is_accepted_and_changes_nothing(data_dir):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL)))
    _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="started")))
    first = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="completed"))
    assert _service().record(first) == SUCCESS
    again = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="completed"))
    assert _service().record(again) == SUCCESS
    assert again.resp.log.finished_at == first.resp.log.finished_at
    assert _rows(data_dir)[("all", "download")].status == "completed"


def test_out_of_order_report_is_a_conflict_and_changes_neither_table(data_dir):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL)))
    assert _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="completed"))) == CONFLICT  # not started yet
    assert _logs(USECASE_DOWNLOAD_ALL)[0].status == "requested"
    assert _rows(data_dir)[("all", "download")].status == "running"


def test_a_report_from_an_older_run_is_refused(data_dir):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL)))
    _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="started", run_id="run-2")))
    assert _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="failed", run_id="run-1"))) == CONFLICT
    assert _logs(USECASE_DOWNLOAD_ALL)[0].status == "started"


def test_request_is_one_transaction_if_the_dataset_write_fails_the_log_is_not_kept(data_dir, monkeypatch):
    def broken(self, ctx):
        raise RuntimeError("disk error")

    monkeypatch.setattr(SqlAlchemySystemDatasetsDao, "update", broken)
    ctx = _ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL))
    assert _service().request(ctx) == FAILURE and ctx.resp.code == FAILURE
    monkeypatch.undo()
    assert _logs(USECASE_DOWNLOAD_ALL) == []  # the log row was rolled back with it
    assert _rows(data_dir)[("all", "download")].status == "not_started"


def test_record_is_one_transaction_if_the_dataset_write_fails_the_log_is_not_changed(data_dir, monkeypatch):
    _service().request(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL)))

    def broken(self, ctx):
        raise RuntimeError("disk error")

    monkeypatch.setattr(SqlAlchemySystemDatasetsDao, "update", broken)
    assert _service().record(_ctx(DatasetStatusReq(usecase=USECASE_DOWNLOAD_ALL, status="started"))) == FAILURE
    monkeypatch.undo()
    assert _logs(USECASE_DOWNLOAD_ALL)[0].status == "requested"
    assert _rows(data_dir)[("all", "download")].status == "running"
