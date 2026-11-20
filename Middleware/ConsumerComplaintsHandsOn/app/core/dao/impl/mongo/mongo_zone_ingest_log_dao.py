"""ZoneIngestLogDao on MongoDB."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

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
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)
from app.core.dao.zone_ingest_log_dao import ZoneIngestLogDao

log = logging.getLogger(__name__)


@dataclass
class _DocWithZone:
    zone: str
    doc: Any


def _now() -> datetime:
    return datetime.now(UTC)


def _coll(req: ZoneIngestLogReq) -> str | None:
    if not req.zone or req.zone not in ZONE_INGEST_LOG_ZONES:
        return None
    return f"ingest_log_{req.zone}"


def _to_record(mapped: _DocWithZone) -> ZoneIngestLogRecord:
    doc = mapped.doc
    status_on = doc["status_on"]
    status_updated_on = doc["status_updated_on"]
    if status_on is not None and getattr(status_on, "tzinfo", None) is None:
        status_on = status_on.replace(tzinfo=UTC)
    if status_updated_on is not None and getattr(status_updated_on, "tzinfo", None) is None:
        status_updated_on = status_updated_on.replace(tzinfo=UTC)
    return ZoneIngestLogRecord(
        id=doc["id"],
        zone=mapped.zone,
        partition_key=doc["partition_key"],
        data_tech=doc["data_tech"],
        source_end_point_id=doc["source_end_point_id"],
        dest_end_point_id=doc["dest_end_point_id"],
        workflow_execution_id=doc.get("workflow_execution_id"),
        status=doc["status"],
        status_on=status_on,
        status_updated_on=status_updated_on,
        configs_json=doc.get("configs_json"),
    )


class MongoZoneIngestLogDao(ZoneIngestLogDao):
    def create(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None:
            return INVALID_INPUT
        if not req.partition_key or not req.source_end_point_id or not req.dest_end_point_id:
            return INVALID_INPUT
        if req.data_tech not in ZONE_INGEST_LOG_DATA_TECHS:
            return INVALID_INPUT
        now = _now()
        doc = {
            "id": str(uuid4()),
            "partition_key": req.partition_key,
            "data_tech": req.data_tech,
            "source_end_point_id": req.source_end_point_id,
            "dest_end_point_id": req.dest_end_point_id,
            "workflow_execution_id": req.workflow_execution_id,
            "status": "pending",
            "status_on": now,
            "status_updated_on": now,
            "configs_json": req.configs_json,
        }
        try:
            with mongo_unit_of_work(ctx) as uow:
                uow.insert(MongoWriteReq(collection=coll, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo zone ingest_log create failed")
            return FAILURE

    def get(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None or not req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=coll, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log get failed")
            return FAILURE

    def list(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None:
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
        query: dict = {}
        if req.status is not None:
            query["status"] = req.status
        if req.partition_key is not None:
            query["partition_key"] = req.partition_key
        if req.workflow_execution_id is not None:
            query["workflow_execution_id"] = req.workflow_execution_id
        if req.status_updated_from is not None or req.status_updated_to is not None:
            rng: dict = {}
            if req.status_updated_from is not None:
                rng["$gte"] = req.status_updated_from
            if req.status_updated_to is not None:
                rng["$lte"] = req.status_updated_to
            query["status_updated_on"] = rng
        try:
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(
                    MongoFindReq(
                        collection=coll,
                        query=query,
                        sort=[("status_updated_on", -1), ("id", -1)],
                        skip=req.offset or 0,
                        limit=limit,
                    )
                )
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=d)) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log list failed")
            return FAILURE

    def update(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None or not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ZONE_INGEST_LOG_STATUSES:
            return INVALID_INPUT
        if req.data_tech is not None and req.data_tech not in ZONE_INGEST_LOG_DATA_TECHS:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=coll, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                payload = dict(doc)
                now = _now()
                for field in (
                    "partition_key",
                    "data_tech",
                    "source_end_point_id",
                    "dest_end_point_id",
                    "workflow_execution_id",
                    "configs_json",
                ):
                    value = getattr(req, field)
                    if value is not None:
                        payload[field] = value
                if req.status is not None and req.status != payload["status"]:
                    payload["status"] = req.status
                    payload["status_on"] = now
                payload["status_updated_on"] = now
                uow.replace(MongoWriteReq(collection=coll, doc=MongoDocument(payload)))
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=payload))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo zone ingest_log update failed")
            return FAILURE

    def delete(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None or not req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                deleted = uow.delete(MongoDeleteReq(collection=coll, doc_id=req.id))
                if deleted is None:
                    return NOT_FOUND
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log delete failed")
            return FAILURE

    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None:
            return INVALID_INPUT
        raw_limit = CLAIM_LIMIT_MAX if req.claim_limit is None else req.claim_limit
        if isinstance(raw_limit, bool) or not isinstance(raw_limit, int) or raw_limit < 1:
            return INVALID_INPUT
        limit = min(raw_limit, CLAIM_LIMIT_MAX)
        try:
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(
                    MongoFindReq(
                        collection=coll,
                        query={"status": "pending"},
                        sort=[("status_updated_on", 1), ("id", 1)],
                        limit=limit,
                    )
                )
                now = _now()
                out = []
                for doc in docs:
                    payload = dict(doc)
                    payload["status"] = "in_progress"
                    payload["status_on"] = now
                    payload["status_updated_on"] = now
                    uow.replace(MongoWriteReq(collection=coll, doc=MongoDocument(payload)))
                    out.append(payload)
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=d)) for d in out]
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log claim_pending failed")
            return FAILURE

    def complete(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None or not req.id:
            return INVALID_INPUT
        if req.status not in ("done", "failed"):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=coll, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                payload = dict(doc)
                now = _now()
                payload["status"] = req.status
                payload["status_on"] = now
                payload["status_updated_on"] = now
                if req.configs_json is not None:
                    payload["configs_json"] = req.configs_json
                uow.replace(MongoWriteReq(collection=coll, doc=MongoDocument(payload)))
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=payload))]
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log complete failed")
            return FAILURE

    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int:
        req = ctx.req
        coll = _coll(req)
        if coll is None or not req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=coll, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                if doc["status"] != "failed":
                    return CONFLICT
                payload = dict(doc)
                now = _now()
                payload["status"] = "pending"
                payload["status_on"] = now
                payload["status_updated_on"] = now
                uow.replace(MongoWriteReq(collection=coll, doc=MongoDocument(payload)))
                ctx.resp.records = [_to_record(_DocWithZone(zone=req.zone, doc=payload))]
            return SUCCESS
        except Exception:
            log.exception("mongo zone ingest_log reset_failed failed")
            return FAILURE
