from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx
from app.core.common.dtos.airflow_start_dag_facade_dtos import AirflowStartDagFacadeCtx
from app.core.facades.airflow_start_dag_facade_task import AirflowStartDagFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class AirflowStartDagCallServiceTask(AirflowStartDagFacadeTask):
    def execute(self, ctx: AirflowStartDagFacadeCtx) -> int:
        ctx.start_ctx = AirflowStartDagCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_airflow_start_dag_service().start(ctx.start_ctx)
        ctx.resp.engine_run_id = ctx.start_ctx.resp.engine_run_id
        ctx.resp.code = code
        return code
