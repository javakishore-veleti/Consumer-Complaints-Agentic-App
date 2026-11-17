"""Apache Airflow WorkflowEngine: delegates to AirflowStartDagService (#60 / D73)."""

from app.core.common.app_types_constants import EngineType
from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx, AirflowStartDagReq
from app.core.common.dtos.workflow_engine_dtos import WorkflowEngineCtx
from app.core.services.objects_factory import ServicesObjectsFactory
from app.core.services.workflow_engine import WorkflowEngine


class ApacheAirflowWorkflowEngineImpl(WorkflowEngine):
    @property
    def engine_type(self) -> str:
        return EngineType.APACHE_AIRFLOW.value

    def start(self, ctx: WorkflowEngineCtx) -> int:
        af_ctx = AirflowStartDagCtx(
            req=AirflowStartDagReq(
                execution_id=ctx.req.execution_id,
                dag_conf=dict(ctx.req.dag_conf or {}),
            )
        )
        code = ServicesObjectsFactory.get_airflow_start_dag_service().start(af_ctx)
        ctx.resp.engine_run_id = af_ctx.resp.engine_run_id
        ctx.resp.code = code
        return code
