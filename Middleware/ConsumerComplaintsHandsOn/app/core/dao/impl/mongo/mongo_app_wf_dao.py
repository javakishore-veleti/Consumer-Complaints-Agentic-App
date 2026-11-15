"""AppWfDao on MongoDB (D79)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import EngineType
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfRecord, AppWfReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_wf_dao import AppWfDao
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
COLL = "app_workflows"
NAME_MAX = 100
ENGINE_WORKFLOW_ID_MAX = 255




def _to_record(doc: MongoDocument) -> AppWfRecord:
    return AppWfRecord(
        id=doc["id"],
        workflow_name=doc["workflow_name"],
        engine_type=doc["engine_type"],
        engine_workflow_id=doc["engine_workflow_id"],
        config=doc.get("config"),
        enabled=doc["enabled"],
        created_at=(doc["created_at"].replace(tzinfo=timezone.utc) if doc["created_at"].tzinfo is None else doc["created_at"]),
        updated_at=(doc["updated_at"].replace(tzinfo=timezone.utc) if doc["updated_at"].tzinfo is None else doc["updated_at"]),
    )


def _name_of(req: AppWfReq) -> str | None:
    return None if req.workflow_name is None else req.workflow_name.strip()


def _has_invalid_field(req: AppWfReq) -> bool:
    name = _name_of(req)
    if name is not None and (not name or len(name) > NAME_MAX):
        return True
    if req.engine_type is not None and req.engine_type not in EngineType.values():
        return True
    if req.engine_workflow_id is not None and (
        not req.engine_workflow_id.strip() or len(req.engine_workflow_id) > ENGINE_WORKFLOW_ID_MAX
    ):
        return True
    if req.config is not None and not isinstance(req.config, dict):
        return True
    return False


class MongoAppWfDao(AppWfDao):
    def create(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (_name_of(req) and req.engine_type and req.engine_workflow_id) or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                if uow.find_one(MongoFindReq(collection=COLL, query={"workflow_name": _name_of(req)})) is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                doc = {
                    "id": str(uuid4()),
                    "workflow_name": _name_of(req),
                    "engine_type": req.engine_type,
                    "engine_workflow_id": req.engine_workflow_id,
                    "config": req.config,
                    "enabled": True if req.enabled is None else req.enabled,
                    "created_at": now,
                    "updated_at": now,
                }
                uow.insert(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo app_workflows create failed")
            return FAILURE

    def get(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not (req.id or _name_of(req)):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = (
                    uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                    if req.id
                    else uow.find_one(MongoFindReq(collection=COLL, query={"workflow_name": _name_of(req)}))
                )
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows get failed")
            return FAILURE

    def list(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        try:
            query: dict = {}
            if req.engine_type is not None:
                query["engine_type"] = req.engine_type
            if req.enabled is not None:
                query["enabled"] = req.enabled
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query, sort=[("workflow_name", 1)]))
                ctx.resp.records = [_to_record(d) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows list failed")
            return FAILURE

    def update(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                if _name_of(req) is not None and _name_of(req) != doc["workflow_name"]:
                    if uow.find_one(MongoFindReq(collection=COLL, query={"workflow_name": _name_of(req)})) is not None:
                        return CONFLICT
                    doc["workflow_name"] = _name_of(req)
                if req.engine_type is not None:
                    doc["engine_type"] = req.engine_type
                if req.engine_workflow_id is not None:
                    doc["engine_workflow_id"] = req.engine_workflow_id
                if req.config is not None:
                    doc["config"] = req.config
                if req.enabled is not None:
                    doc["enabled"] = req.enabled
                doc["updated_at"] = datetime.now(timezone.utc)
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo app_workflows update failed")
            return FAILURE

    def delete(self, ctx: AppWfCtx) -> int:
        req = ctx.req
        if not req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
                uow.delete(MongoDeleteReq(collection=COLL, doc_id=req.id))
            return SUCCESS
        except Exception:
            log.exception("mongo app_workflows delete failed")
            return FAILURE
