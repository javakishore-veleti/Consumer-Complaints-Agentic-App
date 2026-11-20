"""ZoneIngestLogDao on SQLAlchemy (SQLite + Postgres)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.common.dtos.zone_ingest_log_dtos import (
    CLAIM_LIMIT_MAX,
    LIST_LIMIT_MAX,
    ZONE_INGEST_LOG_DATA_TECHS,
    ZONE_INGEST_LOG_STATUSES,
    ZONE_INGEST_LOG_ZONES,
    ZoneIngestLogCtx,
    ZoneIngestLogRecord,
    ZoneIngestLogReq,
)
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.models import ZONE_INGEST_LOG_MODELS
from app.core.dao.impl.unit_of_work import unit_of_work
from app.core.dao.zone_ingest_log_dao import ZoneIngestLogDao

log = logging.getLogger(__name__)


@dataclass
class _MappedRow:
    zone: str
    row: Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_record(mapped: _MappedRow) -> ZoneIngestLogRecord:
    row = mapped.row
    status_on = row.status_on
    status_updated_on = row.status_updated_on
    if status_on is not None and status_on.tzinfo is None:
        status_on = status_on.replace(tzinfo=timezone.utc)
    if status_updated_on is not None and status_updated_on.tzinfo is None:
        status_updated_on = status_updated_on.replace(tzinfo=timezone.utc)
    return ZoneIngestLogRecord(
        id=row.id,
        zone=mapped.zone,
        partition_key=row.partition_key,
        data_tech=row.data_tech,
        source_end_point_id=row.source_end_point_id,
        dest_end_point_id=row.dest_end_point_id,
        workflow_execution_id=row.workflow_execution_id,
        status=row.status,
        status_on=status_on,
        status_updated_on=status_updated_on,
        configs_json=row.configs_json,
    )


def _model(req: ZoneIngestLogReq):
    if not req.zone or req.zone not in ZONE_INGEST_LOG_ZONES:
        return None
    return ZONE_INGEST_LOG_MODELS[req.zone]


class SqlAlchemyZoneIngestLogDao(ZoneIngestLogDao):
    def create(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None:
            return INVALID_INPUT
        if not req.partition_key or not req.source_end_point_id or not req.dest_end_point_id:
            return INVALID_INPUT
        if req.data_tech not in ZONE_INGEST_LOG_DATA_TECHS:
            return INVALID_INPUT
        now = _now()
        try:
            with unit_of_work(ctx) as session:
                row = model(
                    id=str(uuid4()),
                    partition_key=req.partition_key,
                    data_tech=req.data_tech,
                    source_end_point_id=req.source_end_point_id,
                    dest_end_point_id=req.dest_end_point_id,
                    workflow_execution_id=req.workflow_execution_id,
                    status="pending",
                    status_on=now,
                    status_updated_on=now,
                    configs_json=req.configs_json,
                )
                session.add(row)
                session.flush()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row))]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("zone ingest_log create failed")
            return FAILURE

    def get(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None or not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(model, req.id)
                if row is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row))]
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log get failed")
            return FAILURE

    def list(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None:
            return INVALID_INPUT
        if req.limit is not None and (isinstance(req.limit, bool) or not isinstance(req.limit, int) or req.limit < 0):
            return INVALID_INPUT
        if req.offset is not None and (
            isinstance(req.offset, bool) or not isinstance(req.offset, int) or req.offset < 0
        ):
            return INVALID_INPUT
        if req.status is not None and req.status not in ZONE_INGEST_LOG_STATUSES:
            return INVALID_INPUT
        limit = LIST_LIMIT_MAX if req.limit is None else min(req.limit, LIST_LIMIT_MAX)
        if limit == 0:
            ctx.resp.records = []
            return SUCCESS
        offset = req.offset or 0
        try:
            with unit_of_work(ctx) as session:
                stmt = select(model)
                if req.status is not None:
                    stmt = stmt.where(model.status == req.status)
                if req.partition_key is not None:
                    stmt = stmt.where(model.partition_key == req.partition_key)
                if req.workflow_execution_id is not None:
                    stmt = stmt.where(model.workflow_execution_id == req.workflow_execution_id)
                if req.status_updated_from is not None:
                    stmt = stmt.where(model.status_updated_on >= req.status_updated_from)
                if req.status_updated_to is not None:
                    stmt = stmt.where(model.status_updated_on <= req.status_updated_to)
                stmt = stmt.order_by(model.status_updated_on.desc(), model.id.desc()).offset(offset).limit(limit)
                rows = session.scalars(stmt).all()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row)) for row in rows]
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log list failed")
            return FAILURE

    def update(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None or not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ZONE_INGEST_LOG_STATUSES:
            return INVALID_INPUT
        if req.data_tech is not None and req.data_tech not in ZONE_INGEST_LOG_DATA_TECHS:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(model, req.id)
                if row is None:
                    return NOT_FOUND
                now = _now()
                if req.partition_key is not None:
                    row.partition_key = req.partition_key
                if req.data_tech is not None:
                    row.data_tech = req.data_tech
                if req.source_end_point_id is not None:
                    row.source_end_point_id = req.source_end_point_id
                if req.dest_end_point_id is not None:
                    row.dest_end_point_id = req.dest_end_point_id
                if req.workflow_execution_id is not None:
                    row.workflow_execution_id = req.workflow_execution_id
                if req.configs_json is not None:
                    row.configs_json = req.configs_json
                if req.status is not None and req.status != row.status:
                    row.status = req.status
                    row.status_on = now
                row.status_updated_on = now
                session.flush()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row))]
            return SUCCESS
        except IntegrityError:
            return CONFLICT
        except Exception:
            log.exception("zone ingest_log update failed")
            return FAILURE

    def delete(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None or not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(model, req.id)
                if row is None:
                    return NOT_FOUND
                session.delete(row)
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log delete failed")
            return FAILURE

    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None:
            return INVALID_INPUT
        raw_limit = CLAIM_LIMIT_MAX if req.claim_limit is None else req.claim_limit
        if isinstance(raw_limit, bool) or not isinstance(raw_limit, int) or raw_limit < 1:
            return INVALID_INPUT
        limit = min(raw_limit, CLAIM_LIMIT_MAX)
        try:
            with unit_of_work(ctx) as session:
                stmt = (
                    select(model)
                    .where(model.status == "pending")
                    .order_by(model.status_updated_on.asc(), model.id.asc())
                    .limit(limit)
                )
                rows = list(session.scalars(stmt).all())
                now = _now()
                for row in rows:
                    row.status = "in_progress"
                    row.status_on = now
                    row.status_updated_on = now
                session.flush()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row)) for row in rows]
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log claim_pending failed")
            return FAILURE

    def complete(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None or not req.id:
            return INVALID_INPUT
        if req.status not in ("done", "failed"):
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(model, req.id)
                if row is None:
                    return NOT_FOUND
                now = _now()
                row.status = req.status
                row.status_on = now
                row.status_updated_on = now
                if req.configs_json is not None:
                    row.configs_json = req.configs_json
                session.flush()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row))]
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log complete failed")
            return FAILURE

    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        model = _model(req)
        if model is None or not req.id:
            return INVALID_INPUT
        try:
            with unit_of_work(ctx) as session:
                row = session.get(model, req.id)
                if row is None:
                    return NOT_FOUND
                if row.status != "failed":
                    return CONFLICT
                now = _now()
                row.status = "pending"
                row.status_on = now
                row.status_updated_on = now
                session.flush()
                ctx.resp.records = [_to_record(_MappedRow(zone=req.zone, row=row))]
            return SUCCESS
        except Exception:
            log.exception("zone ingest_log reset_failed failed")
            return FAILURE
