"""POST /management/airflow/upsert-secrets (D42). Open to the Admin portal (no callback secret; D59)."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.models.airflow_upsert_secrets_models import UpsertSecretResultOut, UpsertSecretsOut
from app.core.common.dtos.airflow_upsert_secrets_facade_dtos import AirflowUpsertSecretsFacadeCtx
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class AirflowUpsertSecretsApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/management/airflow", tags=["management"])
        self.router.add_api_route(
            "/upsert-secrets",
            self.upsert_secrets,
            methods=["POST"],
            response_model=UpsertSecretsOut,
        )

    def upsert_secrets(self) -> UpsertSecretsOut | JSONResponse:
        ctx = AirflowUpsertSecretsFacadeCtx()
        FacadesObjectsFactory.get_airflow_upsert_secrets_facade().upsert(ctx)
        out = UpsertSecretsOut(
            results=[UpsertSecretResultOut(name=r.name, outcome=r.outcome) for r in ctx.resp.results]
        )
        if ctx.resp.code == SUCCESS:
            return out
        if ctx.resp.code == FAILURE and any(r.outcome == "missing" for r in ctx.resp.results):
            return JSONResponse(status_code=422, content=out.model_dump())
        if ctx.resp.code == FAILURE:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "airflow variables upsert failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
