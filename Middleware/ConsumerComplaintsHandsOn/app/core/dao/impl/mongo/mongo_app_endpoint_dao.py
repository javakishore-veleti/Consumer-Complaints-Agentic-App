"""AppEndpointDao on MongoDB (D79 / D85)."""

import logging
from dataclasses import dataclass
import re
from datetime import datetime, timezone
from uuid import uuid4

from app.core.common.app_types_constants import AppEndpointCategory
from app.core.common.dtos.app_endpoint_dtos import AppEndpointCtx, AppEndpointRecord, AppEndpointReq
from app.core.common.return_codes import CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.app_endpoint_dao import AppEndpointDao
from app.core.dao.impl.mongo.docs import MongoDocument
from app.core.dao.impl.mongo.unit_of_work import (
    MongoDeleteReq,
    MongoFindReq,
    MongoWriteReq,
    is_duplicate_key,
    mongo_unit_of_work,
)

log = logging.getLogger(__name__)
COLL = "app_endpoints"
LOCATIONS = "datasets_location"
CREDENTIALS_PATTERN = re.compile(r"[A-Za-z0-9_.\-]{1,100}")
NAME_MAX = 100


def _to_record(doc: MongoDocument) -> AppEndpointRecord:
    created, updated = doc["created_at"], doc["updated_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return AppEndpointRecord(
        id=doc["id"],
        name=doc["name"],
        category=doc["category"],
        from_dataset_location_id=doc.get("from_dataset_location_id"),
        from_env_var_name=doc.get("from_env_var_name"),
        to_dataset_location_id=doc.get("to_dataset_location_id"),
        to_env_var_name=doc.get("to_env_var_name"),
        credentials_ref=doc.get("credentials_ref"),
        description=doc.get("description"),
        enabled=bool(doc.get("enabled", True)),
        created_at=created,
        updated_at=updated,
    )


@dataclass
class XorSide:
    location_id: str | None
    env_var: str | None


def _xor_ok(side: XorSide) -> bool:
    return (side.location_id is None) != (side.env_var is None)



def _has_invalid_field(req: AppEndpointReq) -> bool:
    if req.name is not None and (
        not isinstance(req.name, str) or not req.name.strip() or len(req.name.strip()) > NAME_MAX
    ):
        return True
    if req.category is not None and req.category not in AppEndpointCategory.values():
        return True
    if req.from_env_var_name is not None and (
        not isinstance(req.from_env_var_name, str) or not req.from_env_var_name.strip()
    ):
        return True
    if req.to_env_var_name is not None and (
        not isinstance(req.to_env_var_name, str) or not req.to_env_var_name.strip()
    ):
        return True
    if req.from_dataset_location_id is not None and req.from_env_var_name is not None:
        return True
    if req.to_dataset_location_id is not None and req.to_env_var_name is not None:
        return True
    if req.credentials_ref is not None and (
        not isinstance(req.credentials_ref, str) or CREDENTIALS_PATTERN.fullmatch(req.credentials_ref) is None
    ):
        return True
    return False


@dataclass
class MergeSideReq:
    location_id: str | None
    env_var: str | None
    set_location: str | None
    set_env: str | None


def _merge_side(req: MergeSideReq) -> XorSide:
    out_loc, out_env = req.location_id, req.env_var
    if req.set_location is not None:
        out_loc, out_env = req.set_location, None
    if req.set_env is not None:
        out_loc, out_env = None, req.set_env.strip() if isinstance(req.set_env, str) else req.set_env
    return XorSide(location_id=out_loc, env_var=out_env)



