"""MioDatasetDao on MongoDB (D79)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetRecord, MioDatasetReq
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
from app.core.dao.mio_dataset_dao import MioDatasetDao

log = logging.getLogger(__name__)
COLL = "mios_datasets"
MIOS = "mios"
DATASETS = "datasets"
LOCS = "datasets_location"




def _to_record(doc: MongoDocument) -> MioDatasetRecord:
    return MioDatasetRecord(
        id=doc["id"],
        mio_id=doc["mio_id"],
        dataset_id=doc["dataset_id"],
        dataset_location_id=doc["dataset_location_id"],
        created_at=(doc["created_at"].replace(tzinfo=timezone.utc) if doc["created_at"].tzinfo is None else doc["created_at"]),
    )


class MongoMioDatasetDao(MioDatasetDao):
    def create(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.dataset_id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=MIOS, query={"id": req.mio_id})) is None or uow.find_one(MongoFindReq(collection=DATASETS, query={"id": req.dataset_id})) is None:
                    return NOT_FOUND
                location = uow.find_one(MongoFindReq(collection=LOCS, query={"id": req.dataset_location_id}))
                if location is None:
                    return NOT_FOUND
                if location["dataset_id"] != req.dataset_id:
                    return INVALID_INPUT
                if uow.find_one(MongoFindReq(collection=COLL, query={"mio_id": req.mio_id, "dataset_id": req.dataset_id})) is not None:
                    return CONFLICT
                doc = {
                    "id": str(uuid4()),
                    "mio_id": req.mio_id,
                    "dataset_id": req.dataset_id,
                    "dataset_location_id": req.dataset_location_id,
                    "created_at": datetime.now(timezone.utc),
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo mios_datasets create failed")
            return FAILURE

    def get(self, ctx: MioDatasetCtx) -> int:
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
            log.exception("mongo mios_datasets get failed")
            return FAILURE

    def list(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        try:
            query: dict = {}
            if req.mio_id is not None:
                query["mio_id"] = req.mio_id
            if req.dataset_id is not None:
                query["dataset_id"] = req.dataset_id
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query, sort=[("created_at", 1), ("id", 1)]))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_datasets list failed")
            return FAILURE

    def update(self, ctx: MioDatasetCtx) -> int:
        req = ctx.req
        if not (req.id and req.dataset_location_id):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                if (req.mio_id is not None and req.mio_id != doc["mio_id"]) or (
                    req.dataset_id is not None and req.dataset_id != doc["dataset_id"]
                ):
                    return INVALID_INPUT
                location = uow.find_one(MongoFindReq(collection=LOCS, query={"id": req.dataset_location_id}))
                if location is None:
                    return NOT_FOUND
                if location["dataset_id"] != doc["dataset_id"]:
                    return INVALID_INPUT
                doc["dataset_location_id"] = req.dataset_location_id
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_datasets update failed")
            return FAILURE

    def delete(self, ctx: MioDatasetCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": ctx.req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
                uow.delete(MongoDeleteReq(collection=COLL, doc_id=ctx.req.id))
            return SUCCESS
        except Exception:
            log.exception("mongo mios_datasets delete failed")
            return FAILURE
