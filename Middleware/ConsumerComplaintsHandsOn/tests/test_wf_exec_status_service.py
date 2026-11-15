"""The status an engine reports for one execution (D60): the execution log and its MIO ingest row change together, and
duplicate, out-of-order and late reports are harmless (D30)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq
from app.core.common.dtos.wf_exec_status_facade_dtos import WfExecStatusFacadeCtx
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.sqlalchemy_mio_ingest_log_dao import SqlAlchemyMioIngestLogDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_MIO = "Customer complaints 3 months 2026"


def _report(req: WfExecStatusReq) -> WfExecStatusCtx:
    ctx = WfExecStatusCtx(req=req)
    ServicesObjectsFactory.get_wf_exec_status_service().record(ctx)
    return ctx


def _execution(execution_id):
    ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


def _ingest(ingest_id):
    ctx = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0]


@pytest.fixture
def workflow_id(data_dir):
    ctx = AppWfCtx(req=AppWfReq(workflow_name="t_ingest", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def ingest_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def new_execution(workflow_id):
    """Creates an execution of the workflow; pass an ingest id to attach it to that ingest."""

    def create(ingest=None):
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=ingest))
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    return create


# ---- input


@pytest.mark.parametrize("status", ["requested", "running", "", None])
def test_only_started_completed_and_failed_can_be_reported(new_execution, status):
    execution_id = new_execution()
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status=status))
    assert ctx.resp.code == INVALID_INPUT
    assert (ctx.resp.execution, ctx.resp.ingest) == (None, None)
    assert _execution(execution_id).status == "requested"


@pytest.mark.parametrize("execution_id", [None, "", "   "])
def test_a_blank_execution_id_is_invalid(data_dir, execution_id):
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == INVALID_INPUT


def test_an_unknown_execution_is_not_found(data_dir):
    assert _report(WfExecStatusReq(execution_id="no-such-execution", status="started")).resp.code == NOT_FOUND


def test_a_too_long_engine_run_id_is_invalid_and_changes_nothing(new_execution):
    execution_id = new_execution()
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", engine_run_id="r" * 129))
    assert ctx.resp.code == INVALID_INPUT
    assert _execution(execution_id).status == "requested"


# ---- an execution without an ingest row


def test_an_execution_without_an_ingest_changes_only_the_execution(new_execution):
    execution_id = new_execution()
    started = _report(
        WfExecStatusReq(execution_id=execution_id, status="started", engine_run_id="run-1", rows_loaded=10)
    )
    assert started.resp.code == SUCCESS
    assert started.resp.ingest is None  # the volume fields are ignored: there is no ingest row
    assert (started.resp.execution.status, started.resp.execution.engine_run_id) == ("started", "run-1")
    assert started.resp.execution.started_at is not None
    done = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="ok"))
    assert done.resp.code == SUCCESS
    assert (done.resp.execution.status, done.resp.execution.message) == ("completed", "ok")
    assert done.resp.execution.finished_at is not None


def test_a_repeated_report_is_success_and_keeps_the_times(new_execution):
    execution_id = new_execution()
    first = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    again = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    assert again.resp.code == SUCCESS
    assert again.resp.execution.started_at == first.resp.execution.started_at


def test_an_out_of_order_report_is_a_conflict_and_changes_nothing(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="m", rows_loaded=5))
    assert ctx.resp.code == CONFLICT
    assert (ctx.resp.execution, ctx.resp.ingest) == (None, None)
    assert (_execution(execution_id).status, _execution(execution_id).message) == ("requested", None)
    assert (_ingest(ingest_id).status, _ingest(ingest_id).rows_loaded) == ("requested", None)


# ---- the ingest follows its executions


def test_started_moves_a_requested_ingest_to_started(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", message="go", batch_count=2))
    assert ctx.resp.code == SUCCESS
    assert ctx.resp.execution.status == "started"
    assert (ctx.resp.ingest.id, ctx.resp.ingest.status) == (ingest_id, "started")
    assert (ctx.resp.ingest.message, ctx.resp.ingest.batch_count) == ("go", 2)
    assert ctx.resp.ingest.started_at is not None


def test_a_second_execution_starting_leaves_a_started_ingest_and_its_message_alone(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    before = _report(WfExecStatusReq(execution_id=first, status="started", message="first")).resp.ingest
    after = _report(WfExecStatusReq(execution_id=second, status="started", message="second")).resp.ingest
    assert (after.status, after.started_at, after.message) == ("started", before.started_at, "first")


def test_completed_moves_the_ingest_only_when_every_execution_is_completed(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    for execution_id in (first, second):
        assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == SUCCESS
    one = _report(WfExecStatusReq(execution_id=first, status="completed", rows_loaded=100))
    assert one.resp.code == SUCCESS
    assert (one.resp.ingest.status, one.resp.ingest.rows_loaded) == ("started", 100)  # the volume is a note
    both = _report(WfExecStatusReq(execution_id=second, status="completed", message="all done", rows_loaded=250))
    assert both.resp.code == SUCCESS
    ingest = both.resp.ingest
    assert (ingest.status, ingest.message, ingest.rows_loaded) == ("completed", "all done", 250)
    assert ingest.finished_at is not None


def test_failed_moves_the_ingest_to_failed_with_the_message(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=first, status="started"))
    failed = _report(WfExecStatusReq(execution_id=first, status="failed", message="disk full"))
    assert failed.resp.code == SUCCESS
    assert (failed.resp.ingest.status, failed.resp.ingest.message) == ("failed", "disk full")
    assert _execution(second).status == "requested"  # other executions are not touched


def test_failed_from_requested_fails_a_requested_ingest(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="failed", message="could not start"))
    assert ctx.resp.code == SUCCESS
    assert (ctx.resp.execution.status, ctx.resp.ingest.status) == ("failed", "failed")


def test_a_final_ingest_is_left_alone_but_the_execution_moves_and_the_volume_is_written(new_execution, ingest_id):
    first, second = new_execution(ingest_id), new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=first, status="failed", message="boom"))
    started = _report(WfExecStatusReq(execution_id=second, status="started", message="late"))
    assert started.resp.code == SUCCESS and started.resp.execution.status == "started"
    done = _report(WfExecStatusReq(execution_id=second, status="completed", increment_marker="2026-03-31"))
    assert done.resp.code == SUCCESS and done.resp.execution.status == "completed"
    ingest = done.resp.ingest
    assert (ingest.status, ingest.message, ingest.increment_marker) == ("failed", "boom", "2026-03-31")


def test_duplicate_reports_after_the_ingest_completed_are_success_and_change_nothing(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    first = _report(WfExecStatusReq(execution_id=execution_id, status="completed", message="done")).resp
    again = _report(WfExecStatusReq(execution_id=execution_id, status="completed"))
    assert again.resp.code == SUCCESS
    assert again.resp.ingest == first.ingest
    assert again.resp.execution.finished_at == first.execution.finished_at
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == CONFLICT
    assert _ingest(ingest_id) == first.ingest


def test_a_late_failed_after_completed_is_a_conflict_and_keeps_both_rows(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    _report(WfExecStatusReq(execution_id=execution_id, status="completed"))
    late = _report(WfExecStatusReq(execution_id=execution_id, status="failed", message="late", rows_loaded=1))
    assert late.resp.code == CONFLICT
    assert (_execution(execution_id).status, _execution(execution_id).message) == ("completed", None)
    assert (_ingest(ingest_id).status, _ingest(ingest_id).rows_loaded) == ("completed", None)


# ---- one transaction


def test_an_invalid_volume_rolls_back_the_execution_too(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started", rows_loaded=-1))
    assert ctx.resp.code == INVALID_INPUT
    assert _execution(execution_id).status == "requested"
    assert _ingest(ingest_id).status == "requested"


def test_if_the_ingest_write_fails_the_execution_is_not_changed(new_execution, ingest_id, monkeypatch):
    execution_id = new_execution(ingest_id)

    def broken(self, ctx):
        raise RuntimeError("disk error")

    monkeypatch.setattr(SqlAlchemyMioIngestLogDao, "update", broken)
    ctx = _report(WfExecStatusReq(execution_id=execution_id, status="started"))
    assert ctx.resp.code == FAILURE and ctx.resp.execution is None
    monkeypatch.undo()
    assert _execution(execution_id).status == "requested"
    assert _ingest(ingest_id).status == "requested"


def test_an_ingest_conflict_is_a_failure_not_the_executions_conflict(new_execution, ingest_id, monkeypatch):
    execution_id = new_execution(ingest_id)
    monkeypatch.setattr(SqlAlchemyMioIngestLogDao, "update", lambda self, ctx: CONFLICT)
    assert _report(WfExecStatusReq(execution_id=execution_id, status="started")).resp.code == FAILURE
    monkeypatch.undo()
    assert _execution(execution_id).status == "requested"


# ---- the facade


def test_the_facade_hands_the_report_to_the_service(new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    ctx = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id=execution_id, status="started"))
    assert FacadesObjectsFactory.get_wf_exec_status_facade().report(ctx) == SUCCESS
    assert ctx.resp.code == SUCCESS
    assert (ctx.resp.execution.status, ctx.resp.ingest.status) == ("started", "started")
    missing = WfExecStatusFacadeCtx(req=WfExecStatusReq(execution_id="no-such-execution", status="started"))
    assert FacadesObjectsFactory.get_wf_exec_status_facade().report(missing) == NOT_FOUND
    assert missing.resp.code == NOT_FOUND
