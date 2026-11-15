from dataclasses import dataclass, field

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    AirflowUpsertSecretsCtx,
    AirflowUpsertSecretsReq,
    AirflowUpsertSecretsResp,
)


@dataclass
class AirflowUpsertSecretsFacadeCtx:
    req: AirflowUpsertSecretsReq = field(default_factory=AirflowUpsertSecretsReq)
    resp: AirflowUpsertSecretsResp = field(default_factory=AirflowUpsertSecretsResp)
    service_ctx: AirflowUpsertSecretsCtx = field(default_factory=AirflowUpsertSecretsCtx)
