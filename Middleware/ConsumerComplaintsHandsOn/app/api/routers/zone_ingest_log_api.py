"""CRUD + claim for /ingestion-logs/{zone} (M55-0011 / #391). Open to Admin portal."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.zone_ingest_log_models import (
    ZoneIngestLogClaimHttpReq,
    ZoneIngestLogCompleteHttpReq,
    ZoneIngestLogCreateHttpReq,
    ZoneIngestLogIdHttpReq,
    ZoneIngestLogListHttpReq,
    ZoneIngestLogOut,
    ZoneIngestLogUpdateHttpReq,
)
from app.core.common.dtos.zone_ingest_log_dtos import (
    ZONE_INGEST_LOG_ZONES,
    ZoneIngestLogCtx,
    ZoneIngestLogRecord,
    ZoneIngestLogReq,
)
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory


class ZoneIngestLogApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/ingestion-logs", tags=["ingestion-logs"])
        self.router.add_api_route("/{zone}", self.list, methods=["GET"], response_model=list[ZoneIngestLogOut])
        self.router.add_api_route(
            "/{zone}", self.create, methods=["POST"], response_model=ZoneIngestLogOut, status_code=201
        )
        self.router.add_api_route(
            "/{zone}/claim", self.claim, methods=["POST"], response_model=list[ZoneIngestLogOut]
        )
        self.router.add_api_route("/{zone}/{id}", self.get, methods=["GET"], response_model=ZoneIngestLogOut)
        self.router.add_api_route("/{zone}/{id}", self.update, methods=["PUT"], response_model=ZoneIngestLogOut)
        self.router.add_api_route("/{zone}/{id}", self.delete, methods=["DELETE"], status_code=204)
        self.router.add_api_route(
            "/{zone}/{id}/complete", self.complete, methods=["POST"], response_model=ZoneIngestLogOut
        )
        self.router.add_api_route(
            "/{zone}/{id}/reset", self.reset, methods=["POST"], response_model=ZoneIngestLogOut
        )

    def list(self, req: Annotated[ZoneIngestLogListHttpReq, Depends()]) -> list[ZoneIngestLogOut]:
        if req.zone not in ZONE_INGEST_LOG_ZONES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid zone")
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=req.zone,
                limit=req.limit,
                offset=req.offset,
                status=req.status,
                partition_key=req.partition_key,
                workflow_execution_id=req.workflow_execution_id,
                status_updated_from=req.status_updated_from,
                status_updated_to=req.status_updated_to,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().list(ctx)
        self._check(ctx)
        return [self._out(r) for r in ctx.resp.records]

    def create(self, req: Annotated[ZoneIngestLogCreateHttpReq, Depends()]) -> ZoneIngestLogOut:
        body = req.body
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=req.zone,
                partition_key=body.partition_key,
                data_tech=body.data_tech,
                source_end_point_id=body.source_end_point_id,
                dest_end_point_id=body.dest_end_point_id,
                workflow_execution_id=body.workflow_execution_id,
                configs_json=body.configs_json,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().create(ctx)
        self._check(ctx)
        return self._out(ctx.resp.records[0])

    def get(self, req: Annotated[ZoneIngestLogIdHttpReq, Depends()]) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=req.zone, id=req.id))
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().get(ctx)
        self._check(ctx)
        return self._out(ctx.resp.records[0])

    def update(self, req: Annotated[ZoneIngestLogUpdateHttpReq, Depends()]) -> ZoneIngestLogOut:
        body = req.body
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=req.zone,
                id=req.id,
                partition_key=body.partition_key,
                data_tech=body.data_tech,
                source_end_point_id=body.source_end_point_id,
                dest_end_point_id=body.dest_end_point_id,
                workflow_execution_id=body.workflow_execution_id,
                status=body.status,
                configs_json=body.configs_json,
            )
        )
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().update(ctx)
        self._check(ctx)
        return self._out(ctx.resp.records[0])

    def delete(self, req: Annotated[ZoneIngestLogIdHttpReq, Depends()]) -> None:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=req.zone, id=req.id))
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().delete(ctx)
        self._check(ctx)

    def claim(self, req: Annotated[ZoneIngestLogClaimHttpReq, Depends()]) -> list[ZoneIngestLogOut]:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=req.zone, claim_limit=req.body.limit))
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().claim_pending(ctx)
        self._check(ctx)
        return [self._out(r) for r in ctx.resp.records]

    def complete(self, req: Annotated[ZoneIngestLogCompleteHttpReq, Depends()]) -> ZoneIngestLogOut:
        body = req.body
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(zone=req.zone, id=req.id, status=body.status, configs_json=body.configs_json)
        )
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().complete(ctx)
        self._check(ctx)
        return self._out(ctx.resp.records[0])

    def reset(self, req: Annotated[ZoneIngestLogIdHttpReq, Depends()]) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=req.zone, id=req.id))
        ctx.resp.code = FacadesObjectsFactory.get_zone_ingest_log_facade().reset_failed(ctx)
        self._check(ctx)
        return self._out(ctx.resp.records[0])

    @staticmethod
    def _out(record: ZoneIngestLogRecord) -> ZoneIngestLogOut:
        return ZoneIngestLogOut.model_validate(record, from_attributes=True)

    @staticmethod
    def _check(ctx: ZoneIngestLogCtx) -> None:
        code = ctx.resp.code
        if code == SUCCESS:
            return
        if code == NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "ingest log not found")
        if code == INVALID_INPUT:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid input")
        if code == CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "conflict")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")