class MongoAppEndpointDao(AppEndpointDao):
    def create(self, ctx: AppEndpointCtx) -> int:
        req = ctx.req
        if not (req.name and req.category) or _has_invalid_field(req):
            return INVALID_INPUT
        from_loc = req.from_dataset_location_id
        from_env = req.from_env_var_name.strip() if req.from_env_var_name else None
        to_loc = req.to_dataset_location_id
        to_env = req.to_env_var_name.strip() if req.to_env_var_name else None
        if not _xor_ok(XorSide(from_loc, from_env)) or not _xor_ok(XorSide(to_loc, to_env)):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                for loc_id in (from_loc, to_loc):
                    if loc_id is not None and uow.find_one(MongoFindReq(collection=LOCATIONS, query={"id": loc_id})) is None:
                        return NOT_FOUND
                if uow.find_one(MongoFindReq(collection=COLL, query={"name": req.name.strip()})) is not None:
                    return CONFLICT
                now = datetime.now(timezone.utc)
                doc = {
                    "id": str(uuid4()),
                    "name": req.name.strip(),
                    "category": req.category,
                    "from_dataset_location_id": from_loc,
                    "from_env_var_name": from_env,
                    "to_dataset_location_id": to_loc,
                    "to_env_var_name": to_env,
                    "credentials_ref": req.credentials_ref,
                    "description": req.description,
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
            log.exception("mongo app_endpoints create failed")
            return FAILURE

    def get(self, ctx: AppEndpointCtx) -> int:
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
            log.exception("mongo app_endpoints get failed")
            return FAILURE

    def list(self, ctx: AppEndpointCtx) -> int:
        req = ctx.req
        query: dict = {}
        if req.category is not None:
            query["category"] = req.category
        if req.enabled is not None:
            query["enabled"] = req.enabled
        if req.name is not None:
            query["name"] = req.name
        try:
            with mongo_unit_of_work(ctx) as uow:
                docs = uow.find(MongoFindReq(collection=COLL, query=query))
            docs.sort(key=lambda d: (d.get("category") or "", d.get("name") or "", d.get("id") or ""))
            ctx.resp.records = [_to_record(MongoDocument(d)) for d in docs]
            return SUCCESS
        except Exception:
            log.exception("mongo app_endpoints list failed")
            return FAILURE

    def update(self, ctx: AppEndpointCtx) -> int:
        req = ctx.req
        if not req.id or _has_invalid_field(req):
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": req.id}))
                if doc is None:
                    return NOT_FOUND
                name = req.name.strip() if req.name is not None else doc["name"]
                category = req.category if req.category is not None else doc["category"]
                from_side = _merge_side(MergeSideReq(doc.get("from_dataset_location_id"), doc.get("from_env_var_name"), req.from_dataset_location_id, req.from_env_var_name))
                to_side = _merge_side(MergeSideReq(doc.get("to_dataset_location_id"), doc.get("to_env_var_name"), req.to_dataset_location_id, req.to_env_var_name))
                from_loc, from_env = from_side.location_id, from_side.env_var
                to_loc, to_env = to_side.location_id, to_side.env_var
                if not _xor_ok(XorSide(from_loc, from_env)) or not _xor_ok(XorSide(to_loc, to_env)):
                    return INVALID_INPUT
                for loc_id in (from_loc, to_loc):
                    if loc_id is not None and uow.find_one(MongoFindReq(collection=LOCATIONS, query={"id": loc_id})) is None:
                        return NOT_FOUND
                if req.name is not None and name != doc["name"]:
                    if uow.find_one(MongoFindReq(collection=COLL, query={"name": name})) is not None:
                        return CONFLICT
                doc["name"] = name
                doc["category"] = category
                doc["from_dataset_location_id"] = from_loc
                doc["from_env_var_name"] = from_env
                doc["to_dataset_location_id"] = to_loc
                doc["to_env_var_name"] = to_env
                if req.credentials_ref is not None:
                    doc["credentials_ref"] = req.credentials_ref
                if req.description is not None:
                    doc["description"] = req.description
                if req.enabled is not None:
                    doc["enabled"] = req.enabled
                doc["updated_at"] = datetime.now(timezone.utc)
                uow.replace(MongoWriteReq(collection=COLL, doc=MongoDocument(doc)))
                ctx.resp.records = [_to_record(MongoDocument(doc))]
            return SUCCESS
        except Exception as exc:
            if is_duplicate_key(exc):
                return CONFLICT
            log.exception("mongo app_endpoints update failed")
            return FAILURE

    def delete(self, ctx: AppEndpointCtx) -> int:
        if not ctx.req.id:
            return INVALID_INPUT
        try:
            with mongo_unit_of_work(ctx) as uow:
                doc = uow.find_one(MongoFindReq(collection=COLL, query={"id": ctx.req.id}))
                if doc is None:
                    return NOT_FOUND
                ctx.resp.records = [_to_record(MongoDocument(doc))]
                uow.delete(MongoDeleteReq(collection=COLL, query={"id": ctx.req.id}))
            return SUCCESS
        except Exception:
            log.exception("mongo app_endpoints delete failed")
            return FAILURE
