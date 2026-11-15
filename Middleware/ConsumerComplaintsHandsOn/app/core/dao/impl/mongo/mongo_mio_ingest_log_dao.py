"""MioIngestLogDao on MongoDB (D79)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import ExecStatus
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogRecord, MioIngestLogReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoUpdateReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)
from app.core.dao.mio_ingest_log_dao import MioIngestLogDao

log = logging.getLogger(__name__)
COLL = "mios_ingest_log"
MIOS = "mios"
MARKER_MAX = 255
ROWS_LOADED_MAX = 9223372036854775807
BATCH_COUNT_MAX = 2147483647
NOTE_FIELDS = ("message", "rows_loaded", "batch_count", "increment_marker")


def _now() -> datetime:
    return datetime.now(timezone.utc)




def _to_record(doc: MongoDocument) -> MioIngestLogRecord:
    return MioIngestLogRecord(
        id=doc["id"],
        mio_id=doc["mio_id"],
        status=doc["status"],
        message=doc.get("message"),
        rows_loaded=doc.get("rows_loaded"),
        batch_count=doc.get("batch_count"),
        increment_marker=doc.get("increment_marker"),
        requested_at=(doc["requested_at"].replace(tzinfo=timezone.utc) if doc["requested_at"].tzinfo is None else doc["requested_at"]),
        started_at=(None if doc.get("started_at") is None else (doc["started_at"].replace(tzinfo=timezone.utc) if doc["started_at"].tzinfo is None else doc["started_at"])),
        finished_at=(None if doc.get("finished_at") is None else (doc["finished_at"].replace(tzinfo=timezone.utc) if doc["finished_at"].tzinfo is None else doc["finished_at"])),
    )


def _has_invalid_volume(req: MioIngestLogReq) -> bool:
    if req.message is not None and not isinstance(req.message, str):
        return True
    for count, largest in ((req.rows_loaded, ROWS_LOADED_MAX), (req.batch_count, BATCH_COUNT_MAX)):
        if count is not None and (isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= largest):
            return True
    marker = req.increment_marker
    return marker is not None and (not isinstance(marker, str) or len(marker) > MARKER_MAX)


def _has_invalid_paging(req: MioIngestLogReq) -> bool:
    for number in (req.limit, req.offset):
        if number is not None and (isinstance(number, bool) or not isinstance(number, int) or number < 0):
            return True
    return False


def _notes_of(req: MioIngestLogReq) -> dict:
    return {name: getattr(req, name) for name in NOTE_FIELDS if getattr(req, name) is not None}


class MongoMioIngestLogDao(MioIngestLogDao):
    def create(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.mio_id or _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=MIOS, query={"id": req.mio_id})) is None:
                    return NOT_FOUND
                doc = {
                    "id": str(uuid4()),
                    "mio_id": req.mio_id,
                    "status": ExecStatus.REQUESTED.value,
                    "message": None,
                    "requested_at": _now(),
                    "started_at": None,
                    "finished_at": None,
                    "rows_loaded": None,
                    "batch_count": None,
                    "increment_marker": None,
                    **_notes_of(req),
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_ingest_log create failed")
            return FAILURE

    def get(self, ctx: MioIngestLogCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": ctx.req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_ingest_log get failed")
            return FAILURE

    def list(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if _has_invalid_paging(req):
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        try:
            query: dict = {}
            if req.mio_id:
                query["mio_id"] = req.mio_id
            if req.status:
                query["status"] = req.status
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query, sort=[("requested_at", -1), ("id", 1)], skip=req.offset or 0, limit=req.limit,
                ))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_ingest_log list failed")
            return FAILURE

    def update(self, ctx: MioIngestLogCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in ExecStatus.values():
            return INVALID_INPUT
        if _has_invalid_volume(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                current = ExecStatus(doc["status"])
                target = current if req.status is None else ExecStatus(req.status)
                changes_status = target != current
                if changes_status and target not in current.next_statuses:
                    return CONFLICT
                notes = _notes_of(req)
                if changes_status:
                    changes = {**notes, "status": target.value}
                    if target == ExecStatus.STARTED:
                        changes["started_at"] = _now()
                    elif target.is_final:
                        changes["finished_at"] = _now()
                    moved = uow.update_matching(MongoUpdateReq(collection=COLL, query={"id": req.id, "status": current.value}, changes=changes))
                    doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                    if not moved:
                        if doc is None:
                            return NOT_FOUND
                        if doc["status"] != target.value:
                            return CONFLICT
                        for name, value in notes.items():
                            doc[name] = value
                        uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                else:
                    for name, value in notes.items():
                        doc[name] = value
                    uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id})))]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_ingest_log update failed")
            return FAILURE
