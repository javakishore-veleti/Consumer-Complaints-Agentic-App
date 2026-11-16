"""POST /intellect/query — local vector search for Intellect portal (D90). No callback secret."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from app.api.models.intellect_query_models import IntellectHitOut, IntellectQueryBody, IntellectQueryOut
from app.core.common.dtos.intellect_query_dtos import IntellectQueryReq
from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class IntellectQueryApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/intellect", tags=["intellect"])
        self.router.add_api_route(
            "/query",
            self.query,
            methods=["POST"],
            response_model=IntellectQueryOut,
        )

    def query(self, body: IntellectQueryBody) -> IntellectQueryOut:
        ctx = IntellectQueryFacadeCtx(
            req=IntellectQueryReq(query=body.query, limit=body.limit, config=body.config)
        )
        FacadesObjectsFactory.get_intellect_query_facade().query(ctx)
        if ctx.resp.code == SUCCESS:
            return IntellectQueryOut(
                hits=[IntellectHitOut(id=h.id, text=h.text, score=h.score) for h in ctx.resp.hits],
                config=ctx.resp.config or body.config,
            )
        if ctx.resp.code == INVALID_INPUT:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, ctx.resp.error or "invalid request")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
