"""GET /app-endpoints list and read (#156). Open to Admin portal (no callback secret; D59)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.models.app_endpoint_models import AppEndpointIdPath, AppEndpointListQuery, AppEndpointOut
from app.core.common.dtos.app_endpoint_list_dtos import AppEndpointListReq
from app.core.common.dtos.app_endpoint_list_facade_dtos import AppEndpointListFacadeCtx
from app.core.common.return_codes import NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class AppEndpointApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/app-endpoints", tags=["app-endpoints"])
        self.router.add_api_route(
            "",
            self.list,
            methods=["GET"],
            response_model=list[AppEndpointOut],
        )
        self.router.add_api_route(
            "/{id}",
            self.get,
            methods=["GET"],
            response_model=AppEndpointOut,
        )

    def list(self, req: Annotated[AppEndpointListQuery, Query()]) -> list[AppEndpointOut]:
        ctx = AppEndpointListFacadeCtx(
            req=AppEndpointListReq(category=req.category, enabled=req.enabled, name=req.name)
        )
        FacadesObjectsFactory.get_app_endpoint_list_facade().list(ctx)
        self._check_list(ctx)
        return [AppEndpointOut.model_validate(e) for e in ctx.resp.entries]

    def get(self, req: Annotated[AppEndpointIdPath, Depends()]) -> AppEndpointOut:
        ctx = AppEndpointListFacadeCtx(req=AppEndpointListReq(id=req.id))
        FacadesObjectsFactory.get_app_endpoint_list_facade().get(ctx)
        self._check_get(ctx)
        return AppEndpointOut.model_validate(ctx.resp.entries[0])

    @staticmethod
    def _check_list(ctx: AppEndpointListFacadeCtx) -> None:
        if ctx.resp.code == SUCCESS:
            return
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")

    @staticmethod
    def _check_get(ctx: AppEndpointListFacadeCtx) -> None:
        if ctx.resp.code == SUCCESS:
            return
        if ctx.resp.code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "app endpoint not found")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
