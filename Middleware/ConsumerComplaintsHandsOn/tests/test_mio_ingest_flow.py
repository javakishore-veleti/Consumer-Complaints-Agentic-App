from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import CONFLICT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def test_one_ingest_of_a_seeded_mio_served_by_several_executions(data_dir):
    ingests = DaoObjectsFactory.get_mio_ingest_log_dao()
    executions = DaoObjectsFactory.get_app_wf_exec_log_dao()
    mio = MioCtx(req=MioReq(name="Customer complaints 3 months 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_ingest", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS
    workflow_id = workflow.resp.records[0].id

    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, batch_count=2))
    assert ingests.create(ingest) == SUCCESS
    ingest_id = ingest.resp.records[0].id
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="started"))) == SUCCESS

    def execute():
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=ingest_id))
        assert executions.create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    def move(exec_id, status):
        return executions.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=exec_id, status=status)))

    first = execute()
    assert move(first, "started") == SUCCESS and move(first, "failed") == SUCCESS
    rerun = execute()
    assert move(rerun, "started") == SUCCESS and move(rerun, "completed") == SUCCESS

    # The caller decides the ingest's status (D58); the DAO does not derive it from the executions.
    still = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert ingests.get(still) == SUCCESS and still.resp.records[0].status == "started"
    done = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="completed", rows_loaded=1500))
    assert ingests.update(done) == SUCCESS
    late = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id, status="failed"))
    assert ingests.update(late) == CONFLICT

    served = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=ingest_id))
    assert executions.list(served) == SUCCESS
    assert sorted((r.id, r.status) for r in served.resp.records) == sorted([(first, "failed"), (rerun, "completed")])
    of_mio = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id))
    assert ingests.list(of_mio) == SUCCESS
    assert [(r.id, r.status, r.rows_loaded, r.batch_count) for r in of_mio.resp.records] == [
        (ingest_id, "completed", 1500, 2)
    ]
