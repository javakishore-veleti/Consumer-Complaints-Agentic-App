from app.core.common.dtos.airflow_start_dag_dtos import (
    AirflowDagRunTriggerCtx,
    AirflowDagRunTriggerReq,
    AirflowStartDagCtx,
)
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.airflow_start_dag_service import AirflowStartDagService
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient


class AirflowStartDagServiceImpl(AirflowStartDagService):
    def __init__(self, client: AirflowDagRunsClient | None = None):
        self._client = client or AirflowDagRunsClient()

    def start(self, ctx: AirflowStartDagCtx) -> int:
        ctx.resp.engine_run_id = None
        execution_id = (ctx.req.execution_id or "").strip()
        if not execution_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        elog = DaoObjectsFactory.get_app_wf_exec_log_dao()
        get_ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
        code = elog.get(get_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        row = get_ctx.resp.records[0]
        dag_id = (row.engine_workflow_id or "").strip()
        if not dag_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        trigger = AirflowDagRunTriggerCtx(
            req=AirflowDagRunTriggerReq(dag_id=dag_id, execution_id=execution_id)
        )
        code = self._client.trigger(trigger)
        if code != SUCCESS or not trigger.resp.dag_run_id:
            ctx.resp.code = FAILURE
            return FAILURE
        upd = AppWfExecLogCtx(
            req=AppWfExecLogReq(id=execution_id, engine_run_id=trigger.resp.dag_run_id)
        )
        code = elog.update(upd)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.engine_run_id = trigger.resp.dag_run_id
        ctx.resp.code = SUCCESS
        return SUCCESS
