"""POST /intellect/query — local vector search (D90). POST /intellect/query-ast — Query AST (M52 / #352). GET/POST /intellect/risk-radar — Risk Radar (M53 / #359)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.models.intellect_query_models import IntellectHitOut, IntellectQueryBody, IntellectQueryOut
from app.api.models.query_ast_models import QueryAstBody, QueryAstOut
from app.api.models.risk_radar_models import (
    RiskRadarAlertOut,
    RiskRadarBody,
    RiskRadarOut,
    RiskRadarQuery,
)
from app.core.common.dtos.intellect_query_dtos import IntellectQueryReq
from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.common.dtos.query_ast_dtos import QueryAstReq
from app.core.common.dtos.query_ast_facade_dtos import QueryAstFacadeCtx
from app.core.common.dtos.risk_radar_dtos import RiskRadarReq
from app.core.common.dtos.risk_radar_facade_dtos import RiskRadarFacadeCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
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
        self.router.add_api_route(
            "/query-ast",
            self.query_ast,
            methods=["POST"],
            response_model=QueryAstOut,
        )
        self.router.add_api_route(
            "/risk-radar",
            self.risk_radar_get,
            methods=["GET"],
            response_model=RiskRadarOut,
        )
        self.router.add_api_route(
            "/risk-radar",
            self.risk_radar_post,
            methods=["POST"],
            response_model=RiskRadarOut,
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

    def query_ast(self, body: QueryAstBody) -> QueryAstOut:
        ctx = QueryAstFacadeCtx(req=QueryAstReq(ast=body.ast, execute=body.execute))
        FacadesObjectsFactory.get_query_ast_facade().run(ctx)
        if ctx.resp.code == SUCCESS:
            return QueryAstOut(
                sql=ctx.resp.sql,
                executed=ctx.resp.executed,
                count=ctx.resp.count,
                k_anon_ok=ctx.resp.k_anon_ok,
            )
        if ctx.resp.code == INVALID_INPUT:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, ctx.resp.error or "invalid request")
        if ctx.resp.code == FAILURE and "warehouse unavailable" in (ctx.resp.error or ""):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, ctx.resp.error)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, ctx.resp.error or "request failed")

    def risk_radar_get(self, req: Annotated[RiskRadarQuery, Query()]) -> RiskRadarOut:
        return self._risk_radar(RiskRadarReq(source=req.source or "fixture"))

    def risk_radar_post(self, body: RiskRadarBody) -> RiskRadarOut:
        return self._risk_radar(RiskRadarReq(source=body.source or "fixture"))

    def _risk_radar(self, req: RiskRadarReq) -> RiskRadarOut:
        ctx = RiskRadarFacadeCtx(req=req)
        FacadesObjectsFactory.get_risk_radar_facade().run(ctx)
        if ctx.resp.code == SUCCESS:
            return RiskRadarOut(
                alerts=[
                    RiskRadarAlertOut(
                        id=a.id,
                        title=a.title,
                        severity=a.severity,
                        parent_org_id=a.parent_org_id,
                        primary_money_topic=a.primary_money_topic,
                        window_days=a.window_days,
                        current_count=a.current_count,
                        baseline_mean=a.baseline_mean,
                        z_score=a.z_score,
                        k_anon_ok=a.k_anon_ok,
                        drilldown_ast=a.drilldown_ast,
                    )
                    for a in ctx.resp.alerts
                ],
                source=ctx.resp.source,
            )
        if ctx.resp.code == INVALID_INPUT:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, ctx.resp.error or "invalid request")
        if ctx.resp.code == FAILURE and "warehouse unavailable" in (ctx.resp.error or ""):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, ctx.resp.error)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, ctx.resp.error or "request failed")
