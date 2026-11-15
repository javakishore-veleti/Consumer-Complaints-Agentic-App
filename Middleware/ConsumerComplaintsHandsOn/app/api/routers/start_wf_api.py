"""The portal's start of any registered workflow (D29, D68). Singleton. No callback secret (D59)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.start_wf_models import StartWfOut, StartWfReq
from app.core.common.dtos.start_wf_dtos import StartWfReq as StartWfServiceReq
from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class StartWfApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/workflows", tags=["workflows"])
        self.router.add_api_route(
            "/{workflow_id}/start",
            self.start,
            methods=["POST"],
            response_model=StartWfOut,
            status_code=status.HTTP_202_ACCEPTED,
        )

    def start(self, req: Annotated[StartWfReq, Depends()]) -> StartWfOut:
        ctx = StartWfFacadeCtx(
            req=StartWfServiceReq(
                workflow_id=req.workflow_id,
                mio_id=req.body.mio_id,
                dataset_location_id=req.body.dataset_location_id,
            )
        )
        FacadesObjectsFactory.get_start_wf_facade().start(ctx)
        self._check(ctx)
        return StartWfOut(execution_id=ctx.resp.execution_id or "")

    @staticmethod
    def _check(ctx: StartWfFacadeCtx) -> None:
        if ctx.resp.code == SUCCESS:
            return
        if ctx.resp.code == INVALID_INPUT:
            raise HTTPException(422, "invalid request")
        if ctx.resp.code == FAILURE:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "engine start failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
