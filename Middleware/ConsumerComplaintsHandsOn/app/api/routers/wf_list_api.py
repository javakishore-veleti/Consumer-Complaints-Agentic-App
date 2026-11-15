"""The portal's list of every registered workflow (D29, D66). Singleton. No callback secret (D59)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.models.wf_list_models import WfListOut, WfListReq
from app.core.common.dtos.wf_list_dtos import WfListReq as WfListServiceReq
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class WfListApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/workflows", tags=["workflows"])
        self.router.add_api_route(
            "",
            self.list,
            methods=["GET"],
            response_model=list[WfListOut],
        )

    def list(self, req: Annotated[WfListReq, Query()]) -> list[WfListOut]:
        ctx = WfListFacadeCtx(req=WfListServiceReq())
        FacadesObjectsFactory.get_wf_list_facade().list(ctx)
        self._check(ctx)
        return [WfListOut.model_validate(e) for e in ctx.resp.entries]

    @staticmethod
    def _check(ctx: WfListFacadeCtx) -> None:
        if ctx.resp.code == SUCCESS:
            return
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
