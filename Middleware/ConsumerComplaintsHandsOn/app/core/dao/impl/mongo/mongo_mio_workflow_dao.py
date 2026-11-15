"""MioWorkflowDao on MongoDB (D79 / D84)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowRecord
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)
from app.core.dao.mio_workflow_dao import MioWorkflowDao

log = logging.getLogger(__name__)
COLL = "mios_workflows"
MIOS = "mios"
WORKFLOWS = "app_workflows"


def _to_record(doc: MongoDocument) -> MioWorkflowRecord:
    created = doc["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioWorkflowRecord(
        id=doc["id"],
        mio_id=doc["mio_id"],
        workflow_id=doc["workflow_id"],
        created_at=created,
    )


class MongoMioWorkflowDao(MioWorkflowDao):
    def create(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.workflow_id):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=MIOS, query={"id": req.mio_id})) is None:
                    return NOT_FOUND
                if uow.find_one(MongoFindReq(collection=WORKFLOWS, query={"id": req.workflow_id})) is None:
                    return NOT_FOUND
                if uow.find_one(
                    MongoFindReq(collection=COLL, query={"mio_id": req.mio_id, "workflow_id": req.workflow_id})
                ) is not None:
                    return CONFLICT
                doc = {
                    "id": str(uuid4()),
                    "mio_id": req.mio_id,
                    "workflow_id": req.workflow_id,
                    "created_at": datetime.now(timezone.utc),
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo mios_workflows create failed")
            return FAILURE

    def get(self, ctx: MioWorkflowCtx) -> int:
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
            log.exception("mongo mios_workflows get failed")
            return FAILURE

    def list(self, ctx: MioWorkflowCtx) -> int:
        req = ctx.req
        try:
            query: dict = {}
            if req.mio_id is not None:
                query["mio_id"] = req.mio_id
            if req.workflow_id is not None:
                query["workflow_id"] = req.workflow_id
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query, sort=[("created_at", 1), ("id", 1)]))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_workflows list failed")
            return FAILURE

    def delete(self, ctx: MioWorkflowCtx) -> int:
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
            log.exception("mongo mios_workflows delete failed")
            return FAILURE
