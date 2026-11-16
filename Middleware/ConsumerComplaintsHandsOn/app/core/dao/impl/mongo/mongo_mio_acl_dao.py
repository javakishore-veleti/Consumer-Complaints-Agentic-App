"""MioAclDao on MongoDB (D89)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import MioAudience
from app.core.common.dtos.mio_acl_dtos import MioAclCtx, MioAclRecord
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)
from app.core.dao.mio_acl_dao import MioAclDao

log = logging.getLogger(__name__)
COLL = "mios_acl"
MIOS = "mios"


def _to_record(doc: MongoDocument) -> MioAclRecord:
    created = doc["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return MioAclRecord(
        id=doc["id"], mio_id=doc["mio_id"], audience=doc["audience"], created_at=created
    )


class MongoMioAclDao(MioAclDao):
    def create(self, ctx: MioAclCtx) -> int:
        req = ctx.req
        if not (req.mio_id and req.audience):
            return INVALID_INPUT
        if req.audience not in MioAudience.values():
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=MIOS, query={"id": req.mio_id})) is None:
                    return NOT_FOUND
                if uow.find_one(
                    MongoFindReq(collection=COLL, query={"mio_id": req.mio_id, "audience": req.audience})
                ) is not None:
                    return CONFLICT
                doc = {
                    "id": str(uuid4()),
                    "mio_id": req.mio_id,
                    "audience": req.audience,
                    "created_at": datetime.now(timezone.utc),
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo mios_acl create failed")
            return FAILURE

    def list(self, ctx: MioAclCtx) -> int:
        req = ctx.req
        query: dict = {}
        if req.mio_id is not None:
            query["mio_id"] = req.mio_id
        if req.audience is not None:
            query["audience"] = req.audience
        try:
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(
                    MongoFindReq(collection=COLL, query=query, sort=[("created_at", 1), ("id", 1)])
                )
                ctx.resp.records = [_to_record(MongoDocument(d)) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo mios_acl list failed")
            return FAILURE

    def delete(self, ctx: MioAclCtx) -> int:
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
            log.exception("mongo mios_acl delete failed")
            return FAILURE
