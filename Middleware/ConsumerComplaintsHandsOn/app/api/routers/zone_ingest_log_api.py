"""CRUD + claim for /ingestion-logs/{zone} (M55-0011 / #391). Open to Admin portal."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.models.zone_ingest_log_models import (
    ZoneIngestLogClaimIn,
    ZoneIngestLogCompleteIn,
    ZoneIngestLogCreateIn,
    ZoneIngestLogOut,
    ZoneIngestLogUpdateIn,
)
from app.core.common.dtos.zone_ingest_log_dtos import ZONE_INGEST_LOG_ZONES, ZoneIngestLogCtx, ZoneIngestLogReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.facades.objects_factory import FacadesObjectsFactory

ZoneName = Literal["raw", "refined", "curated", "taxonomy", "chroma"]


def _out(record) -> ZoneIngestLogOut:
    return ZoneIngestLogOut.model_validate(record, from_attributes=True)


def _raise(code: int) -> None:
    if code == SUCCESS:
        return
    if code == NOT_FOUND:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ingest log not found")
    if code == INVALID_INPUT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid input")
    if code == CONFLICT:
        raise HTTPException(status.HTTP_409_CONFLICT, "conflict")
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "request failed")


class ZoneIngestLogApi(metaclass=SingletonMeta):
    def __init__(self):
        self.router = APIRouter(prefix="/ingestion-logs", tags=["ingestion-logs"])
        self.router.add_api_route("/{zone}", self.list, methods=["GET"], response_model=list[ZoneIngestLogOut])
        self.router.add_api_route("/{zone}", self.create, methods=["POST"], response_model=ZoneIngestLogOut, status_code=201)
        self.router.add_api_route("/{zone}/claim", self.claim, methods=["POST"], response_model=list[ZoneIngestLogOut])
        self.router.add_api_route("/{zone}/{id}", self.get, methods=["GET"], response_model=ZoneIngestLogOut)
        self.router.add_api_route("/{zone}/{id}", self.update, methods=["PUT"], response_model=ZoneIngestLogOut)
        self.router.add_api_route("/{zone}/{id}", self.delete, methods=["DELETE"], status_code=204)
        self.router.add_api_route(
            "/{zone}/{id}/complete", self.complete, methods=["POST"], response_model=ZoneIngestLogOut
        )
        self.router.add_api_route(
            "/{zone}/{id}/reset", self.reset, methods=["POST"], response_model=ZoneIngestLogOut
        )

    def list(
        self,
        zone: Annotated[ZoneName, Path()],
        limit: Annotated[int | None, Query(ge=0, le=30)] = 30,
        offset: Annotated[int | None, Query(ge=0)] = 0,
        status_filter: Annotated[str | None, Query(alias="status")] = None,
        partition_key: Annotated[str | None, Query()] = None,
        workflow_execution_id: Annotated[str | None, Query()] = None,
        status_updated_from: Annotated[datetime | None, Query()] = None,
        status_updated_to: Annotated[datetime | None, Query()] = None,
    ) -> list[ZoneIngestLogOut]:
        if zone not in ZONE_INGEST_LOG_ZONES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid zone")
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=zone,
                limit=limit,
                offset=offset,
                status=status_filter,
                partition_key=partition_key,
                workflow_execution_id=workflow_execution_id,
                status_updated_from=status_updated_from,
                status_updated_to=status_updated_to,
            )
        )
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().list(ctx)
        _raise(code)
        return [_out(r) for r in ctx.resp.records]

    def create(self, zone: Annotated[ZoneName, Path()], body: ZoneIngestLogCreateIn) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=zone,
                partition_key=body.partition_key,
                data_tech=body.data_tech,
                source_end_point_id=body.source_end_point_id,
                dest_end_point_id=body.dest_end_point_id,
                workflow_execution_id=body.workflow_execution_id,
                configs_json=body.configs_json,
            )
        )
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().create(ctx)
        _raise(code)
        return _out(ctx.resp.records[0])

    def get(self, zone: Annotated[ZoneName, Path()], id: Annotated[str, Path()]) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=zone, id=id))
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().get(ctx)
        _raise(code)
        return _out(ctx.resp.records[0])

    def update(
        self, zone: Annotated[ZoneName, Path()], id: Annotated[str, Path()], body: ZoneIngestLogUpdateIn
    ) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(
                zone=zone,
                id=id,
                partition_key=body.partition_key,
                data_tech=body.data_tech,
                source_end_point_id=body.source_end_point_id,
                dest_end_point_id=body.dest_end_point_id,
                workflow_execution_id=body.workflow_execution_id,
                status=body.status,
                configs_json=body.configs_json,
            )
        )
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().update(ctx)
        _raise(code)
        return _out(ctx.resp.records[0])

    def delete(self, zone: Annotated[ZoneName, Path()], id: Annotated[str, Path()]) -> None:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=zone, id=id))
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().delete(ctx)
        _raise(code)

    def claim(self, zone: Annotated[ZoneName, Path()], body: ZoneIngestLogClaimIn) -> list[ZoneIngestLogOut]:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=zone, claim_limit=body.limit))
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().claim_pending(ctx)
        _raise(code)
        return [_out(r) for r in ctx.resp.records]

    def complete(
        self, zone: Annotated[ZoneName, Path()], id: Annotated[str, Path()], body: ZoneIngestLogCompleteIn
    ) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(
            req=ZoneIngestLogReq(zone=zone, id=id, status=body.status, configs_json=body.configs_json)
        )
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().complete(ctx)
        _raise(code)
        return _out(ctx.resp.records[0])

    def reset(self, zone: Annotated[ZoneName, Path()], id: Annotated[str, Path()]) -> ZoneIngestLogOut:
        ctx = ZoneIngestLogCtx(req=ZoneIngestLogReq(zone=zone, id=id))
        code = FacadesObjectsFactory.get_zone_ingest_log_facade().reset_failed(ctx)
        _raise(code)
        return _out(ctx.resp.records[0])
