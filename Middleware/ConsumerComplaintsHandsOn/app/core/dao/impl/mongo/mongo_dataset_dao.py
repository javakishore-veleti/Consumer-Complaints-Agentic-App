"""DatasetDao on MongoDB (D79)."""

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetRecord, DatasetReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.dataset_dao import DatasetDao
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoUpdateReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)

log = logging.getLogger(__name__)
COLL = "datasets"
LOCS = "datasets_location"
LINKS = "mios_datasets"
NAME_MAX = 100
CODE_PATTERN = re.compile(r"[A-Z0-9]{1,15}")




def _to_record(doc: MongoDocument) -> DatasetRecord:
    return DatasetRecord(
        id=doc["id"],
        name=doc["name"],
        code=doc["code"],
        description=doc.get("description"),
        created_at=(doc["created_at"].replace(tzinfo=timezone.utc) if doc["created_at"].tzinfo is None else doc["created_at"]),
        updated_at=(doc["updated_at"].replace(tzinfo=timezone.utc) if doc["updated_at"].tzinfo is None else doc["updated_at"]),
    )


def _name_of(req: DatasetReq) -> str | None:
    return None if req.name is None else req.name.strip()


def _name_is_not_text(req: DatasetReq) -> bool:
    return req.name is not None and not isinstance(req.name, str)


def _has_invalid_field(req: DatasetReq) -> bool:
    if _name_is_not_text(req):
        return True
    name = _name_of(req)
    if name is not None and (not name or len(name) > NAME_MAX):
        return True
    if req.code is not None and (not isinstance(req.code, str) or CODE_PATTERN.fullmatch(req.code) is None):
        return True
    return False


class MongoDatasetDao(DatasetDao):
    def create(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if _has_invalid_field(req) or not (_name_of(req) and req.code):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=COLL, query={"name": _name_of(req)})) is not None or uow.find_one(
                    COLL, {"code": req.code}
                ):
                    return CONFLICT
                now = datetime.now(timezone.utc)
                doc = {
                    "id": str(uuid4()),
                    "name": _name_of(req),
                    "code": req.code,
                    "description": req.description,
                    "created_at": now,
                    "updated_at": now,
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo datasets create failed")
            return FAILURE

    def get(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if _name_is_not_text(req) or not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = (
                    uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                    if req.id
                    else uow.find_one(MongoFindReq(collection=COLL, query={"name": _name_of(req)}))
                )
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo datasets get failed")
            return FAILURE

    def list(self, ctx: DatasetCtx) -> int:
        try:
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query={}, sort=[("name", 1)]))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo datasets list failed")
            return FAILURE

    def update(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                new_name = _name_of(req) if _name_of(req) != doc["name"] else None
                new_code = req.code if req.code != doc["code"] else None
                if new_name is not None:
                    rival = uow.find_one(MongoFindReq(collection=COLL, query={"name": new_name}))
                    if rival is not None and rival["id"] != doc["id"]:
                        return CONFLICT
                if new_code is not None:
                    rival = uow.find_one(MongoFindReq(collection=COLL, query={"code": new_code}))
                    if rival is not None and rival["id"] != doc["id"]:
                        return CONFLICT
                    if uow.find_one(LOCS, {"dataset_id": doc["id"], "local_env_var_name": {"$ne": None}}):
                        return CONFLICT
                if new_name is not None:
                    doc["name"] = new_name
                if new_code is not None:
                    doc["code"] = new_code
                if req.description is not None:
                    doc["description"] = req.description
                doc["updated_at"] = datetime.now(timezone.utc)
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo datasets update failed")
            return FAILURE

    def delete(self, ctx: DatasetCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                if uow.find_one(MongoFindReq(collection=LOCS, query={"dataset_id": doc["id"]})) or uow.find_one(MongoFindReq(collection=LINKS, query={"dataset_id": doc["id"]})):
                    return CONFLICT
                ctx.resp.records = [_to_record(MongoDocument(doc))]
                uow.delete(MongoDeleteReq(collection=COLL, doc_id=req.id))
            return SUCCESS
        except Exception:
            log.exception("mongo datasets delete failed")
            return FAILURE
