"""Triggers Airflow through the #60 AirflowStartDagFacade (af_start)."""

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagReq
from app.core.common.dtos.airflow_start_dag_facade_dtos import AirflowStartDagFacadeCtx
from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.return_codes import INVALID_INPUT
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.facades.start_wf_facade_task import StartWfFacadeTask


class StartWfTriggerEngineTask(StartWfFacadeTask):
    def execute(self, ctx: StartWfFacadeCtx) -> int:
        execution_id = ctx.resp.execution_id
        if not execution_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        engine_ctx = AirflowStartDagFacadeCtx(req=AirflowStartDagReq(execution_id=execution_id))
        code = FacadesObjectsFactory.get_airflow_start_dag_facade().start(engine_ctx)
        ctx.resp.code = code
        return code
