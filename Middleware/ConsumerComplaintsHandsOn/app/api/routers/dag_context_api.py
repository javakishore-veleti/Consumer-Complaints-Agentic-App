"""GET /callbacks/workflow-executions/{id}/dag-context — ops config for Airflow DAGs."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.dag_context_models import DagContextGetReq, DagContextOut
from app.core.common.dtos.dag_context_dtos import DagContextCtx, DagContextReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class DagContextApi(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/callbacks", tags=["callbacks"])
        self.router.add_api_route(
            "/workflow-executions/{execution_id}/dag-context",
            self.get_dag_context,
            methods=["GET"],
            response_model=DagContextOut,
        )

    def get_dag_context(self, req: Annotated[DagContextGetReq, Depends()]) -> DagContextOut:
        ctx = DagContextCtx(
            req=DagContextReq(
                execution_id=req.execution_id,
                app_endpoint_name=req.app_endpoint,
            )
        )
        FacadesObjectsFactory.get_dag_context_facade().get(ctx)
        code = ctx.resp.code
        if code == SUCCESS:
            return DagContextOut(
                execution_id=req.execution_id,
                config_used=ctx.resp.config_used or {},
                dataset_locations=ctx.resp.dataset_locations,
                app_endpoint=ctx.resp.app_endpoint,
            )
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow execution or related row not found")
        if code == INVALID_INPUT:
            raise HTTPException(422, "invalid dag context request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
