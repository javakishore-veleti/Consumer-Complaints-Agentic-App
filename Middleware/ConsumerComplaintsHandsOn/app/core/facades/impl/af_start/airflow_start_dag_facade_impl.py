from app.core.common.dtos.airflow_start_dag_facade_dtos import AirflowStartDagFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.airflow_start_dag_facade import AirflowStartDagFacade
from app.core.facades.impl.af_start.tasks.airflow_start_dag_call_service_task import (
    AirflowStartDagCallServiceTask,
)


class AirflowStartDagFacadeImpl(AirflowStartDagFacade):
    def __init__(self):
        self._tasks = [AirflowStartDagCallServiceTask()]

    def start(self, ctx: AirflowStartDagFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
