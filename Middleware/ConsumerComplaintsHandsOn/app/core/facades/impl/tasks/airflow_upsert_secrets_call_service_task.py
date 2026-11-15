from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowUpsertSecretsCtx
from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.facades.airflow_upsert_secrets_facade_task import AirflowUpsertSecretsFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class AirflowUpsertSecretsCallServiceTask(AirflowUpsertSecretsFacadeTask):
    def execute(self, ctx: AirflowUpsertSecretsFacadeCtx) -> int:
        ctx.service_ctx = AirflowUpsertSecretsCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx.service_ctx)
        ctx.resp = ctx.service_ctx.resp
        return code
