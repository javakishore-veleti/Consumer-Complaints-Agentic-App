from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.impl.tasks.airflow_upsert_secrets_call_service_task import (
    AirflowUpsertSecretsCallServiceTask,
)


class AirflowUpsertSecretsFacadeImpl(AirflowUpsertSecretsFacade):
    def __init__(self):
        self._tasks = [AirflowUpsertSecretsCallServiceTask()]

    def upsert(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ctx.resp.code = SUCCESS
        for task in self._tasks:
            code = task.execute(ctx)
            if code != SUCCESS:
                ctx.resp.code = code
                break
        return ctx.resp.code
