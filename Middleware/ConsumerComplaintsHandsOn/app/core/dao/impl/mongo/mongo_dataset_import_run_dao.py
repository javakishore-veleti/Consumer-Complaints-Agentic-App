"""DatasetImportRunDao on MongoDB (M11)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.core.common.dtos.dataset_import_run_dtos import (
    ELIGIBLE_FOR_INGEST,
    STATUS_FAILED,
    STATUS_INGESTED,
    STATUS_INGESTING,
    STATUS_LANDED,
    STATUS_STAGING,
    DatasetImportRunCtx,
    DatasetImportRunRecord,
)
from app.core.common.return_codes import (
    CONFLICT,
    FAILURE,
    INVALID_INPUT,
    NOT_FOUND,
    SUCCESS,
)
from app.core.dao.dataset_import_run_dao import DatasetImportRunDao
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoFindReq,
    MongoUpdateReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)

log = logging.getLogger(__name__)
COLL = "dataset_import_runs"
_ALLOWED = frozenset({STATUS_STAGING, STATUS_LANDED, STATUS_INGESTING, STATUS_INGESTED, STATUS_FAILED})
_TRANSITIONS = {
    STATUS_STAGING: frozenset({STATUS_LANDED, STATUS_FAILED}),
    STATUS_LANDED: frozenset({STATUS_INGESTING, STATUS_FAILED}),
    STATUS_INGESTING: frozenset({STATUS_INGESTED, STATUS_FAILED, STATUS_INGESTING}),
    STATUS_FAILED: frozenset({STATUS_INGESTING, STATUS_LANDED, STATUS_FAILED}),
    STATUS_INGESTED: frozenset({STATUS_INGESTED}),
}


def _now() -> datetime:
    return datetime.now(UTC)


def _to_record(doc: MongoDocument) -> DatasetImportRunRecord:
    times = {
        "source_snapshot_start": doc["source_snapshot_start"],
        "source_snapshot_end": doc["source_snapshot_end"],
        "workflow_started_at": doc["workflow_started_at"],
        "workflow_completed_at": doc.get("workflow_completed_at"),
        "ingested_at": doc.get("ingested_at"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }
    for name, value in list(times.items()):
        times[name] = (
            value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value
        )
    return DatasetImportRunRecord(
        id=doc["id"],
        run_folder_name=doc["run_folder_name"],
        location_kind=doc["location_kind"],
        location_ref=doc["location_ref"],
        source_snapshot_start=times["source_snapshot_start"],
        source_snapshot_end=times["source_snapshot_end"],
        status=doc["status"],
        workflow_started_at=times["workflow_started_at"],
        workflow_completed_at=times["workflow_completed_at"],
        ingested_at=times["ingested_at"],
        mio_id=doc.get("mio_id"),
        execution_id=doc.get("execution_id"),
        part_count=doc.get("part_count"),
        message=doc.get("message"),
        created_at=times["created_at"],
        updated_at=times["updated_at"],
    )


class MongoDatasetImportRunDao(DatasetImportRunDao):
    def create(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if not (
            req.run_folder_name
            and req.location_kind
            and req.location_ref
            and req.source_snapshot_start
            and req.source_snapshot_end
            and req.workflow_started_at
        ):
            return INVALID_INPUT
        status = req.status or STATUS_STAGING
        if status not in _ALLOWED:
            return INVALID_INPUT
        now = _now()
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(
                    MongoFindReq(collection=COLL, query={"run_folder_name": req.run_folder_name.strip()})
                ) is not None:
                    return CONFLICT
                doc = {
                    "id": (req.id.strip() if req.id and req.id.strip() else str(uuid4())),
                    "run_folder_name": req.run_folder_name.strip(),
                    "location_kind": req.location_kind.strip(),
                    "location_ref": req.location_ref.strip(),
                    "source_snapshot_start": req.source_snapshot_start,
                    "source_snapshot_end": req.source_snapshot_end,
                    "status": status,
                    "workflow_started_at": req.workflow_started_at,
                    "workflow_completed_at": req.workflow_completed_at,
                    "ingested_at": req.ingested_at,
                    "mio_id": req.mio_id,
                    "execution_id": req.execution_id,
                    "part_count": req.part_count,
                    "message": req.message,
                    "created_at": now,
                    "updated_at": now,
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo dataset_import_run create failed")
            return FAILURE

    def get(self, ctx: DatasetImportRunCtx) -> int:
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
            log.exception("mongo dataset_import_run get failed")
            return FAILURE

    def list(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if req.limit is not None and (isinstance(req.limit, bool) or req.limit < 0):
            return INVALID_INPUT
        if req.offset is not None and (isinstance(req.offset, bool) or req.offset < 0):
            return INVALID_INPUT
        if req.status is not None and req.status not in _ALLOWED:
            return INVALID_INPUT
        try:
            query: dict = {}
            if req.ids:
                query["id"] = {"$in": list(req.ids)}
            if req.status:
                query["status"] = req.status
            if req.eligible_only:
                query["status"] = {"$in": sorted(ELIGIBLE_FOR_INGEST)}
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(
                    MongoFindReq(
                        collection=COLL,
                        query=query,
                        sort=[("workflow_started_at", -1), ("id", -1)],
                        skip=req.offset or 0,
                        limit=req.limit,
                    )
                )
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo dataset_import_run list failed")
            return FAILURE

    def update(self, ctx: DatasetImportRunCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        if req.status is not None and req.status not in _ALLOWED:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                current = doc["status"]
                if req.status is not None and req.status != current:
                    allowed = _TRANSITIONS.get(current, frozenset())
                    if req.status not in allowed:
                        return CONFLICT
                    changes: dict = {"status": req.status, "updated_at": _now()}
                    if req.workflow_completed_at is not None:
                        changes["workflow_completed_at"] = req.workflow_completed_at
                    if req.ingested_at is not None:
                        changes["ingested_at"] = req.ingested_at
                    if req.part_count is not None:
                        changes["part_count"] = req.part_count
                    if req.message is not None:
                        changes["message"] = req.message
                    if req.status == STATUS_INGESTED and "ingested_at" not in changes:
                        changes["ingested_at"] = _now()
                    moved = uow.update_matching(
                        MongoUpdateReq(
                            collection=COLL,
                            query={"id": req.id, "status": current},
                            changes=changes,
                        )
                    )
                    if not moved:
                        return CONFLICT
                else:
                    changed = False
                    for name in (
                        "workflow_completed_at",
                        "ingested_at",
                        "part_count",
                        "message",
                        "execution_id",
                    ):
                        val = getattr(req, name)
                        if val is not None:
                            doc[name] = val
                            changed = True
                    if changed:
                        doc["updated_at"] = _now()
                        uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                fresh = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                ctx.resp.records = [_to_record(MongoDocument(fresh))]
            return SUCCESS
        except Exception:
            log.exception("mongo dataset_import_run update failed")
            return FAILURE
